# Chiplets and chip-to-chip links (CHI C2C, CXS)

> How AMBA extends coherent CHI traffic beyond a single die: packing CHI messages into fixed 256-byte **containers** and carrying them over links such as UCIe or a PCIe/CXL physical layer.

## In plain words

There are several ways to take an interconnect off the die. Arm's system guide says that "using CHI end-to-end lets architectural features span chip and chiplet boundaries, enabling a common memory and security model. This approach avoids protocol conversions, incompatibilities, and extra latency" (G-SYS §4.4.1).

**CHI C2C** is the spec that makes this possible. It defines how CHI messages are **packetized** into fixed-size containers for a chip(let)-to-chip(let) link. It "focuses on the packetization of CHI messages, making them suitable to be transported over a chip-to-chip link", and the format "is optimized for link utilization and latency, while avoiding complex packing and unpacking schemes". It also defines credits, routing, initialisation and the registers software uses to set the link up (C2C-B §B1.1, ch. B8, B13, B15).

## Use cases (C2C-B §B1.1)

- **Multi-chip SMP**: a few similar chips, each with attached memory that all of them share coherently.
- **Coherent accelerator attach**: an accelerator attached to a host as fully coherent or I/O coherent.
- **Hub-and-spoke**: several hosts and accelerators around a central hub, which may have memory. This topology is new in Issue B (C2C-B Table C1.2).

## Layers (C2C-B §B2.1)

| Layer | Role | Defined by C2C? |
|---|---|---|
| Protocol | Minimal conversion between on-chip CHI and CHI C2C | Yes |
| Packetization | Packs messages into containers and unpacks them. If there is no Link layer, it connects directly to the external signals | Yes |
| Link | Flits, optional CRC and retry. The container leaves room for the flit header and link-reliability bytes | No: "expected, but not required" |
| Physical | "Logic to overcome latency skew among different signals and link retraining" | No |

## Containers and messages

### Containers (C2C-B §B3.1–B3.3)

Every container is **256 bytes**. Messages are placed in **granules**, which are mostly 20 bytes.

| Format | Payload | Other bytes | Matches link layer |
|---|---|---|---|
| **X** | 240 B (twelve 20 B granules) | 10 B link header, 6 B protocol header | UCIe 256-byte Latency Optimized mode |
| **Y** | 226 B (ten 20 B granules, one 16 B, one 10 B) | 20 B link header | CXL 256-byte latency-optimized flit |
| **Z** | 228 B (eleven 20 B granules, one 8 B) | 16 B link header, 10 B protocol header, 2 B reserved | UCIe non-latency-optimized flit (CXL.cachemem or Streaming) and CXL 256-byte non-latency-optimized flit |

- **Protocol header fields**: ChipTgtID (6 bits), NumHops (3 bits, 1–8 hops), MsgStart (12 bits, which granules start a message), ContCredit (container credits for multi-hop), ContFormat, MsgCredit (16 bits, credit grants), ChipSrcID (6 bits), ContRollover and G0IDECtrl (C2C-B §B3.2).
- **Packing rules**:
  - Messages start on granule boundaries. The spec says this "limits positions … to minimize decode logic".
  - A message may spill into the next container ("rollover"). A message spans at most two containers, a rollover sequence is at most four containers, and sequences are never interleaved (C2C-B §B3.3).
- **Which container format is used** is negotiated. If both sides support Format X, X is used. Otherwise Z, then Y (C2C-B §B14.4.3.2).
- **Format Z is required on a link with IDE** (encryption). Granule G0 is then reserved for the MAC (C2C-B §B11.2).

### Message classes and types (C2C-B §B2.2, §B5.2)

- The message classes are REQ, RSP, SNP, DAT and the C2C-specific **MISC**. MISC carries initialisation and credit grants. It is split into **MiscU** (uncredited) and **MiscC** (credited). MiscC messages are not defined in Issue B.
- A 4-bit `MsgType` names the message: ReqS/ReqL, Resp/Resp2, Snoop, DataS/DataL, WrReqDataS/WrReqDataL, WrDataExt, MiscU, MiscC.
  - The short forms (S) carry the common fields. The long forms (L) carry everything else.
  - Resp2 packs two responses into one 20-byte granule.
  - A transmitter may always use the long form, at some cost in packing efficiency (C2C-B §B5.3–B5.5).
- **Shared channel connect** puts all classes in one container stream. It "typically results in a better link efficiency" and is expected to be common. **Independent channel connect** gives "implementation ease … at the cost of potential underutilization" (C2C-B §B2.3).
- **Multiple interfaces**: there can be 1–16 interfaces between two chips. Association rules keep related messages on the same interface, for example all responses of a transaction and same-address allocating requests and snoops. The spec gives an XOR address hash as an example (C2C-B §B2.4).

### WritePush and multi-request (C2C-B §B4, §B5.6–B5.7)

- **WritePush** sends a write's request and data in one message (WrReqDataS/L), "eliminating the need for a DBIDResp". Immediate writes, write+CMO, atomics and DVM requests are "permitted, but not required" to use it. It is controlled by the `WritePush_Support` and `DVMPush_Support` properties.
- **WritePull** is the normal three-step CHI write.
- **Multi-request** (new in Issue B) carries one request for up to 64 cache lines. A WritePush multi-request adds WrDataExt messages. The maximum length is negotiated separately for WritePull, WritePush and non-write flows. A length of 2^n requests must not cross a (2^n × 64)-byte boundary (C2C-B Table B14.4).

### What does not cross a C2C link (C2C-B §B5.1)

| Not supported | Consequence stated by the spec |
|---|---|
| **DMT, DCT, DWT** (direct transfers) | ReturnNID/ReturnTxnID and FwdNID/FwdTxnID are not carried. A Home chip may still use DMT internally. At the C2C port, the data response's SrcID must be the Home's Node ID |
| **Forwarding snoops** | DCT "can be partially supported" if the Home-chip egress converts the forwarding snoop into a non-forwarding one and splits the snoop response |
| **Request Retry** | AllowRetry and PCrdType are removed. Order value 0b01 is not supported |
| **Exclusives to Non-cacheable or Device memory** | — |
| **GDI** | Its field is not transported |
| **Direct TagMatch or Persist response from Subordinate to Requester** | — |

Fields removed for other reasons:
- **Requests carry no TgtID** because requests are routed by address decode.
- **DataID is removed** because data always crosses as one 64-byte block.
- **Poison becomes RespErr = 0b10.**
- **DataCheck is removed** because "the Link layer may use its own proprietary mechanism, such as CRC and Forward Error Correction (FEC)" (C2C-B Table B5.1).

## Flow control (C2C-B ch. B8)

- **Basic rules** (§B8.1):
  - Messages must never be dropped.
  - Incoming packets from the Link or Physical layer "must be accepted without applying backpressure, in accordance with industry wide physical design standards. See UCIe".
  - RSP and DAT must be accepted without depending on REQ or SNP progress. SNP must progress without depending on REQ.
  - WritePush must not block other data.
- **Credits per message class.** The receiver grants credits through the container header (`MsgCredit`, for every class except MISC) or a `MiscU.CrdtGrant` message.
  - MiscU needs no credit.
  - A WrReqData message needs 1 REQ **and** 1 DAT credit. Resp2 needs 2 RSP credits.
  - A transmitter tracks up to 63 credits per REQ Resource Plane and up to 1023 for each other credit type (§B8.2).
- **Resource Planes (RP)**: up to eight per REQ class, with dedicated and shared credits. Messages in one RP stay in order. Different RPs must not block one another.
  - The spec's stated uses: forward-progress guarantees (e.g. PCIe posted writes), service-time guarantees (real-time traffic), and "eliminating Request retry without creating a transport deadlock".
  - Using shared credits first is recommended but not required (§B8.3).
- **DAT credit pools**: DAT0 (data that must progress past a blocked WritePush), DAT1 (WritePush that needs a forward-progress guarantee) and DATSh (shared) (§B8.4).
- **Ordered interface**: containers arrive in the order they were sent. Messages of one class and RP keep their order. This is required, so there is no property for it (§B8.6).
- **DVM**: only one DVMSync may be outstanding to remote DVM Nodes, and any number of DVMReq. A DVM Node must accept one DVMSync from each remote DVM Node (§B8.7).

## Routing (C2C-B ch. B6–B7)

- **NodeID** is 11 bits: a **ChipID** of 0–6 bits plus an **AgentID**. A chip may own several ChipIDs, which must be contiguous (§B6.1–B6.2).
- **What each message is routed by** (Table B7.1): requests by **address decode** only, responses and data by **TgtID** only, snoops by either.
  - The structures are chip address decoders (hash of 1, 2, 4, 8 or 16 ways, plus an optional 3-way), optional **Port Aggregation Group** decoders and an **ID Route Table**.
- **Snoop paths**: requests and same-address snoops must use the same port (§B7.4).
- **Multi-hop** (new in Issue B) "is required in topologies that are not fully connected" (§B7.5):
  - **Unpack**: each intermediate chip unpacks and repacks. It needs no extra credits, but "may add cycles".
  - **Pass-through**: the container is forwarded unchanged using ChipTgtID and NumHops. It needs message credits from the target chip and container credits from each intermediate chip. This "may limit the scalability", and packing may be less efficient. Routing loops can deadlock, and "Software should setup container routing paths to avoid" them (§B8.8.2).
  - A port has at most 4 Logical Links.

## DVM, interface states and properties

- **DVM** (ch. B9):
  - All CHI DVM transactions are supported. A **DVM Node (DN)** per ChipID handles them, with at most 64 in a system. Issue A allowed only one DN per chip.
  - DVMReq works like a 32-byte partial write (push or pull). DVMSync is dataless.
  - Its responses use the RSP opcodes 0x1C–0x1F and the DAT opcode 0xD, which CHI reserves for C2C (C2C-B Table B9.1–B9.2; CHI-H §B13.10.18).
- **Interface states** (ch. B12):
  - **Activation**: STOP → ACTIVATE → RUN → DEACTIVATE. Credits are implicitly returned in STOP.
  - **Coherency connect**: CohDisabled → CohConnect → CohEnabled → CohDisconnect. It is tracked separately for local Requesters and local Homes and always started from the requester side.
  - **DVM connect**: DVMDisabled → DVMConnect → DVMEnabled → DVMDisconnect.
  - Software triggers these through the `ActTrig`, `CohTrig` and `DVMTrig` register fields. Before deactivation, software must first disconnect coherency and DVM.
- **Initialisation** (ch. B13):
  - The Link layer wakes the Protocol layer. The handshake is IMPLEMENTATION DEFINED, and the spec's example uses CXS `CXSACTIVEREQ`/`CXSACTIVEACK`.
  - `MiscU.LinkStatus` reports the flit format. Then come `ActivateReq`/`ActivateAck`, an optional property exchange and finally credits.
  - Address maps, Node IDs and routing tables are set up by software, not by the hardware exchange.
- **Properties** (ch. B14):
  - There are three groups: on-chip payload, on-chip opcode/flow, and C2C-specific. Each has _Rx, _Tx or Uniform variants.
  - Levels negotiate to the highest level both sides support, and bit vectors to the AND of both.
  - If the local side can send something the remote side cannot receive, the transmitter "must terminate or downgrade" it. The spec's examples are SnpUniqueStash → SnpUnique, and doing atomics locally.

## Security (C2C-B ch. B10–B11)

- **RME-DA / RME-CDA**:
  - The host is the trusted computing base.
  - A device works only in Realm and Non-secure PAS and must not connect directly to another device.
  - A device interface may have at most 16 Request Nodes, of which at most 8 are caching (IDs 0–7). The host must track device caching precisely. The cap exists "to manage the increase in the size of a fine grain tracking snoop filter" (§B10.4).
- **IDE**:
  - Encryption and integrity are done by engines in the Link layer, which is outside the spec's scope.
  - They apply over a **single hop** only. A MAC covers an "IDE epoch" of containers.
  - Decrypted containers are released only after the MAC checks out ("containment mode") (§B11.1).

## Hooks for C2C inside the CHI spec (CHI-H)

The base CHI spec contains several features that exist mainly for chip-to-chip links:
- **Reserved opcodes**: RSP opcodes 0x1C–0x1F and DAT opcode 0xD are "reserved for C2C use" (CHI-H §B13.10.18). C2C-B uses them for the DVM responses above.
- **Multi-request** (Issue H) packs up to 64 cache lines into one request. One of its stated motivations is better efficiency on CHI C2C links (CHI-H §B2.6). C2C-B says it permits multi-requests to "optimize link bandwidth utilization" (§B4).
- **PrefetchTgtHint** tells a C2C receiver that the original read had a PrefetchTgt. If that PrefetchTgt was dropped at the link transmitter, the receiver can re-create it (CHI-H §B13.10.57).
- **DataSource.CompleterDistance** is incremented by the die-to-die or socket-to-socket transmitter, so a requester can tell local data from remote data (CHI-H §B11.2.7.2).
- **RME Device Assignment** (RME-DA / RME-CDA) is "expected" to be used with chip(let)-to-chip(let) links. A host checks every request and snoop from an attached device (CHI-H §B10.7).

## What Issue B added

C2C-B Table C1.2 lists these as new since Issue A.b:
- Format Z
- Request Resource Plane mapping
- software-visible registers (ch. B15)
- NodeID management
- `CohTrig`/`DVMTrig`
- PortID hardware exchange
- more properties, and support for multiple `MiscU.Properties` messages
- the Event message
- multi-hop routing
- multi-request
- IDE
- the hub-and-spoke topology

Property exchange and WritePush already existed in Issue A: their properties are marked "Issue introduced: A" in Tables B14.1–B14.9.

## Where CXS fits

The IP that implements C2C packetisation and the chosen transport "are typically connected on-chip using the AMBA **CXS** protocol" (G-SYS §4.4.1). C2C-B uses a CXS activation handshake as its example of Link-to-Protocol wake-up (§B13.2). CXS is a credited packet stream; see [Streaming interfaces](streaming-interfaces.md).

## Where the sources agree

- C2C reuses CHI end-to-end to **avoid protocol conversion**, giving a common memory and security model across dies (G-SYS §4.4.1; C2C-B §B1.1).
- C2C defines the Protocol and Packetization layers only. Link and Physical layers come from the transport, for example UCIe or a PCIe physical layer (C2C-B §B2.1; G-SYS §4.4.1).
- The CHI reserved-for-C2C opcodes (CHI-H §B13.10.18) are exactly the ones C2C-B uses for DVM responses (C2C-B Table B9.1–B9.2).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| How C2C IP connects on-chip | G-SYS §4.4.1: "typically connected on-chip using … CXS" | C2C-B §B2.1: the Packetization layer may connect "directly to the external signals" if no Link layer is present. §B13.2 calls the wake-up handshake IMPLEMENTATION DEFINED, with CXS only as an example | G-SYS describes a typical product split. The spec allows other arrangements |
| What CXS is for | CXS-D §1.2: "The primary use case … is to transport packets between an on-chip interconnect and PCIe controller" (CCIX and CXL packets) | G-SYS §4.4.1: the CHI C2C transport attachment | Both are valid. CXS-D §1.1 allows "any point-to-point packetized communication", and C2C is one such use |
| How many DVM Nodes a chip may have | C2C Issue A: at most one per chip (noted in C2C-B §B9.2.1) | C2C-B §B9.2.1: one or more, each with its own ChipID | Changed in Issue B. Older Issue-A designs assume a single DN |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Choose the container format that your link layer's flit format allows. C2C-B Table B14.11 maps the Link-layer header size (6, 20 or 16 bytes) to the compatible formats X, Y and Z. Hardware negotiation then picks X first, then Z, then Y (§B14.4.3.2).
- Never apply back-pressure on the receive side of a C2C link (C2C-B §B8.1). Receive buffering has to cover every credit you grant. *Editor's note (not from the sources): this follows from the credit rules in §B8.2, but the spec does not state it as a sizing rule.*
- If an on-chip feature is not negotiated, for example stashing or atomics, the transmitter must downgrade or terminate it before the link (C2C-B §B14.1).
- At the port facing a Subordinate Node, copy SrcID→ReturnNID and TxnID→ReturnTxnID, and set DoDWT = 0 (C2C-B §B5.1.3).

## Related articles

- [CHI architecture](chi-architecture.md)
- [Streaming interfaces](streaming-interfaces.md) (CXS)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [DVM and address translation](dvm-and-address-translation.md)
- [Protection and security](protection-and-security.md) (RME-DA)

## Sources

C2C-B (read in full; the ch. B15 register field tables were scanned only), CHI-H, CXS-D, G-SYS. See [Source key](sources.md).
