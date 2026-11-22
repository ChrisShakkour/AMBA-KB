# Interface protection: parity, poison and RAS

> Mechanisms that detect corrupted bits on the wires (**parity check signals**) and mark corrupted data so it isn't silently used (**poison**, **DataCheck**). Together these support RAS (Reliability, Availability, Serviceability) and functional safety.

## In plain words

In safety-critical or server chips a single bit can flip, from radiation or a marginal timing path. Two complementary ideas handle this:

- **Parity on the interface**: for every group of up to 8 wires, add one extra wire so the number of 1s is always odd. If a bit flips, the receiver notices the count is even. This protects the *short wires between two components*. Inside components you use your own ECC (APB-E §5.1; AHB-C §12.1).
- **Poison**: if a memory controller finds an *uncorrectable* error in data, it doesn't crash the system immediately. It sends the data along with a **poison** flag, and the error is only raised if somebody actually *consumes* the data (G-CHI §10; AXI-L §A16.1).

## Parity check signals

The same scheme is used across APB5, AHB5, AXI5, AXI5-Stream, CHI, CXS and LPI (APB-E ch. 5; AHB-C ch. 12; AXI-L §A16.2; AXIS-B ch. 5; CXS-D §3.2; LPI-D §2.2):

- Property **`Check_Type`** = `False` (no check signals) or **`Odd_Parity_Byte_All`**. CXS calls it `CXSCHECKTYPE = Odd_Byte_Parity`. AXI5 and CHI also have **`Odd_Parity_Byte_Data`**, which protects only the data (AXI: signals whose names end in DATA; CHI: the DAT `DataCheck` field) (AXI-L Table A16.3; CHI-H §B16.1.7).
- **Odd parity**: the signal bits plus the check bit always contain an odd number of 1s.
- Each check bit covers **at most 8 bits**, which "assumes … a maximum of three logic levels" for generating it.
- **Critical single-bit controls** (VALID, READY, PSEL, PENABLE…) get one check bit that is simply the **inverted** signal.
- A wide check signal covers bytes: bit [n] covers payload [8n+7:8n].
- Check signals must be correct every cycle that their **Check Enable** term is true (for example `PWDATACHK` when PSEL & PWRITE).
- Parity covers **all bits of the payload**, even unused byte lanes.
- Missing covered signals are treated as LOW. If none are present, the check signal is omitted.

Example names: `PADDRCHK`, `PCTRLCHK`, `PWDATACHK`, `HTRANSCHK`, `HCTRLCHK1/2`, `HWDATACHK`, `AWADDRCHK`, `WDATACHK`, `TDATACHK`, `CXSDATACHK`, `QREQCHK`, `PSTATECHK`. In CHI: `*FLITCHK` (one bit per flit byte) plus inverted checks on `*FLITV`, `*LCRDV`, `*LINKACTIVEREQ/ACK` and `SACTIVE` (G-CHI §16, CHI-D additions).

**What to do on a detected error is not specified**: terminate or propagate the transfer, correct or propagate the parity, update memory or not, raise an interrupt (APB-E §5.4; AHB-C §12.4; AXI-L §A16.2.2). "The transaction response is independent of parity error detection" (AHB-C §12.4).

## Poison, DataCheck and data errors

| Mechanism | Granularity | Where | Meaning |
|---|---|---|---|
| **Poison** | 1 bit per **64 bits** of data | CHI DAT flit (G-CHI §10). AXI5 `xPOISON` (AXI-L §A16.1) | This data is known corrupt. Defer the error until it is consumed |
| **DataCheck** | 1 bit per **byte**, odd parity | CHI DAT flit (CHI-B onward) | Detects corruption of the data field in flight. Replaced by interface parity if that is implemented (CHI-D) |
| **RespErr / DERR / NDERR** | Per message | CHI | Data error (data unusable) or non-data error (the transaction failed) |
| **TraceTag** | 1 bit per flit | CHI (CHI-B) | Not an error mechanism: marks flits for debug tracing (G-CHI §10) |

"Corrupted data is considered consumed" when it is used in a computation, or when it is passed to a component that does not support poison (which must then raise an exception) (G-CHI §10).

### What the full specs add

**CHI error types (CHI-H §B9.1)**
- **DERR**: the right location was accessed but the data is bad (ECC or parity). Home must keep propagating the request to the Subordinate.
- **NDERR**: anything else, such as a non-existent address, a write to read-only space, or an unsupported transaction. Home may or may not forward the request, but must pass the NDERR back.
- Every transaction must still **complete in a protocol-compliant way**, with the correct number of data beats (the values need not be valid).
- Mixing rules: never OK with EXOK, never EXOK with NDERR, and NDERR on either none or all data beats of a message.
- A requester that receives NDERR on an allocating read must not allocate or change state. A snoopee that answers with NDERR must invalidate its copy and must not forward data.
- An interconnect that detects an error must not use DMT or DCT, because requests and snoops have no way to carry an error forward.
- A DERR on a **clean** line is recommended to be dropped. A DERR on a **dirty** line must be propagated.

**CHI Poison and DataCheck (CHI-H §B9.2)**
- Poison: 1 bit per 64 data bits. Poisoned data must not be *used*, but may be stored in caches and memory. Once set, poison travels with the data, and "over-poisoning" a larger chunk is allowed. **There is no poison on MTE tags.**
- DataCheck: 8 odd-parity bits per 64 data bits (one per byte).
- When the two sides support different features, the interconnect converts: Poison → DataCheck by corrupting all 8 check bits of the chunk, DataCheck error → Poison bit, or either → DERR. Poison is normally *deferred* by the receiver, whereas DERR usually is not.
- A sender that sets Poison or a bad DataCheck need not also set DERR.

**AXI5 poison (AXI-L §A16.1)**: `WPOISON`/`RPOISON`, 1 bit per 64 bits, **independent of the response**. An error response without poison, and poison with an OKAY response, are both legal.

**Software vs hardware errors (CHI-H §B9.4)**: mismatched memory attributes are a *software* error. The system must not deadlock, and damage must stay inside that 4 KB region. Any other protocol violation is a *hardware* error, and recovery is not guaranteed.

## Where the sources agree

- Every AMBA 5 spec uses **the same odd byte-parity scheme** with the same rules: each parity bit covers no more than 8 payload bits ("This limitation assumes that there is a maximum of three logic levels available in the timing allowance": APB-E ch. 5; AXIS-B §5.3), and a critical control signal gets a single parity bit that "is the inversion of the original critical control signal" (APB-E ch. 5; AHB-C ch. 12). The text is almost identical between APB-E ch. 5 and AHB-C ch. 12.
- Parity is meant as the inter-component part of **end-to-end** protection. Inside components you need your own EDC/ECC (APB-E §5.1; AHB-C §12.1).
- Error-handling **policy is the system's job**, not the protocol's.

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| How CHI protects data | CHI-B: `DataCheck` (byte parity on the data field) | CHI-D: optional **interface parity** on whole flits (`*FLITCHK`), which "if implemented, replaces DAT.DataCheck" (G-CHI §16) | *Editor's note (not from the sources):* Arm moved CHI to the same full-interface parity as the other AMBA 5 protocols. DataCheck remains for systems without it |
| Parity on APB `PSLVERR` | APB-E Table B-2: `PSLVERRCHK` is **optional-conditional (OC)** | Most other APB5 check signals are **conditional (C)**, required when Check_Type is set | PSLVERR itself is optional on APB, so its check signal is optional too |
| Can one check bit cover more than 8 bits? | APB-E §5, AHB-C §12 and CHI-H §B9.3.1: no more than 8 bits per group (a 3-logic-level timing budget) | AXI-L Table A16.3: "generally covers up to 8 bits. However, a parity bit can cover more than 8 bits if the configuration requires it" | AXI5 has many narrow optional fields that don't pack into bytes. AXI-L relaxed the rule rather than add more check wires. Check the exact grouping in AXI-L §A16.2.3 |
| Which parity options exist | APB-E, AHB-C: `Check_Type` = Odd_Parity_Byte_All or False | AXI-L, CHI-H: also **Odd_Parity_Byte_Data** (data only) | *Editor's note (not from the sources):* Data-only protection lets AXI/CHI keep the old "DataCheck-only" behaviour as a named option |
| AHB strobe parity width | AHB-C Table 12-1: `HWSTRBCHK` = ceil(DATA_WIDTH/**64**) bits | APB-E: `PSTRBCHK` = **1** bit | Both follow the rule that each parity bit covers no more than 8 payload bits. HWSTRB has DATA_WIDTH/8 bits, hence /64. PSTRB is at most 4 bits |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Generate check bits **directly from flops** feeding the outputs. Don't let synthesis put logic between the flop and the pin after the parity is computed, or you lose the protection.
- For the inverted-control style: `PSELxCHK = ~PSELx`, `HREADYCHK = ~HREADY`.
- If a peripheral can't use poison, it must treat poisoned data as an error when it consumes it. Do not drop the poison bit quietly.

## Related articles

- [Responses and errors](responses-and-errors.md)
- [Interface properties and user signals](interface-properties-and-user-signals.md)
- [Low power and wake-up](low-power-and-wakeup.md) (parity on Q/P-Channel)
- [CHI architecture](chi-architecture.md)

## Sources

APB-E, AHB-C, AXI-L (read in full), AXIS-B, CHI-H (read in full), CXS-D, LPI-D, G-CHI. See [Source key](sources.md).
