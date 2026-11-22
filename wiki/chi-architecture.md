# CHI: Coherent Hub Interface architecture

> CHI is AMBA's scalable coherent interconnect architecture. Nodes exchange packetised messages (flits) over four channels through a network, with a Home Node coordinating coherency for each address. This article is based on a full read of CHI Issue H (CHI-H), the latest issue.

## In plain words

AXI and ACE are *wires between two blocks*. CHI is more like a *network protocol* for a whole chip:
- Every component is a **node** with a Node ID.
- Messages are **flits** carrying source and target IDs, so routers can send them across a ring, mesh or crossbar.
- For any address, one **Home Node** acts as the referee. It orders requests, snoops caches and talks to memory.
- Flow control uses **credits**, not READY signals, which suits long wires and high clock speeds.

A good mental model: a CPU (Request Node) asks the Home Node "give me line X so I can write it". The Home Node checks who else has a copy, tells them to give it up (snoops), gets the data from the best place (another cache, its own cache, or memory) and replies. The requester then says "got it" (CompAck), so the Home Node can move on to the next request for that line.

## Layers (CHI-H §B1.1.3)

| Layer | Unit | Job |
|---|---|---|
| Protocol | Transaction | Request/response generation, cache-state transitions, transaction flows, retry (protocol credits) |
| Network | Packet | Packetisation, adds SrcID/TgtID for routing |
| Link | Flit | Credit-based flow control (L-Credits), deadlock-free channels |

In CHI, one packet = one flit = one phit (CHI-H §B1.3).

## Nodes (CHI-H §B1.6; G-CHI §3)

| Node | Name | Role |
|---|---|---|
| RN-F | Fully coherent Request Node | Has coherent caches and must answer snoops (a CPU cluster). May issue every request type except ReadNoSnpSep |
| RN-D | I/O coherent Request Node + DVM | No coherent cache, but receives **DVM snoops only** (for example an SMMU) |
| RN-I | I/O coherent Request Node | No coherent cache and **no SNP channel at all** (a DMA engine, an I/O bridge) |
| HN-F | Fully coherent Home Node | **PoC and PoS** for its addresses. Orders requests, sends snoops, often holds a system cache (SLC) and a **snoop filter** |
| HN-I | Non-coherent Home Node | Orders requests to I/O space. Not a PoC, cannot process snoopable requests (but must still answer them) |
| MN | Miscellaneous Node | Receives DVMOps and broadcasts them as SnpDVMOp. Orders Sync vs non-Sync DVMs, but plays no part in memory ordering |
| SN-F | Subordinate Node (Normal memory) | Memory controller behind an HN-F |
| SN-I | Subordinate Node (I/O) | Peripheral or non-coherent memory. Only SN-I may receive WriteNoSnpDef (CHI-H Table C3.3) |

RN-D and RN-I cannot issue allocating reads, CopyBacks, CleanUnique, MakeUnique or Evict, because they have no coherent cache (CHI-H §C3.1).

## Channels and identifiers

- **REQ** (requests), **RSP** (data-less responses), **SNP** (snoops and DVM), **DAT** (data). Each is TX or RX at a node (CHI-H §B13.4).
- Only HN-F and MN send on SNP. The SNP flit has **no TgtID**, because snoop routing is implementation-defined (for example from a snoop filter) (CHI-H §B13.9.3; G-CHI §3).
- Main IDs (CHI-H §B2.4):
  - **SrcID / TgtID**: node IDs, 7 to 16 bits wide (`NodeID_Width`). Issue H raised the maximum to 16.
  - **TxnID**: a **12-bit** field, unique per outstanding request. A Requester may have at most **1024** requests outstanding. TxnID can be reused once all responses are in, even if a separate TagMatch, StashDone or Persist is still pending (those carry TxnID 0 and a *Group ID* instead).
  - **DBID**: the Completer's buffer ID, used as the TxnID for write data and CompAck.
  - **ReturnNID / ReturnTxnID** (HN → SN): tells the SN where to send data directly (DMT) or where the requester waits for DBIDResp (DWT).
  - **FwdNID / FwdTxnID** (in forwarding snoops): tells the snooped cache where to send data directly (DCT).
  - **HomeNID** (in CompData): tells the requester where to send CompAck when data came from somewhere else.
  - **LPID**: identifies the logical processor inside a multi-core requester. Required for exclusives and for Non-snoopable Non-cacheable or Device accesses.
- Many fields **share flit bits** depending on the message. For example LPID, PGroupID, StashGroupID and TagGroupID all live in the same request bits (CHI-H §B13.10).

## How a transaction is built (CHI-H §B2.3, ch. B5)

| Class | Examples | Typical response pattern |
|---|---|---|
| Read | ReadNoSnp, ReadOnce, ReadClean, ReadNotSharedDirty, ReadShared, ReadUnique, ReadPreferUnique, MakeReadUnique | CompData (or RespSepData + DataSepResp) then **CompAck** from an RN-F |
| Dataless | CleanUnique, MakeUnique, Evict, StashOnce*, CleanShared, CleanInvalid, MakeInvalid… | Comp (plus CompAck for CleanUnique/MakeUnique) |
| Write: Immediate | WriteNoSnpFull/Ptl, WriteUniqueFull/Ptl, WriteNoSnpDef, WriteUnique*Stash | DBIDResp + Comp, or a combined **CompDBIDResp**, then write data |
| Write: Zero | WriteNoSnpZero, WriteUniqueZero | No data sent at all |
| Write: CopyBack | WriteBackFull/Ptl, WriteCleanFull, WriteEvictFull, WriteEvictOrEvict | CompDBIDResp then CopyBackWriteData (or Comp + CompAck if Home declines the data) |
| Combined Write + CMO | WriteBackFullCleanInv, WriteNoSnpPtlCleanSh… | Write responses plus **CompCMO** (and Persist for persistent CMOs) |
| Atomic | AtomicStore, AtomicLoad, AtomicSwap, AtomicCompare | DBIDResp, data, then Comp or CompData |
| Other | DVMOp, PrefetchTgt, PCrdReturn | DVMOp is write-like with 8 bytes of data. **PrefetchTgt gets no response at all** |

Things that trip up newcomers:
- **Write data waits for a DBID.** A requester may not send write data until it has a DBIDResp, DBIDRespOrd or CompDBIDResp (CHI-H §B2.3.2).
- **The requester must never need CompAck to make progress.** An RN must be able to accept every Comp and CompData for its outstanding transactions without sending any CompAck (CHI-H §B13.4.1).
- **Partial reads (<64 B) cannot use DCT**, and forwarding snoops are never used for requests smaller than 64 bytes (CHI-H §B4.4).
- **A completion means "ordered".** Comp/CompData guarantees that the request has reached the PoS/PoC and is ordered against later requests to the same address from anyone (CHI-H §B4.5.1).

## Cache states and coherency (CHI-H ch. B4)

Seven states: I, UC, UCE, UD, UDP, SC, SD. See [Cache coherency fundamentals](cache-coherency-fundamentals.md). Key rules:
- **UCE** (Unique Clean Empty) never returns or forwards data. **UDP** (Unique Dirty Partial) must return its data to Home and never forwards it (CHI-H §B4.1).
- Silent transitions are allowed (for example UC → I eviction, UC → UD store, UD → SD local sharing), but **UC → UCE is not permitted** (CHI-H §B4.6).
- Before sending CleanInvalid, MakeInvalid or Evict, the requester must already have moved the line to I (CHI-H §B4.7.2).
- The `Resp` field means different things in different messages, which is a classic source of bugs (CHI-H §B4.5):
  - in **CompData**: the state the requester may end in;
  - in **write data**: the state when the data was sent;
  - in **SnpResp**: the snoopee's state *after* responding.
- Encodings: `Resp[2]` = PassDirty, `Resp[1:0]` = state (I=00, SC=01, UC/UD=10, SD=11) (CHI-H Table B13.34).

### Snoops (CHI-H §B4.3–§B4.10)

- **Non-forwarding** snoops (SnpShared, SnpUnique, SnpCleanInvalid…) may go to many RN-Fs. A **forwarding** snoop (SnpSharedFwd, SnpUniqueFwd…) may go to only **one** RN-F.
- Home may substitute snoops: any invalidating snoop can become SnpUnique or SnpCleanInvalid, and any forwarding snoop can become its non-forwarding form. The snoopee may also treat "forward" as a hint (CHI-H §B4.4.2).
- **RetToSrc** asks the snoopee to also send a copy to Home. Home may set it on only one snoop. A Dirty line is always returned, whatever RetToSrc says (CHI-H §B4.9).
- **DoNotGoToSD** stops a forced move into SD (useful for caches without an Owned state).
- **SnpQuery** (CHI-E) asks for the precise state without changing it. It is used to resolve MakeReadUnique(Excl) cheaply (CHI-H §B4.3).
- **SnpPreferUnique** behaves differently if the snoopee is in the middle of an exclusive sequence (it keeps a shared copy). Otherwise it invalidates. Home learns which from the response (CHI-H §B4.8.3.5).

### Hazards (CHI-H §B4.11, §B5.6)

- An RN-F must answer snoops **without depending on its own outstanding requests** (except SnpDVMOp Sync). If it has already received part of the data for a request to the same line, it waits for the rest, then answers.
- If a snoop hits a pending CopyBack, the CopyBack still completes, but the state it reports is the state *after* the snoop. If that is I, the write data is all zero with BE=0.
- At Home: one outstanding snoop per line per snoopee. After sending a Comp, Home must not snoop that line again until it has the CompAck (or CopyBack data).

## Ordering and multi-request (CHI-H §B2.6, §B2.7)

- `Order` field: 00 none; 01 "request accepted" (HN → SN only); 10 **Request Order** (or **OWO**, Ordered Write Observation, when ExpCompAck=1); 11 **Endpoint Order** (CHI-H Table B13.22).
- Ordered requests are gated by **ReadReceipt** (reads), **DBIDResp** or **DBIDRespOrd** (writes).
- CHI **requires multi-copy atomicity** of every compliant component. "Same address" means same cache line **and** same PAS (CHI-H §B2.7.1).
- **Multi-request** (Issue H): one REQ flit can cover up to **64 cache lines** (128 B–4 KB), using MultiReq, NumReq and per-line **CacheLineID** in the responses. The coherency granule is still 64 B and the request may be split anywhere. It is limited to non-allocating reads and immediate writes, must not cross 4 KB, and is never used for exclusives (CHI-H §B2.6, §B13.10.64–66).

## Memory attributes (CHI-H §B2.8)

- `MemAttr` = {Allocate, Cacheable, Device, EWA}, plus `SnpAttr` (snoopable or not) and `LikelyShared` (an allocation hint).
- Device types use the Arm names **Device nRnE, Device nRE and Device RE**. There is **no Write-Through type** in CHI. Device accesses must use ReadNoSnp/WriteNoSnp*, and neither CMOs nor PrefetchTgt may target Device memory.
- From Issue H, CMOs may access **only Cacheable** memory (CHI-H Table C5.11).
- Data bus widths are **128, 256 or 512 bits only** (CHI-H §B13.9.4, §B16.1.13).

## Performance features

| Feature | Since | Idea |
|---|---|---|
| **Retry + protocol credits** | CHI-A | A busy Completer replies RetryAck(PCrdType), later sends PCrdGrant, and the request is resent with that credit. A requester that no longer needs the credit returns it with **PCrdReturn**. Up to 16 credit types. In Issue H Retry is **optional** (`Retry_Support` = True / RP0_Only / False) (CHI-H §B2.10, §B16.1.38) |
| **DMT**, Direct Memory Transfer | CHI-B | The SN sends read data *directly* to the RN (ReturnNID/ReturnTxnID). Home sends the ReadNoSnp to the SN only after the snoop responses show that no cache is supplying data (CHI-H §B5.1) |
| **DCT**, Direct Cache Transfer | CHI-B | A snooped RN-F forwards data directly to the requester (FwdNID/FwdTxnID). The forwarded copy and the snoop response travel on different channels, in any order |
| **DWT**, Direct Write Transfer | CHI-E | Home sends WriteNoSnp with DoDWT=1, the SN sends DBIDResp to the RN, and the RN sends data straight to the SN. Not allowed with OWO, Zero writes or failed exclusives |
| **PrefetchTgt** | CHI-B | A hint straight from RN to SN. It gets no response and no RetryAck, the RN may forget it as soon as it is sent, and the SN may drop it. `PrefetchTgtHint` (CHI-G) lets a C2C link receiver re-create a dropped prefetch |
| **Cache stashing** | CHI-B | Push data into a chosen cache (StashNID/StashLPID). It is always a hint. The target can *DataPull* through its snoop response. StashOnceSep (CHI-E) splits Comp and StashDone |
| **Atomics** | CHI-B | Far atomics executed in HN or SN (see [Atomics](exclusive-locked-and-atomic-access.md)) |
| **CopyAtHome (CAH)** | CHI-F | Home says "I kept a copy", so a later unmodified CopyBack can complete without moving data |
| **DataSource / DataTarget** | CHI-F/G | DataSource (8 bits since CHI-G) reports distance, type of completer, Hit-Dirty and prefetch usefulness. DataTarget hints how likely a line is to be reused and how deep to place it (CHI-H §B11.2–§B11.3) |
| **Limited Data Elision** | CHI-G | Skip sending all-zero or replicated data beats (NumDat, Replicate) |
| **Multiple interfaces / replicated channels** | CHI-E | Duplicate a whole interface (separate NodeID and TxnID pool) or just a busy channel (shared NodeID and TxnID pool, per-subchannel credits) (CHI-H §B13.7) |
| **Resource Planes + shared credits** | CHI-H | Up to 8 independent credit pools on REQ and SNP (`Num_RP_REQ`, `Num_RP_SNP`), optionally with shared credits |

## Exclusives, DVM, errors, security, MTE

Covered in detail in the related articles:
- **Exclusives**: LP monitor in the RN-F plus a PoC monitor in the HN-F (CHI-H ch. B6). See [Atomics](exclusive-locked-and-atomic-access.md).
- **DVM**: DVMOp to the MN, two-part SnpDVMOp, Sync semantics, range TLBI (CHI-H ch. B8). See [DVM](dvm-and-address-translation.md).
- **Errors**: RespErr OK / EXOK / DERR / NDERR, Poison, DataCheck, interface parity (CHI-H ch. B9). See [Parity and RAS](interface-protection-parity-and-ras.md).
- **RME, MEC, Device Assignment, GDI**: a 3-bit PAS field, MECID, StreamID/SecSID1 (CHI-H ch. B10). See [Security](protection-and-security.md).
- **QoS, MPAM, PBHA, CBusy, TraceTag** (CHI-H ch. B11). See [QoS](qos-and-traffic-modelling.md).
- **MTE**: 4-bit tags per 16 bytes, TagOp Invalid/Transfer/Update/Match/Fetch (CHI-H ch. B12).

## Link-level behaviour (CHI-H ch. B13–B15)

- **L-Credits**: 1–15 per channel (and per Resource Plane). One per flit. A credit cannot be used in the cycle it arrives.
- **FLITPEND**: asserted exactly one cycle before a flit, for clock gating.
- **Channel dependencies**: an RN must make progress on inbound SNP without needing outbound REQ, and on inbound RSP/DAT without needing *any* other channel (CHI-H §B13.4.1).
- **Link activation**: LINKACTIVEREQ/ACK, a four-phase handshake per direction. STOP(00) → ACTIVATE(10) → RUN(11) → DEACTIVATE(01). Before STOP, the transmitter returns **every** credit with LCrdReturn flits. TX and RX links must follow each other in a timely manner (CHI-H §B14.5–§B14.6).
- **SACTIVE**: TXSACTIVE is high from before the first flit until after the last flit of all transactions. Only the interconnect may derive TXSACTIVE from RXSACTIVE (CHI-H §B14.7).
- **SYSCOREQ/SYSCOACK**: an RN-F or RN-D joins or leaves the coherency **and DVM** domain (CHI-H §B15).
- **Properties and broadcast pins**: about 40 interface properties (CHI-H §B16.1) and tie-off pins such as BROADCASTINNER/OUTER, BROADCASTATOMIC and BROADCASTMULTIREQ (CHI-H §B16.2). See [Interface properties](interface-properties-and-user-signals.md).

## Issues of CHI

| Issue | Date | Highlights (from CHI-H Appendix C5 and G-CHI §16) | Compatible with previous? |
|---|---|---|---|
| A | Jun 2014 (limited release) | First CHI | — |
| B | Aug 2017 (first public) | Atomics, DMT, DCT, stashing, RAS, MESI support, larger PA | **No** |
| C | May 2018 | Separate Comp and data for reads, CompAck after first data, combined write data + CompAck | No (DAT flit +1 bit) |
| D | Aug 2019 | CleanSharedPersistSep, Deep persistence, interface parity, MPAM, CBusy, wider TxnID, DVM early Comp | No |
| E.a / E.b / E.c | 2020–2022 | MTE, DWT, Zero writes, WriteEvictOrEvict, SnpQuery, DBIDRespOrd, ReadPreferUnique/MakeReadUnique, Combined Write + CMO, StashOnceSep, range TLBI, multiple interfaces, 12-bit TxnID. E.b: new terminology | No |
| F / F.b | 2022 / 2024 | RME, WriteNoSnpDef, CAH, PBHA, DataSource 5 bits, partial ReadOnce. F.b: MPAM width fixed to 12 bits, DVM field names aligned with AXI | No |
| G / G.b | 2024 / 2025 | MEC, RME-DA/CDA, Limited Data Elision, DataTarget + CacheLevel, PrefetchTgtHint, MTE_Support, DataSource 8 bits, Cache_State_UDP/SD properties | No |
| H | Sep 2025 | GDI (6 PAS), **PAS field replaces NS/NSE**, 16-bit NodeID, multi-request, Resource Planes and shared credits, optional Retry, Outer_Cacheable_Support, CMOs only to Cacheable memory | No |

## Where the sources agree

- CHI is the **successor to ACE** with a similar coherency model, plus snoop filters/directories and partial/empty states (G-CHI §1, §3; CHI-H §B1.1.2).
- CHI is **topology-independent** (crossbar, ring or mesh), and the interconnect implementation is up to the designer (CHI-H §B1.2; G-CHI §2).
- AXI-L says the same thing from its side: AXI "does not support data snooping", so fully coherent agents use CHI (AXI-L §A8.1).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Number of CHI issues | G-CHI §2 (v1.2, Jun 2025): "There are currently **seven** issues … A to G" | CHI-H (Sep 2025): Issue **H**, the "eleventh public release" (counting E.a, E.b, E.c, F.b and G.b) | The guide predates Issue H and counts letters, not sub-issues |
| Backward compatibility | G-CHI §2: each issue (B→G) is "not directly compatible" with the previous one, because flit widths change | — | G-CHI §2 gives the reasons per issue, for example "because the physical width of data channel attributes increase by one bit", or because "all channels have modified fields". In practice, two CHI interfaces must match on **issue and properties** to connect directly |
| TxnID width | G-CHI §3: "an 8-bit field" | G-CHI §16 (10 bits in CHI-D, 12 in CHI-E) and CHI-H §B2.4.2: **12 bits**, at most 1024 outstanding | The guide's §3 was written for early CHI. Use the flit definitions of your issue |
| When CHI started | G-AXI §2: "In 2014, the AMBA 5 Coherent Hub Interface (CHI) specification was introduced" | CHI-H: 2014 = limited release, 2017 = first public | Both are correct, with different meanings of "introduced" |
| Terms for completers | G-CHI §1: "Subordinate is synonymous with slave" | G-CHI §3 and CHI-H §B1.3: "Completer" is the responding role, "Subordinate Node" a node type | Two vocabularies in one guide. See [Terminology and roles](terminology-and-roles.md) |
| What "DWT" means | CHI-H glossary (Part D): Direct Write Transfer is "sending **Read data** directly from a Snoopee or Subordinate to the Requester" | CHI-H §B2.3.2 and §B13.10.24: DWT sends **write data** from the RN straight to the SN | An **internal inconsistency** in CHI-H: the glossary entry describes DCT/DMT. Trust the body text |
| PBHA width | CHI-H glossary: software sets "up to **two** bits" | CHI-H §B11.5 and §B13.10.29 (and AXI-L §A10.2): **4** bits | Another stale glossary entry in CHI-H. The flit field is 4 bits |
| Is Retry part of every CHI link? | G-CHI §4 and earlier issues: Retry is the base request flow-control mechanism | CHI-H §B16.1.38: `Retry_Support` may be False or RP0_Only, with Resource Planes as the alternative | *Editor's note (not from the sources):* Issue H made Retry optional so that credit-only (Resource Plane) designs avoid retry bookkeeping. Check interoperability (Table B16.41): a Completer that retries a Requester that cannot retry can deadlock |
| PrefetchTgt response | CHI-H §B4.2.6.2: **no response and no RetryAck** | AXI-L §A8.6: the AXI **Prefetch** (to which a PrefetchTgt can be converted) has a **B response** and a unique ID | *Editor's note (not from the sources):* AXI channels always complete with a handshake. CHI can drop a message-based hint cheaply. A CHI→AXI bridge must absorb the extra B response |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Get the **flit field map** for *your exact CHI issue and properties*. Field positions depend on NodeID width, address width, data width and optional fields (CHI-H §B13.9).
- Never use an L-Credit in the cycle it is received, and never send a flit without a credit (CHI-H §B14.2).
- On reset every component must hold TX*LCRDV, TX*FLITV, TXLINKACTIVEREQ and RXLINKACTIVEACK LOW (CHI-H §B14.1.3).
- Design your RN so that inbound RSP and DAT can always be sunk. Reserve buffer space for every outstanding request's data before issuing it (CHI-H §B13.4.1).
- Treat `Resp` according to the message type, not as a single "state" field (CHI-H §B4.5).

## Related articles

- [Networks-on-chip (NoC)](networks-on-chip.md)
- [Cache coherency fundamentals](cache-coherency-fundamentals.md)
- [ACE coherency extensions](ace-coherency-extensions.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Transaction IDs and ordering](transaction-ids-and-ordering.md)
- [Exclusive access and atomics](exclusive-locked-and-atomic-access.md)
- [DVM and address translation](dvm-and-address-translation.md)
- [Chiplets and chip-to-chip](chiplets-and-chip-to-chip.md)
- [Low power and wake-up](low-power-and-wakeup.md)
- [QoS and traffic modelling](qos-and-traffic-modelling.md)

## Sources

CHI-Ec, CHI-G, CHI-H, G-CHI, G-AXI, G-SYS, AXI-L. See [Source key](sources.md).
