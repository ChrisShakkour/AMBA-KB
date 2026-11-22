# Transaction IDs, outstanding transactions and ordering

> Rules for *which transactions must stay in order* and which may overtake each other, and how IDs let a protocol have many transactions in flight at once.

## In plain words

When you post several letters, you often don't care which arrives first, except when one says "ignore my previous letter". Ordering rules say which "letters" a protocol keeps in sequence.
- **APB and AHB**: one thing at a time, so order is automatic.
- **AXI**: each request carries an **ID**. Requests with the **same ID** stay in order. Requests with **different IDs** may complete in any order. The ID works like a set of independent queues.
- **CHI**: ordering is requested per transaction with an **Order** field, and is enforced by the Home Node, the *Point of Serialisation*.
- **Streams (ATB, AXI-Stream)**: the stream itself is the order. Bytes are never reordered.

## AXI: the ID-based model

### What is guaranteed (AXI-L §A5.3)
- Requests on the same channel with the **same ID and destination** stay in order, and responses with the same ID return **in request order**.
- No guarantees between different Managers, between **reads and writes**, between different IDs, between different Peripheral regions, or between different Memory locations.
- If you need order where none is guaranteed: **wait for the response** before issuing the next request.

### Memory location vs Peripheral region (AXI-L §A5.3.1)
- *Memory location*: a read returns the last value written, there are no side effects, and ordering is guaranteed per location.
- *Peripheral region*: reads and writes can have side effects, and ordering is guaranteed per region. The region size is implementation-defined but must fit inside one Subordinate.

### Device vs Normal ordering
- Device (`AxCACHE[1]=0`) reads or writes with the same ID to the same Peripheral region **arrive in order** (AXI-L §A5.3.4).
- Writes with the same ID, same cacheability and same location are **observed in order**.
- Device vs Normal Non-cacheable with the same ID: ordered only if `Device_Normal_Independence = False` (AXI-L §A5.3.8).
- **Ordered Write Observation** (optional property): writes from one Manager with one ID are observed in issue order *regardless of address*. This is helpful for producer→consumer flag writes (AXI-L §A5.3.9).

### Completion and early responses
- *Write completion* = the B handshake (with BCOMP if present). *Read completion* = the last R beat with RLAST (AXI-L §A5.3.3).
- A **Bufferable** write may get an **early response** from an intermediate buffer. The buffer then owns ordering for that address until its downstream response comes back (AXI-L §A5.3.7).
- Trick: issue Device Bufferable writes, then one Device **Non**-bufferable write with the same ID to the same Subordinate. Its response proves that all the earlier writes have arrived (AXI-L §A4.3.5).

### IDs through an interconnect
- The interconnect **appends** Manager-port bits to AWID/ARID and removes them from BID/RID (AXI-L §A5.4).
- It must keep same-ID responses in order **even if they go to different Subordinates** (AXI-L §A5.5–A5.6).
- **Unique ID indicator** (`AxIDUNQ`, `xIDUNQ`): marks an ID as not shared by any other in-flight transaction, so downstream logic can skip ordering tracking (AXI-L §A5.2).

### AXI5 ID constraints you must not miss (AXI-L Appendix B3)
- **Unique in flight** is *required* for: Atomics, Prefetch, WriteZero, WriteDeferrable, InvalidateHint, chunked reads, MTE tag transactions, UnstashTranslation and ACT (compression) transactions.
- **Must not share an ID** while outstanding: DVM Complete vs other reads, StashOnce vs non-StashOnce writes, translated vs untranslated transactions, StashTranslation vs others.
- **Must use the same ID**: requests that need ordering, and the two halves of an exclusive pair.

### Interleaving
- **Read data** with different IDs may interleave beat by beat. `Read_Interleaving_Disabled` can switch this off (AXI-L §A5.6.1).
- **Read data chunking** (AXI5): a Subordinate may return 128-bit chunks of one transaction out of order (AXI-L §A5.6.2).
- **Write data** must be sent in request order (AXI-L §A5.5), except across different **Resource Planes** in credited transport.

## AHB and APB: implicit order

- AMBA2 §3.12.2: "The bus protocol only allows a single outstanding transaction per bus master." A master needing more must appear as several masters.
- AHB5 Device memory: "all read and write transfers from the same Manager to the same Subordinate must remain ordered" (AHB-C §3.9.4).

## CHI: requested order

- **Request Order**: same requester, same address. **Endpoint Order**: same requester, same Subordinate address range. **Ordered Write Observation (OWO)**: other agents observe a sequence of writes from one agent in issue order. **Request Accepted** (HN → SN only): the Subordinate acknowledges that it accepted a read (CHI-H §B2.7.5; G-CHI §4).
- `Order` encodings: 00 none, 01 Request Accepted, 10 Request Order (OWO when ExpCompAck=1), 11 Endpoint Order. It may be non-zero only for ReadNoSnp(Sep), ReadOnce*, WriteNoSnp*, WriteUnique*, the Zero writes and Atomics (CHI-H Table B2.9, §B2.7.5.1).
- A ReadNoSnp/ReadOnce* that needs ordering gets a **ReadReceipt**, after which the next ordered request may go. Writes use **DBIDResp** the same way. **DBIDRespOrd** (CHI-E) additionally promises that every *later* request to the same address, from anyone, is ordered behind this write (CHI-H §B4.5.4; G-CHI §4).
- A sequence that relies on `Order` must stay on **one REQ Resource Plane** (CHI-H §B2.7.5).
- **CompAck** from a fully coherent RN tells the Home Node that the RN has seen its completion, so snoops to the same line can be released in order. This is similar to RACK/WACK in ACE (G-CHI §4). An RN-F must send CompAck for all reads except ReadNoSnp and ReadOnce*, and must never send it for CMOs, StashOnce, Atomics or Evict (CHI-H §B2.7.3).
- **RespSepData vs DataSepResp**: when Comp and data come separately, RespSepData with a non-Invalid state already means "globally observed". G.b applied this rule retroactively back to Issue C. RespSepData_I does not mean that (CHI-H §B2.7.4, Table C5.10).
- **Streaming ordered writes (OWO)**: the requester waits for DBIDResp before issuing the next write, sends each CompAck only after the Comps of all earlier writes, and Home makes the write visible only after CompAck. This is how PCIe-style posted-write ordering is carried over CHI (CHI-H §B2.7.5.3).
- **CHI requires multi-copy atomicity** of every component. "Same address" means the same 64-byte line **and** the same PAS (CHI-H §B2.7.1).

### CHI IDs (CHI-H §B2.4)
- **TxnID** is 12 bits, and a Requester may have at most **1024** requests outstanding. Each must be unique per Requester while outstanding. A retried request may use a new TxnID.
- **DBID** is chosen by the Completer and becomes the TxnID of write data or CompAck. With more than 1024 buffers, DBID is unique only together with the SrcID.
- Separate follow-up responses (Persist, StashDone, TagMatch) carry TxnID 0 and an 8-bit **Group ID** (PGroupID, StashGroupID, TagGroupID). That lets the TxnID be freed early.
- In a **multi-request**, each data or response message names its line with **CacheLineID** (= address bits [11:6]) (CHI-H §B13.10.66).

## Streams: total order

- **ATB**: "must preserve the order of trace bytes, even between trace with different ATIDs". The spec itself points out that this "differs from … AXI … where ordering is preserved only between transactions with the same ID" (ATB-C §4.1).
- **AXI-Stream**: "The reordering of transfers is not permitted". AXIS-B §4.2 lists the advantages: interleaving seen by a Receiver is not increased, system predictability improves, a transfer can be known to have arrived by seeing a later transfer from the same Transmitter arrive, and complexity is reduced. A zero-byte transfer with TLAST "pushes through" everything before it (AXIS-B §2.6). Different TID/TDEST streams may interleave per transfer (AXIS-B §2.7, §4.1).

## Where the sources agree

- Ordering is only ever guaranteed **per source** and only between transactions that are "the same" in some sense: same ID (AXI), same address or range (CHI), same stream (AXI-Stream).
- To order things that the protocol does not order, **wait for completion** (AXI-L §A5.3; the same principle underlies CHI ReadReceipt and DBIDResp).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Write data interleaving | AXI3 (AXI-B, AXI-C): write data with different IDs may interleave, using the `WID` signal | AXI-Hc §A5.2 and G-AXI §7: "deprecated in AXI4 and later". `WID` exists only in AXI3 | AXI-C §8.4: "Most slave designs do not support write data interleaving". §8.5 gives its benefit (an interconnect can merge slow and fast write streams without stalling). §13.16 removes it in AXI4, and "the WID signals are removed to reduce the pin-count of the interface". The legacy note says "The majority of AXI3 masters do not support write interleaving" |
| …and back again | AXI4/AXI5 Valid-Ready: write data strictly in request order | AXI-L §A5.5: with **credited** transport, data for different transactions may interleave **if they use different Resource Planes** | Not the old WID scheme: interleaving is tied to Resource Planes, not to IDs. *Editor's note (not from the sources): because each RP is an independent queue, this probably avoids the reordering cost of WID interleaving. AXI-L gives no reason* |
| Does Endpoint Order imply Request Order? | G-CHI §4: "If you set Endpoint Order, Request Order is implied" | Same paragraph: "However, in CHI-D and beyond, signaling Endpoint Order no longer implies Request Order" | Changed in CHI Issue D. Check which CHI issue your IP implements |
| How many CHI transactions can be outstanding? | G-CHI §3: TxnID is "an **8-bit** field"… "up to 256 **or 1024** outstanding transactions" | G-CHI §16: TxnID grew to **10 bits in CHI-D** and **12 bits in CHI-E**. CHI-H §B2.4.2 confirms a 12-bit field with outstanding requests still capped at **1024** | *Editor's note (not from the sources):* The guide's §3 text predates CHI-D and was only partly updated. The extra TxnID bits give implementations freedom in how they allocate IDs, not more outstanding requests |
| Multi-copy atomicity | CHI-H §B2.7.1: **required** of every CHI component. AXI-L §A6.2: required from AXI Issue G | AHB-C §9.2: an optional property, default False | *Editor's note (not from the sources):* CHI and AXI5 serve Armv8/v9 application systems, where the memory model needs it. AHB5 also serves simpler microcontrollers |
| Domain default when AxDOMAIN is absent (affects which ordering/visibility applies) | AXI-L §A8.3.4, first paragraph: Cacheable requests are assumed **Non-shareable** | AXI-L §A8.3.4, a few lines later: Cacheable requests are assumed **Shareable** | An **internal contradiction in AXI Issue L**. Until Arm corrects it, state the assumption explicitly in your interface documentation |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- An AXI Subordinate that cannot reorder can simply process requests in arrival order. That is always legal, and it just echoes the ID (AXI-L §A5.1.1).
- A Manager with ID signals **cannot** connect to a Subordinate with none, because BID and RID must echo AWID and ARID (AXI-L §A5.1.1). Put an ID-reflecting adapter in between.
- For producer/consumer flags over AXI without Ordered Write Observation, wait for the data write's BRESP before writing the flag.

## Related articles

- [Memory types and cache attributes](memory-types-and-cache-attributes.md)
- [Cache coherency fundamentals](cache-coherency-fundamentals.md)
- [CHI architecture](chi-architecture.md)
- [Debug trace (ATB)](debug-trace-atb.md)

## Sources

AMBA2, AHB-C, AXI-B, AXI-C, AXI-Hc, AXI-L, AXIS-B, ATB-C, CHI-H, G-CHI. See [Source key](sources.md).
