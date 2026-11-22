# Exclusive access, locked transfers and atomics

> Three ways to perform a read-modify-write safely when several Managers share memory: **lock the bus** (old), **exclusive monitor** (load-linked/store-conditional) and **atomic transactions** (send the operation to the data).

## In plain words

Two CPUs both want to increment a shared counter. If both read 5, add 1 and write 6, one increment is lost. AMBA has offered three fixes:

1. **Locked transfers**: "nobody else may use the bus until I'm done." Simple, but it stalls everyone. Used, for example, by processors performing a `SWP` instruction (AXI-C §13.15.2).
2. **Exclusive access**: read the value while a *monitor* watches the address, then write back conditionally. If anyone else wrote in between, the write **fails** and software retries.
3. **Atomic transactions**: send "add 1 to address X" to the interconnect or memory, which performs the operation where the data lives. There are no retries, and the data is unavailable to others only for a very short time.

## 1. Locked transfers

| Protocol | Signal | Status |
|---|---|---|
| AMBA 2 AHB | `HLOCKx` (master→arbiter), `HMASTLOCK` (arbiter→slaves) | The arbiter keeps the bus granted. It recommends an IDLE after the locked sequence (AMBA2 §3.11.5) |
| AHB-Lite/AHB5 | `HMASTLOCK` (Manager output) | Still supported. All transfers in a locked sequence must go to the **same Subordinate address region** (new in Issue B). A multi-port Subordinate must implement it (AHB-C §3.3) |
| AXI3 | `AxLOCK[1:0]` = 0b10 | Supported. The interconnect must give the Manager exclusive access to the target region until an unlocked transaction completes (AXI-Hc §A7.3) |
| AXI4+ | — | **Removed.** An AXI3 locked access is converted to a normal access (AXI-Hc §A7.4.1) |

## 2. Exclusive access

The sequence is the same in AXI, AHB5 and CHI (AXI-L §A6.3; AHB-C §10.1; CHI-H ch. B6):
1. Exclusive **read** of the address. The monitor records (address, Manager/thread ID).
2. Compute the new value. Other non-exclusive transfers may happen in between.
3. Exclusive **write** to the same address with matching attributes.
4. The response says success (**EXOKAY** / `HEXOKAY`=1) or failure (**OKAY** / `HEXOKAY`=0). On failure memory is **not** updated, and software repeats from step 1.

| Detail | AXI (`AxLOCK`=1) | AHB5 (`HEXCL`, `HMASTER`, `HEXOKAY`) |
|---|---|---|
| Who identifies the thread | AXI ID (AWID must match ARID) | `HMASTER` (Manager bits + interconnect bits). Recommended widths: Manager as needed, interconnect port 4, Subordinate/monitor 8 |
| Size / alignment | Power of 2, 1–128 bytes, aligned to Size×Length, ≤16 beats | Single beat, SINGLE or INCR, no BUSY, aligned |
| Where the monitor is | In or in front of the Subordinate | Anywhere that sees all relevant accesses. Not required for every address |
| Unsupported location | Exclusive read gets OKAY (not EXOKAY). Exclusive **write updates the location** and returns OKAY | `HEXOKAY` low = fail |
| Outstanding exclusives | One monitored address per ID | One exclusive outstanding per `HMASTER` value |
| Extra restrictions (AXI5) | Domain must **not** be Shareable. Opcode ReadExclusive/WriteExclusive. AWTAGOP must not be Match | HPROT must let the monitor see the access (for example Non-cacheable if the monitor is behind a cache) |

Sources: AXI-L §A6.3.1–A6.3.4; AHB-C §10.2–10.4.

### Exclusives in CHI (CHI-H ch. B6)

CHI has two cases, depending on whether the address is snoopable:

| | Snoopable location | Non-snoopable location |
|---|---|---|
| Monitors | An **LP monitor** in each logical processor of the RN-F, plus a **PoC monitor** in the HN-F | One **System monitor**, at the PoS or at the endpoint |
| Exclusive load | ReadClean, ReadNotSharedDirty, ReadShared or ReadPreferUnique with `Excl=1` (or no transaction at all if the line is already cached) | ReadNoSnp(Excl) |
| Exclusive store | **CleanUnique(Excl)** or (preferred) **MakeReadUnique(Excl)**, issued only if the line is Shared. If it is Unique and the LP monitor is still set, the store just happens locally | WriteNoSnp(Excl) |
| Pass/fail signal | `RespErr` = **EXOK** (pass) or OK (fail). For MakeReadUnique(Excl) and ReadPreferUnique, the **returned cache state** decides: Shared = fail, Unique = check your own LP monitor | `RespErr` EXOK / OK |
| Restrictions | The PoC monitor must track **every** exclusive-capable LP at once, so there is no livelock | Aligned, 1–64 bytes. Only **one** exclusive outstanding per LP. A mismatched Addr, MemAttr, SnpAttr, Size or LPID may cause a failure |

More CHI rules:
- A passing exclusive read must not use separate Comp and data, DMT or DCT, so that the response carries the pass/fail result (CHI-H §B6.3.1).
- A Home may replace the PoC monitor with a **precise snoop filter** or with snooping (for example SnpQuery) (CHI-H §B6.2.3).
- The system **must** have starvation prevention for exclusives. Arm recommends that exclusives in one PAS cannot slow down another PAS (CHI-H §B6.3.2).
- If the Subordinate does not support exclusives (it fails the ReadNoSnp(Excl)), a following WriteNoSnp(Excl) **does update** the location (CHI-H §B6.3.4), the same rule as AXI.

## 3. Atomic transactions (AXI5, CHI-B+)

Four kinds (AXI-L §A6.4.1):

| Kind | Sends | Returns | Data size |
|---|---|---|---|
| AtomicStore | operand | response only | 1, 2, 4, 8 B |
| AtomicLoad | operand | original value | 1, 2, 4, 8 B |
| AtomicSwap | new value | original value | 1, 2, 4, 8 B |
| AtomicCompare | compare + swap values | original value | 2–32 B out, half that back |

Operations for Store/Load: **ADD, CLR, EOR, SET, SMAX, SMIN, UMAX, UMIN**, selected by `AWATOP[2:0]`. `AWATOP[3]` sets the endianness for arithmetic (AXI-L §A6.4.2, §A6.4.6).

Key rules (AXI-L §A6.4):
- An Atomic transaction uses the AW, W **and** R channels (except AtomicStore), with one ID that must be **unique in flight** on both read and write channels.
- The B response comes only after the result is observable. Read data may arrive before or after the write data is accepted.
- There is no "overflow" error. To learn whether a CompareAndSwap succeeded, compare the returned old value yourself.
- A component that claims support must support **all** operations, sizes and endiannesses. `BROADCASTATOMIC`=0 stops a Manager issuing atomics into systems that can't handle them.
- In CHI, the HN or SN that executes atomics needs an ALU. Support has been optional since CHI-B (G-CHI §9).

### Extra rules in CHI (CHI-H §B4.2.5, §B5.4, §B16.3)
- The returned "original value" **must not be cached** by the requester, and every peer copy of the line ends up Invalid.
- Atomics never use **DMT or DWT**, and Home never uses a **forwarding snoop** for them.
- If the requester has the line cached, it can do the operation locally (Unique), get ownership first, or invalidate its copy and send the Atomic. If it cannot be sure its copy is Invalid, it must set **SnoopMe=1** so Home snoops it too.
- An `Endian` field in the request gives the byte order for arithmetic (the AXI equivalent is `AWATOP[3]`).
- One `RespErr` covers both directions, so an error cannot say whether the write data or the read data was bad. An Atomic that cannot be performed gets **NDERR**, and the full message structure must still complete (CHI-H §B9.1.4.4).
- Interconnect support is optional, but if Atomics are supported for one snoopable address they must be supported for the **whole snoopable range**. Atomics to Device memory must go to the endpoint (CHI-H §B16.3.2).

### Extra rules in AXI5 (AXI-L §A6.4)
- AWATOP sub-encodings are the same eight operations as CHI's sub-opcodes, so a bridge maps them one to one.
- Atomics are allowed with MTE only as **Match** (a tag check), not as a tag update (AXI-L §A12.2.8).

## Single-copy and multi-copy atomicity

- **Single-copy atomicity size**: the minimum chunk that is always updated as a whole. No observer may see half of it updated. It is never larger than the start-address alignment, and byte strobes don't change it (AXI-L §A6.1; AHB-C §9.1).
- **Multi-copy atomicity**: all observers see writes to a location in the same order, and a write visible to one is visible to all (AXI-L §A6.2; AHB-C §9.2).

## Where the sources agree

- The exclusive sequence and its success/fail semantics are the same in AXI and AHB5. Both allow an exclusive read with no matching write, and both make an exclusive write without a prior read **fail** (AXI-L §A6.3.2; AHB-C §10.4).
- A Subordinate may report success **without monitoring** if only one Manager can ever reach the location (AHB-C §10.3.1). In AXI, an unsupported location returns OKAY on reads, and Arm recommends the Manager not attempt the write (AXI-L §A6.3.2).
- Atomics reduce the time that data is unavailable compared with exclusives (AXI-L §A6.4; G-CHI §9).
- **Why exclusives instead of locks**: the exclusive mechanism "can provide semaphore-type operations without requiring the bus to remain dedicated to a particular manager during the operation. This means that the bus access latency and the maximum achievable bandwidth are not affected" (G-AXI §6). The same guide says locked transactions "should only be used for legacy devices" (G-AXI §6).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Locked transfers | AHB-C (2021): `HMASTLOCK` still defined | AXI4+ (AXI-Hc §A7.3): locked transactions **removed** | AXI-Hc §A7.3 states the reasons: "the majority of components do not require locked transactions", and locking has "a significant effect on the complexity of the interconnect" and "the ability to make QoS guarantees". AHB-C keeps HMASTLOCK and gives no reason for keeping it |
| Exclusive write to a location without a monitor | AXI-L §A6.3.4 and CHI-H §B6.3.4 (Non-snoopable): the Subordinate responds OKAY **and the location is updated** | AHB-C §10.3.1: `HEXOKAY` deasserted = "failed". It does not say the location is updated. CHI-H §B6.3.1 (general case): "IMPLEMENTATION DEFINED whether … updates the location" | An important difference for bridges. An AXI→AHB bridge cannot assume AHB writes through an unmonitored exclusive (or vice versa). Inside CHI, the general rule is loose and the Non-snoopable rule is precise. Arm recommends never issuing an exclusive store to such a location |
| Required system property | AXI-L §A6.2: `Multi_Copy_Atomicity` **must be True** for Issue G and later. CHI-H §B2.7.1: required of every CHI component | AHB-C §9.2: an optional property, default False | *Editor's note (not from the sources):* AXI and CHI aligned with the Armv8 memory model, which requires it. AHB5 still serves simpler systems |
| How a CHI exclusive store reports failure | CleanUnique(Excl): `RespErr` OK = fail, EXOK = pass | MakeReadUnique(Excl): EXOK is **not permitted**. A Shared state in the response = fail (CHI-H §B6.3.1.1) | MakeReadUnique (CHI-E) can return data when the line was lost, so it uses the cache state rather than RespErr. RTL must check *both* mechanisms |
| Exclusives in Shareable memory | AXI-Hc ch. D9 (ACE): Inner/Outer Shareable exclusives use ReadClean/ReadShared and CleanUnique with ARLOCK, plus a Manager monitor and a PoS monitor | AXI-Hc §A7.2.4 (for plain AXI) and AXI-L §A6.3.3: an AXI exclusive's domain must be Non-shareable or System | Plain AXI never had Shareable exclusives: they existed only through ACE. Since Issue J removed ACE (AXI-L §B4.1), coherent exclusives are done with CHI (CHI-H ch. B6) |
| Who first had atomics | G-CHI §9: "In AXI3 and 4 and CHI-A, a requester fetches the data, performs the operation, and then writes back" | AXI-Hc §E1.1 / AXI-L §A6.4: AXI5 has atomic transactions | Both are true. Atomics arrived with AXI5/ACE5 and CHI-B (2017). Earlier versions used exclusives |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Exclusive monitor: store (ID, address, size) on an exclusive read. Clear the entry on any write by *another* Manager to an overlapping address. On an exclusive write, check for a match → EXOKAY and write, otherwise OKAY and **don't write**.
- If your AXI Subordinate has no monitor, set `Exclusive_Accesses=False`. Then exclusives "continually fail, but the interface will not deadlock" (AXI-L Table A6.4).
- In a CHI RN-F, do not let an Exclusive Store transaction be outstanding at the same time as another transaction that registers an exclusive sequence (any exclusive load or store). Wait for its messages to finish or for a RetryAck (CHI-H §B6.3.3.3).
- If the LP monitor was already reset, fail the store-exclusive locally and do **not** send CleanUnique(Excl). That avoids pointlessly invalidating other copies (CHI-H §B6.3.3.3).

## Related articles

- [Responses and errors](responses-and-errors.md) (EXOKAY, HEXOKAY)
- [Transaction IDs and ordering](transaction-ids-and-ordering.md)
- [Cache coherency fundamentals](cache-coherency-fundamentals.md)
- [CHI architecture](chi-architecture.md)

## Sources

AMBA2, AHB-C, AXI-Hc, AXI-L (read in full), CHI-H (read in full), G-CHI, G-AXI. See [Source key](sources.md).
