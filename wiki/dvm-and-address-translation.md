# DVM and address translation (SMMU, DTI, LTI)

> How virtual memory is managed across a chip. **DVM** messages tell other agents to invalidate cached translations. **DTI** and **LTI** carry translation requests to and from a System MMU (SMMU).

## In plain words

CPUs use **virtual addresses**, and a page table maps them to physical ones. Devices such as GPUs, NICs and PCIe endpoints can use virtual addresses too, through a **System MMU (SMMU)**, also called an IOMMU. Translations are cached in **TLBs** all over the chip. When software changes a page table, every stale TLB copy must be thrown away. That is what **Distributed Virtual Memory (DVM)** messages do: "invalidate TLB entries for ASID x", followed by "Sync: tell me when you've all finished".

The SMMU itself is often split into pieces:
- a **TCU** (Translation Control Unit) that walks page tables,
- one or more **TBUs** (Translation Buffer Units) sitting next to devices and caching translations.

**DTI** is the protocol between TBU (or PCIe Root Port) and TCU. **LTI** is a lighter protocol between a device and a nearby TBU (G-SYS §4.4.2).

## DVM messages

Operations (`DVMType`, AXI-Hc §D13.1; AXI-L §A15.3; CHI-H §B8.4; G-CHI §5):
- 000 TLB Invalidate (TLBI), including **range** TLBI (DVM v8.4+) and **GPT** TLBI for RME (`Stage` = 0b11, DVM v9.2)
- 001 Branch Predictor Invalidate
- 010 / 011 Physical / Virtual Instruction Cache Invalidate
- 100 **Synchronization** (Sync)
- 110 Hint: in AXI-L only, a reserved slot "for future Hint messages" (AXI-L §A15.3.6). CHI-H marks 101–111 all reserved.

DVM targets only **read-only structures** (TLBs, branch predictors, instruction caches), so it only ever *invalidates*. Invalidating more than asked is functionally correct, it just costs performance (CHI-H §B8.1; AXI-L §A15.1).

| | ACE / ACE5 / ACE5-LiteDVM | AXI5 (Issue L) | CHI (Issue H) |
|---|---|---|---|
| Transport | AR/R (issue), AC/CR (receive) | AC channel (receive), CR response. DVM Complete on AR | DVMOp request to the **MN**. MN broadcasts SnpDVMOp to RN-Fs and RN-Ds (optionally back to the sender too) |
| Parts per message | Some operations need two parts, some one | One or two AC transfers, sent back-to-back. The second part must not wait for a response to the first (AXI-L §A15.4) | Request: REQ.Addr plus the lower **8 bytes of write data** (after a DBIDResp). Snoop: **always two** SnpDVMOp flits, P1 and P2, with the same TxnID, distinguished by SNP.Addr[0], in either order, and **one** SnpResp (CHI-H §B8.2.1, §B8.4.2) |
| Completing a Sync | Receiver issues a **DVM Complete** transaction | DVM Complete on AR (ARSNOOP=1110, unique ID, Shareable) | No DVM Complete message. The snoop response itself means "done" |
| Support levels | `DVM_Message_Support`: Bidirectional / Receiver / False | Receiver / False. **Bidirectional is deprecated** (AXI-L §A15.2) | `DVM_Support`: v8, v8.1, v8.4, v9.2 (CHI-H §B16.1.22) |
| Who may receive | — | A Manager that has done the Coherency Connection handshake (SYSCOREQ/SYSCOACK) | An RN-F or RN-D that has done SYSCOREQ/SYSCOACK |

Arm cores generate a DVM Sync as a result of a **DSB** instruction (G-CHI §5).

### CHI DVM flow rules (CHI-H §B8.2)
- **Non-sync**: the MN may send **Comp early**, before all the snooping is done, if it guarantees to order that DVMOp ahead of any later Sync from the same source. Sending a SnpResp means "I've passed it on and can take another", *not* "it's done".
- **Sync**: the requester may send a Sync only after **every earlier DVMOp it covers has received Comp**. A snoopee sends its SnpResp for a Sync only when all earlier DVM operations have **really completed** locally.
- **Flow control**: only one SnpDVMOp(Sync) may be outstanding from an MN to a given RN. Every RN-F/RN-D must accept at least **two** SnpDVMOps at once (one Non-sync plus one Sync). The MN must keep at least one tracker entry reserved for Non-sync DVMOps so they always progress.
- A Non-sync snoop must be answered without depending on any other transaction. A Sync may depend on other transactions, but must still complete in a timely manner.
- A SnpDVMOp(Sync) at an RN that has issued StashOnceSep requests must wait for the StashDone of any stash that used an invalidated page.

### Payload details worth knowing (CHI-H §B8.4; AXI-L §A15.3)
- **Range TLBI**: the invalidated range is BaseAddr up to BaseAddr + (Num+1) × 2^(5×Scale+1) × granule, where the granule (4K/16K/64K) comes from `TG`. `TTL` is an optional level hint.
- **ASID and VMID** may be 8 or 16 bits, and a message does not say which. 8-bit agents set the upper byte to zero. A mixed system over-invalidates, so Arm expects maintenance to be done by a 16-bit-capable agent. The upper VMID byte travels in `VMIDExt` (CHI) or `ACVMIDEXT` (AXI).
- Every DVM receiver must accept both PICI and VICI forms, even if its I-cache is only one kind.
- Inner vs Outer **DVM domain** is still selected (by `SnpAttr` in CHI), and optional `BROADCASTTLBIINNER/OUTER` and `BROADCASTICINVAL` pins control what a requester broadcasts (CHI-H §B16.2.7, §B16.2.9).
- The interconnect must **detect and suppress** DVM operations that some receiver's `DVM_Support` level cannot handle, and still respond correctly (CHI-H §B16.1.22).
- AXI5 DVM addresses go up to 57-bit VA and 52-bit PA. AC/CR are **ordered** channels: no reordering (AXI-L §A15.4).

## DTI: Distributed Translation Interface (DTI-J)

- **Who uses it**: implementations of the Arm SMMUv3 architecture. The parts are:
  - a **TCU**, which does table walks and holds the SMMU programmers' model;
  - one or more **TBUs**, which intercept transactions, request translations from the TCU and cache them;
  - optionally a PCIe Root Port with ATS;
  - a DTI interconnect between them (DTI-J §B1.1).
- **Two protocols**: **DTI-TBU** (TBU↔TCU) and **DTI-ATS** (PCIe Root Port with Address Translation Services ↔ TCU) (DTI-J §B1.1).
- **Versions**: Issue J describes DTI-TBUv3–v6 and DTI-ATSv1–v5. TBUv1/v2 are described only in Issue E.c (DTI-J §B1.1; DTI-Ec, Mar 2024). All TBUs on one TCU are expected to use the same version "because the SMMU architecture does not permit TBUs in the same implementation to have different feature sets". SMMUv3.2 needs DTI-TBUv2 or later, and RME needs DTI-TBUv3 or later (DTI-J §B3.1).
- **Why "distributed"**: "DTI connections can cover large distances across an SoC. Most implementations do not include a standalone SMMU component", so TBUs can sit close to the devices. A device may also build its own TBU. A fully coherent device needs this because its caches must be tagged with physical addresses, so "translation is performed before the first level of caching" (DTI-J §B1.1.1).
- **Point-to-point and message-based**:
  - **Message groups** (DTI-J §B2.1.1): connection/disconnection, translation request, invalidation and sync, register access (TBU only) and page request (ATS only, for PCIe PRI).
  - **Message format**: messages are fixed-length and a whole number of bytes. The low 4 bits are the message type. Types 0xE/0xF are IMPLEMENTATION DEFINED (§B2.1.2).
  - **Message sizes**: for example, `DTI_TBU_TRANS_REQ` is 160 bits and `DTI_TBU_INV_ACK` is 8 bits (Table B2.2–B2.3).
- **Flow control by tokens**: translation tokens and invalidation tokens. Requests consume tokens and responses return them. The token counts are agreed in the connect handshake, and the TCU may grant fewer than requested from DTI-TBUv5 (§B2.1.3, §B3.1.2).
- **Channel states**: DISCONNECTED → REQ_CONNECT → CONNECTED → REQ_DISCONNECT.
  - A Connect Deny "indicates a system failure, for example, due to a badly configured system" (DTI-J §B2.2).
  - Each TBU or Root Port has its own channel, tokens and ID space (§B2.2.4).
  - A DTI-ATS channel must not be disconnected while ATS is enabled in any PCIe Endpoint (§B2.2.3).
- **Invalidation** (DTI-J §B3.3.5):
  - The TCU sends `INV_REQ` messages, then a `SYNC_REQ`. `INV_ACK` only returns a token.
  - Before answering `SYNC_ACK`, the TBU must make sure the translations are gone **and** the transactions that used them have completed downstream.
  - **Deadlock rules**:
    - A TBU must not wait for a translation that returned a `TranslationStall` fault.
    - `INV_REQ`/`INV_ACK` must not wait for `SYNC_ACK`.
    - The spec's reason: "Invalidation operations must be able to proceed without waiting for downstream transactions to be completed - this is because those transactions might not be able to complete until the invalidation has been accepted."
  - For ATS, SMMUv3 requires the TCU to invalidate the TBU first and the PCIe Endpoint's ATC second (§B4.3.6).
- **Transport** (DTI-J ch. B5):
  - The transport may be any medium that neither reorders nor interleaves messages.
  - The spec's example is a pair of **AXI5-Stream** links, one per direction (`*_DTI_DN`, `*_DTI_UP`), with `Continuous_Packets = True`.
  - `TLAST` marks the last transfer of a message and must be present.
  - `TID` gives the source on the downstream link and `TDEST` the destination on the upstream link. The spec recommends that a TBU does *not* drive them, and that the DTI interconnect adds `TID` bits ("There is only one TCU in the network").

## LTI: Local Translation Interface (LTI-E)

- **What it is**: a point-to-point protocol between an **IO Manager** and a **TBU**. "LTI enables devices to directly request a translation for each transaction while leaving the TBU to manage the Translation Lookaside Buffer (TLB). This enables translations to be requested before ordering requirements are met, avoiding the need to pass transactions through the TBU" (LTI-E §B1.1).
- **Components** (LTI-E §B1.2):
  - a Bus Interface Unit (**BIU**) fetches a translation for each transaction over LTI;
  - a **TLBU** caches translations and asks the TCU over DTI on a miss;
  - the BIU and TLBU are typically packaged together as a TBU.
- **Three integration styles** (LTI-E §B1.2):
  - *In-line*: every transaction passes through the SMMU, typically over AXI, and the device is unaware of translation. LTI is used inside the TBU, between BIU and TLBU.
  - *Lookaside*: the device makes an LTI request per transaction, and its data goes over its own native interface. The spec calls this "more complex than in-line".
  - *Cached*: the device requests translations over **DTI** and caches them in its own TLB. It must support invalidations. This is "the most complex but … can be the most efficient option for devices with specific caching requirements".
- **Channels** (LTI-E §B2.1, ch. B7):
  - **LA** (request) → **LR** (response) → **LC** (completion, sent after the downstream transaction completes). "There are no flows where any of these three stages can be skipped."
  - An LR response may come in the same cycle as the request, "to enable tightly coupled TLBs".
  - **LT** (tag) revokes cached translations.
  - LC only counts completions per completion tag. There are two tags "to enable invalidation to take place without stopping the transaction flow".
- **Flow control**: credits per channel and per Virtual Channel (`LxCREDIT`), with at most 15 per VC and no combinational paths between `LxCREDIT` and `LxVALID`. Virtual Channels on LA/LR exist "to enable one VC to progress when another is blocked, to avoid deadlock" (LTI-E §B2.2–B2.3).
- **Interface states**: `LMOPENREQ`/`LMOPENACK` give ST_CLOSED → ST_OPENING → ST_OPEN → ST_CLOSING. The Subordinate can ask to close with `LMASKCLOSE`, for example in response to a Q-Channel quiescence request (LTI-E ch. B8).
- **Translation flows**: Stall, ATST (PCIe ATS-translated), NoStall and PRI (LTI-E §B1.4).
  - "Stall flow is the most common flow for LTI Managers".
  - Stall is "not recommended for use with PCIe, because of dependencies between outgoing transactions to PCIe from a CPU, and incoming transactions from PCIe through the SMMU".

## Untranslated transactions (AXI5)

AXI5 can carry SMMU information directly on requests: StreamID (`AxMMUSID`), SubstreamID, secure StreamID, flow type (Stall / ATST / NoStall / PRI) and the **TRANSFAULT** response. This lets an untranslated request reach a TBU with everything it needs (AXI-L ch. A13).

The feature has four versions (`Untranslated_Transactions` v1–v4, AXI-L §A13.2):

| Version | Adds |
|---|---|
| v1 (= True) | StreamID, SubstreamID, secure-SID, `AxMMUATST` |
| v2 | `AxMMUFLOW` (Stall / ATST / NoStall / PRI). Needs a 3-bit response for TRANSFAULT, which is used only in the PRI flow and on all beats |
| v3 | `AxMMUVALID`: one interface may mix physical and virtual addresses. Translated and untranslated transactions must not share an in-flight ID |
| v4 | `AxMMUPM` (GDI protected mode) and `AxMMUPASUNKNOWN` (PCIe XT mode) |

For PCIe, StreamID = Requester ID and SubstreamID = PASID (AXI-L §A13.5). `StashTranslation` and `UnstashTranslation` are hints that pre-load or drop a translation in a TBU (AXI-L §A13.9–§A13.10).

In CHI, devices assigned to Realms (**RME-DA / RME-CDA**) send `StreamID` (= PCIe Requester ID) and `SecSID1` (= PCIe T bit) on their requests to the host, which checks them against a Device Permission Table and the GPT (CHI-H §B10.7). A device must not send DVMOps to the host.

## Where the sources agree

- DVM provides invalidate + sync semantics in ACE, AXI5 and CHI. "CHI DVM Syncs are similar to those in ACE. Both check that previously issued DVM operations have been completed" (G-CHI §5).
- DTI lets SMMU functions be **distributed** across the SoC, with TBUs near the devices (DTI-J §B1.1.1; G-SYS §4.4.2).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Can LTI translations be cached? | G-SYS §4.4.2 (May 2025): LTI is "designed for short distances **without any caching**" | LTI-D (Aug 2025) and LTI-E (Mar 2026) §B1.3, §B1.5: configurable. Either "translations must be used immediately and must not be cached", **or** "translations can be cached" with LT-channel invalidation (a translation cache) | A version difference: LTI-E Table C7.4 lists "Translation cache support added to reduce request rate" as new in Issue D. The guide describes the earlier model. The `LTI_CACHE_SUPPORT` property must match on Manager and Subordinate, or the two are "Not compatible" (LTI-E §B12.5) |
| DVM Complete | ACE (AXI-Hc §D13.1): a DVM Sync requires a separate **DVM Complete** transaction | CHI (G-CHI §5): "CHI does not require a DVM Complete message" | *Editor's note (not from the sources):* CHI folds completion into the snoop response to the MN, which removes a transaction type |
| ACE5-LiteDVM capabilities | AXI-Hc: DVM support defaults to **Bidirectional** | AXI-L §B2.1.3: "snoop data transfer and bidirectional DVM messages are not supported" | AXI-L §B2.1.3 explains: the most common use is "a system MMU to receive invalidation messages", and issuing DVMs "is mostly done by fully coherent CPUs, so is beyond the scope of this specification" |
| DTI transport | DTI-E (2020) §6.2: uses **AXI4-Stream** as the example transport | DTI-J (2026) ch. B5: uses **AXI5-Stream** (with `Continuous_Packets = True`) | An example change between issues. "The DTI protocol can be conveyed over different transport layer mediums", and AXI-Stream is only "an example transport medium" (DTI-J §B5.1; DTI-Ec §6.1) |
| Bidirectional DVM on AXI | AXI-Hc: `DVM_Message_Support` = Bidirectional is a normal option | AXI-L §A15.2: Bidirectional is **deprecated** "in this specification" | AXI-L §B2.1.3: issuing DVM messages "is mostly done by fully coherent CPUs, so is beyond the scope of this specification" |
| DVM Hint opcode | AXI-L §A15.3.6: `DVMType` 0b110 = Hint, a reserved space for future hints | CHI-H §B8.4.1: 0b101–0b111 all **reserved** | No Hint messages are defined yet in either spec. AXI keeps the encoding for future use. A CHI↔AXI bridge must not forward 0b110 into CHI |
| What SYSCOREQ/SYSCOACK connects | AXI-L §A15.6: the Coherency Connection lets a Manager receive **DVM messages** on AC (AXI has no data snooping) | CHI-H §B15: it connects an RN-F to the **coherency (snoop) domain and the DVM domain** | Same signal names, different scope. In AXI only DVM depends on the handshake |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- An interface with an address width **below 32 bits cannot support DVM** (AXI-Hc §D13.1).
- In a DTI design, a TCU "must always be able to accept a Connect Request whenever a TBU or PCIe RP is powered up" (DTI-J §B2.2.1). The spec leaves the method out of scope.
- A TBU must answer register-access messages "without requiring the completion of downstream transactions, or the progress of other DTI transactions" (DTI-J §B3.4.5).
- In a TBU, if an ordered transaction is stuck behind a stalled translation when a `SYNC_REQ` arrives, discard the DO_NOT_CACHE translation and re-request it. This is the spec's own deadlock example (DTI-J §B3.3.5.3).
- In a CHI RN, pre-allocate room for **both** SnpDVMOp parts before the MN can send them, and send the single SnpResp only after both parts have arrived (CHI-H §B8.2.3.2).
- An AXI5 Manager must accept DVM messages even in the "Connect" state, before SYSCOACK is seen HIGH (a race), and still sends DVM Complete for a Sync received before it disconnects (AXI-L §A15.6).

## Related articles

- [Cache coherency fundamentals](cache-coherency-fundamentals.md)
- [ACE coherency extensions](ace-coherency-extensions.md)
- [CHI architecture](chi-architecture.md)
- [Streaming interfaces](streaming-interfaces.md) (AXI-Stream as DTI transport)
- [Protection and security attributes](protection-and-security.md)

## Sources

AXI-Hc, AXI-L (read in full), CHI-H (read in full), DTI-E, DTI-J, LTI-D, LTI-E, G-CHI, G-SYS. See [Source key](sources.md).
