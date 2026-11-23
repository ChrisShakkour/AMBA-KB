# Handshakes and flow control

> How the two sides of a link agree that "this piece of data was passed now". AMBA uses three basic styles: **wait-state** signals (APB, AHB, GFB), **VALID/READY** handshakes (AXI, AXI-Stream, ATB) and **credits** (CHI, CXS, CHI C2C, AXI5 credited transport).

## In plain words

Flow control answers the question "can I send this now?".
- **Wait-state style:** the answering side says "not yet" by holding a ready signal LOW. The asking side simply keeps everything stable until it goes HIGH.
- **VALID/READY:** the sender raises **VALID** ("I have something"), the receiver raises **READY** ("I can take it"). The item moves on the clock edge where **both are HIGH**.
- **Credits:** the receiver gives the sender a *token* for each free buffer slot. The sender may send one item per token and never has to wait for a READY answer in the same cycle. This works well for long wires and high clock speeds.

## 1. Wait-state style

| Protocol | Signal | Rule |
|---|---|---|
| APB3+ | `PREADY` (Completer) | Sampled only in the ACCESS phase (`PSEL`&`PENABLE`). While LOW, PADDR, PWRITE, PSEL, PENABLE, PWDATA, PSTRB, PPROT, PAUSER and PWUSER must stay stable. "PREADY can take any value when PENABLE is LOW", so a fixed two-cycle peripheral can tie it HIGH (APB-E §3.1.2) |
| APB2 | *(none)* | Every transfer is exactly 2 cycles, with no wait states (AMBA2 ch. 5) |
| AHB | `HREADYOUT` (each Subordinate) → `HREADY` (combined) | LOW extends the **data phase**. The address phase cannot be extended by the Subordinate, but it is stretched as a side-effect, because the next address waits (AHB-C §1.3, §3.1) |
| GFB | `FREADY` | HIGH means a command is accepted / complete. A Subordinate can hold it LOW for initialisation, long erases or "housekeeping" (GFB-Ab §3.3) |

## 2. VALID/READY handshake (AXI family)

The rules below are quoted from AXI-L §A2.3 and repeated almost word for word in AXIS-B §2.2 and ATB-C §3:

1. A transmitter **must not wait for READY before asserting VALID**. Breaking this rule is the classic AXI deadlock.
2. Once VALID is HIGH it **stays HIGH, with the information stable, until the handshake**.
3. A receiver **may** wait for VALID before raising READY.
4. A receiver may raise READY early, and may drop it again before VALID arrives.
5. VALID must be LOW during reset. The earliest it may rise is the first rising edge after `ARESETn` goes HIGH (AXI-L §A2.1.2).

**Dependencies between AXI channels** (AXI-L §A2.3.2):
- **Write:** the Subordinate must wait for AW handshake *and* the W beat with WLAST before asserting BVALID. AWREADY and WREADY may depend on either valid.
- **Read:** RVALID only after the AR handshake.
- **Atomics** add "The Manager must not wait for the Subordinate to assert RVALID before asserting WVALID" (AXI-L §A6.4.9).

**Default READY value**: either is allowed. HIGH is recommended for request channels to cut latency, but then the Subordinate must be able to take any request (AXI-L §A2.3).

**AXI-Stream extras**: `TREADY` may be omitted by a Receiver that can always accept (default HIGH). A Transmitter should still keep the TREADY input so it can flag back-pressure it cannot handle (AXIS-B §3.1).

**ATB extras**: if `ATREADY` is LOW while ATVALID is HIGH, data, ID and bytes must hold. A Receiver that cannot respond (for example powered down) must drive **ATREADY HIGH** so a replicator never blocks (ATB-C §3.2).

## 3. Credit-based flow control

| Protocol | Credit signals | Key rules |
|---|---|---|
| CHI (link layer) | `*LCRDV` from Receiver, `*FLITV` from Transmitter, `*FLITPEND` as an early hint | One flit consumes one L-Credit. A Receiver gives **1 to 15** credits per channel, must be able to accept every flit it has credited, and a credit cannot be used in the cycle it arrives (CHI-H §B14.2) |
| CHI Resource Planes (Issue H) | `REQFLITRP`/`SNPFLITRP`, one `*LCRDV` bit per plane, optional `*LCRDSHV` + `*SHAREDCRD` | Up to **8 planes** on REQ and SNP (`Num_RP_REQ`, `Num_RP_SNP`), with 1–15 dedicated credits per plane and up to 15 shared credits. Use a dedicated credit before a shared one. Planes must never block each other, and both ends must declare the same plane count (CHI-H §B14.2.1.2, §B16.1.34–37) |
| CHI (protocol layer) | `RetryAck` + `PCrdGrant` with `PCrdType` | A request first goes out with `AllowRetry=1`. If the Completer has no resource it sends RetryAck with a credit type (one of 16), later grants that type, and the Requester resends with `AllowRetry=0`, or returns the unused credit with **PCrdReturn**. Only REQ can be retried (G-CHI §4; CHI-H §B2.10). Since Issue H, Retry is optional: `Retry_Support` = True / RP0_Only / False (CHI-H §B16.1.38) |
| AXI5 credited transport | `xCRDT`, `xCRDTSH`, `xPENDING`, `xRP`, `xSHAREDCRD` | Selected with `AXI_Transport = Credited`. Credits are given per **Resource Plane** (1–8 RPs on AW/W and AR), with **1–15** credits per RP plus up to 15 shared. No combinatorial paths between credit and other signals (AXI-L §A2.4) |
| CXS | `CXSCRDGNT`, optional `CXSCRDRTN` | One credit per flit. Maximum given by `CXS_MAX_CREDIT` (**1–63** in Issue D). A non-configurable Transmitter must track 15 (CXS-D §2.1.2) |
| CHI C2C | Message credits per message class (REQ, RSP, DAT, SNP, MISC) | Separate credits per class, granted in the container header or a MiscU.CrdtGrant message. Uncredited MISC (MiscU) messages need no credit. A WritePush message (request + data) needs one REQ *and* one DAT credit (C2C-B §B8.2) |

**How many credits?** "The number of credits that are required to keep the interface flowing at full bandwidth depends on the credit latency … If the number of credits the Receiver can issue is greater than or equal to the credit latency, then the interface can sustain one flit per cycle" (CXS-D §2.1.2). CXS-D §6.1 lists what goes into that round trip: wire delay each way plus each side's internal delay (`CXS_MAX_CREDIT_LATENCY`). CXS-D §5.5 notes that the physical distance between Transmitter and Receiver sets how many flip-flop stages the signals need. *Editor's note (not from the sources): the specs do not say why credits were chosen over VALID/READY. Note that AXI also allows register stages on VALID/READY paths (AXI-L §A2.5).*

**Resource planes** (AXI5 credited, CHI, C2C) are independent credit pools on one channel, so traffic on one plane cannot block another. This is used to avoid deadlock and for QoS (AXI-L §A2.4.2).

**Channel dependencies in CHI** (CHI-H §B13.4.1) are what keep the whole system deadlock-free:
- A Request Node must make progress on inbound **RSP and DAT without depending on any other channel**. In practice, it must be able to take every Comp/CompData without first sending a CompAck.
- It must make progress on inbound **SNP** without needing outbound REQ (it may wait for outbound RSP/DAT).
- A Subordinate must always sink inbound DAT. Whether inbound REQ may wait for outbound DAT depends on `Retry_Support`. With True, REQ must not depend on outbound DAT. With RP0_Only, that applies only to plane 0. With False, the dependency is permitted.

## Where the sources agree

- All handshake protocols forbid the sender from **withdrawing** an offer: VALID, once asserted, stays until accepted (AXI-L §A2.3; AXIS-B §2.2; ATB-C §3.2). APB and AHB express the same idea as "signals must remain stable while PREADY/HREADY is LOW" (APB-E §3.1.2; AHB-C §3.1).
- All credited links start from reset with **all credits held by the receiver** (CHI-H §B14.1.3; AXI-L §A2.4.1; CXS-D §2.1.1).
- AXI5 credited transport and CHI Issue H use the same Resource Plane design: up to 8 planes, 15 dedicated credits per plane plus up to 15 shared, and a "shared credit used" flag on each transfer (AXI-L §A2.4; CHI-H §B14.2.1.2).
- Using a credit in the same cycle it is granted is not allowed anywhere (CHI-H §B14.2; AXI-L §A2.4.1; CXS-D §2.1.2).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Maximum credits | CHI-H §B14.2 and AXI-L §A2.4.1: max **15** per channel / resource plane | CXS-D §2.2: `CXS_MAX_CREDIT` 1–**63**. CXS-B Table 2-2: **1–15** | A version change: CXS-D Table A1-3 lists "Increased range of CXS_MAX_CREDIT to 1-63" as an **Issue C** change. No reason is given. *Editor's note (not from the sources): more credits allow full bandwidth over longer credit loops, which follows from CXS-D §2.1.2* |
| Returning credits before sleep | CHI-H §B14.5: every credit must be **explicitly returned** (LCrdReturn flits) before the link reaches STOP | AXI-L §A14.2: credits are **implicitly returned** in STOP. No explicit return is needed, and credits arriving in STOP are dropped | See [Low power](low-power-and-wakeup.md). CHI has link flits for credit return, AXI credited transport does not |
| Is protocol Retry always available? | G-CHI §4: RetryAck/PCrdGrant is *the* CHI request flow control | CHI-H §B16.1.38: Issue H allows `Retry_Support = False` or `RP0_Only`, relying on Resource Planes instead | Retry needs trackers to remember every retried request. Credit-only designs avoid that. Mixing a retrying Completer with a non-retrying Requester can deadlock (CHI-H Table B16.41) |
| Can READY "wait for VALID"? | AXI-L / AXIS-B: yes, allowed | ATB-C §3.2: a Receiver that **cannot respond** must hold ATREADY **HIGH** | Not a real conflict. ATB adds a special rule for absent or powered-down receivers so that replicators never deadlock |
| Is the address phase extendable (AHB)? | AHB-C §1.3: "A Subordinate cannot request that the address phase is extended" | AHB-C §3.1 (same spec): "Address … lasts for a single HCLK cycle **unless it is extended by the previous bus transfer**" | Both are true. A Subordinate cannot stall *its own* address phase, but a waited previous transfer delays when the next address is sampled |
| Is handshake "two-way" in ATB? | ATB-C §3.1 calls ATVALID/ATREADY a "two-way flow control" | — | Same concept as AXI, so no real disagreement. Noted because ATB predates AXI-Stream and uses its own wording |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Never write `assign valid = ready & have_data;` on an AXI-family interface: VALID would then depend on READY, which breaks rule 1.
- In a credited receiver, size the buffer for **every credit you will hand out**. Giving more credits than you have slots silently corrupts data.
- In AHB, register `HREADYOUT` but use `HREADY` (the combined signal) to decide when your address phase is sampled.

## Related articles

- [APB interface hub](interface-apb.md), [AHB interface hub](interface-ahb.md), [AXI interface hub](interface-axi.md)
- [Transfer phases and pipelining](transfer-phases-and-pipelining.md)
- [Low power and wake-up](low-power-and-wakeup.md) (FLITPEND, PENDING, link activation)
- [QoS and traffic modelling](qos-and-traffic-modelling.md) (resource planes, retry)
- [CHI architecture](chi-architecture.md)

## Sources

AMBA2, APB-E, AHB-C, AXI-L, AXIS-B, ATB-C, CHI-H, CXS-B, CXS-D, C2C-B, GFB-Ab, G-CHI. See [Source key](sources.md).
