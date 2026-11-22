# Terminology and roles: who starts a transaction, who answers

> Every AMBA protocol has a side that *asks* and a side that *answers*. The names for those sides changed over the years and differ between protocols. This page is your translation table.

## In plain words

A **transaction** is one complete conversation, for example "read 64 bytes from address 0x8000". The block that **starts** it is the initiator; the block that **completes** it is the responder. Older Arm documents called them *master* and *slave*. Newer documents use more neutral words, and the words chosen depend on the protocol's shape:

- Memory-mapped buses (AHB, AXI): **Manager** and **Subordinate**.
- APB and CHI: **Requester** and **Completer**.
- One-way streams (AXI-Stream, ATB, CXS): **Transmitter** and **Receiver**.
- DTI and LTI mix the two: the interface ends are **Manager** (TBU or PCIe Root Port for DTI, IO device for LTI) and **Subordinate** (TCU for DTI, TBU for LTI). LTI calls each channel's sender and receiver TX and RX, and DTI names message directions *downstream* and *upstream* (DTI-J §B1.2, §B2.1.2; LTI-E §B2.1).

## Translation table

| Generic role | Old name | AHB5 / AXI (current) | APB5 | CHI | Stream protocols |
|---|---|---|---|---|---|
| Starts transactions | master | **Manager** (AHB-C, AXI-J+) | **Requester** (APB bridge) (APB-D/E §1.1) | **Requester**, typically a Request Node, RN (CHI-H §B1.3) | **Transmitter** (AXIS-B §1.1, ATB-C §1.1, CXS-D) |
| Answers transactions | slave | **Subordinate** | **Completer** (the peripheral) | **Completer**: a Home Node, Subordinate Node or MN (CHI-H §B1.3; G-CHI §3) | **Receiver** |
| Sits in between | interconnect / bus fabric | Interconnect (looks like a Subordinate on one side and a Manager on the other) (AXI-L §A1.2.1) | APB bridge (it is a Completer on AHB/AXI and the Requester on APB) | Interconnect containing HN-F, HN-I, MN | Interconnect / funnel / replicator |

## Words for the size of a piece of work

| Term | Meaning | Where defined |
|---|---|---|
| **Transfer** (AXI) | One cycle of communication on one channel, a single VALID/READY handshake | AXI-L §A1.3.2 |
| **Beat** | One transfer inside a burst. An AHB INCR4 burst has four beats | AHB-C glossary |
| **Burst** | A group of beats to consecutive (or wrapping) addresses, described by a single address | AHB-C §3.6; AXI-L §A3.1 |
| **Transaction** | Everything needed to complete one request: the request, the data transfers and the response(s) | AXI-L §A1.3.2; CHI-H §B1.3 |
| **Message** (CHI) | A protocol-layer unit such as a Request, Data response or Snoop | CHI-H §B1.3 |
| **Packet** (CHI) | A unit routed across the interconnect. In CHI every packet is one flit | CHI-H §B1.3 |
| **Flit** (CHI, CXS, C2C) | *FLow control unIT*, the smallest unit that consumes a credit | CHI-H §B1.3 |
| **Phit** (CHI) | One physical transfer between neighbours. In CHI every flit is one phit | CHI-H §B1.3 |
| **Packet / frame** (AXI-Stream) | A packet is a group of bytes ending in TLAST. A frame is a whole number of packets | AXIS-B §1.1 |
| **Container** (C2C) | A fixed 256-byte unit carrying several CHI messages across a chip-to-chip link | C2C-B §B3.1 |

## Words for direction and position

- **Upstream / downstream**: relative positions on a transaction's path. Downstream is towards the memory or endpoint (AXI-L §A1.3.1; CHI-H §B1.3).
- **Endpoint / final destination**: where the data really lives. Some memory types require the response to come from the final destination (see [Memory types and cache attributes](memory-types-and-cache-attributes.md)).
- **Memory Subordinate vs Peripheral Subordinate** (AXI): a Memory Subordinate must handle all transaction types correctly. A Peripheral Subordinate only has to handle the access methods listed in its datasheet, but it must still respond in a protocol-compliant way to anything else (AXI-L §A4.1).

## Where the sources agree

- There are always exactly **two interface types per link**, an asking side and an answering side. In AXI the two interface types are "symmetrical", and every connection is Manager↔Subordinate (G-AXI §3; AXI-L §A1.2.1).
- An interconnect is described as a component with Subordinate ports facing the Managers and Manager ports facing the Subordinates (AXI-L §A1.2.1; AHB-C §1.1.3).

## Where the sources disagree (and why)

| Point | Source A | Source B | Why |
|---|---|---|---|
| Name of the asking side | AHB-C (2021) and AXI-J+ (2023) use **Manager** | APB-D/E (2021/2023) use **Requester**; CHI-H uses **Requester** | Arm "regularized" terminology per protocol family. APB and CHI chose Requester/Completer, AHB/AXI chose Manager/Subordinate (APB-D revision table; AHB-C Table B-3) |
| Name of the answering side in CHI | G-CHI §1: "Requester is synonymous with master … **Subordinate** is synonymous with slave" | CHI-H §B1.3 and G-CHI §3 also define **Completer** as "a component that responds to a transaction" | In CHI, *Completer* is the role and *Subordinate Node (SN)* is a node type. The guide mixes the two vocabularies in one sentence |
| Old terms still in use | ATP-A (2019), AMBA2 (1999), AXI-Hc's AXI3 text and AXIS-A use **master/slave** | Current specs replaced them | Documents not re-issued since about 2020 keep the old words. *ATP master* = Manager |
| AXI-Stream sides | G-AXI §2: AXI4-Stream transfers data "from manager to subordinate" | AXIS-B §1.1: "connecting a single **Transmitter** and a single **Receiver**" | *Editor's note (not from the sources):* The guide reuses AXI vocabulary loosely. The stream spec uses stream vocabulary because there is no request/response |
| Is AXI a "bus"? | AHB-C glossary: AXI is "an AMBA **bus** protocol" | G-AXI §3: AXI is a **point-to-point** interface specification, "rather than the interconnect" | Informal versus precise use of "bus". AXI defines one link between two interfaces, and the fabric is up to the implementer |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Name your ports by role and protocol, for example `m_axi_*` (Manager side of an AXI link) and `s_apb_*` (Completer side), and say in a comment which vocabulary you use.
- When you read an older IP datasheet that says "slave error", map it to SLVERR or PSLVERR. The *signal names* (PSLVERR, SLVERR) kept the old word even after the prose changed (APB-E §2.1; AXI-L §A3.3).

## Related articles

- [AMBA overview](amba-overview.md)
- [Interconnect, topology and bridges](interconnect-topology-and-bridges.md)
- [CHI architecture](chi-architecture.md) (node types RN-F, HN-F, SN-F…)

## Sources

AMBA2, APB-D, APB-E, AHB-C, AXI-Hc, AXI-L, AXIS-A, AXIS-B, ATB-C, CXS-D, CHI-H, C2C-B, ATP-A, G-AXI, G-CHI. See [Source key](sources.md).
