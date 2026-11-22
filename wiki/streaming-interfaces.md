# Streaming interfaces: AXI-Stream, ATB and CXS

> Point-to-point protocols that move a **stream** of data in one direction with no addresses: AXI-Stream (general data), ATB (trace) and CXS (credited packets, for example PCIe/CXL or chip-to-chip).

## In plain words

Memory-mapped buses ask "read or write *what address*?". A stream doesn't: it just says "here is the next piece". Think of a conveyor belt. You still need to know:
- **when** an item moves (handshake or credits),
- **where a packet ends** (TLAST, CXS END pointers),
- **which bytes are real** (TKEEP/TSTRB, ATBYTES),
- **which stream or destination** it belongs to (TID/TDEST, ATID, CXSSRCID/TGTID).

## AXI-Stream (AXIS-B)

**Signals**: `TVALID`, `TREADY`, `TDATA`, `TSTRB`, `TKEEP`, `TLAST`, `TID`, `TDEST`, `TUSER`, and in AXI5-Stream also `TWAKEUP` plus parity (AXIS-B §2.1).

**Byte types** (AXIS-B §1.1, §2.4–2.5):

| TKEEP | TSTRB | Byte type | Meaning |
|---|---|---|---|
| 1 | 1 | Data byte | Must reach the destination unchanged and in position |
| 1 | 0 | Position byte | A placeholder that keeps relative position (for partial updates). The data value is irrelevant |
| 0 | 0 | Null byte | No information. It may be added or removed anywhere |
| 0 | 1 | Reserved | Must not be used |

**Stream shapes**: byte stream, continuous aligned, continuous unaligned, sparse (AXIS-B §1.2).

**Rules worth remembering**:
- Low-order bytes are **earlier** in the stream (AXIS-B §2.4.2).
- `TLAST` marks the end of a packet. The number of packets (TLAST count) must be preserved. A zero-byte TLAST transfer is legal and flushes buffers (AXIS-B §2.6).
- Streams are identified by (TID, TDEST). Interleaving between streams is allowed **per transfer**, while merging across streams or across a TLAST is not (AXIS-B §2.6–2.7).
- Width conversion (up/downsizing, merging, packing) must preserve data and position bytes, and may add or remove null bytes (AXIS-B §2.4).
- TUSER is defined **per byte** (`TUSER[x*m+m-1 : x*m]`). Pad or trim per byte when widths differ (AXIS-B §2.9).
- Optional signals and defaults: TREADY default HIGH. TKEEP absent means all ones. TSTRB absent means TSTRB = TKEEP (AXIS-B §3.1).

## ATB: Advanced Trace Bus (ATB-C)

Covered in detail in [Debug trace (ATB)](debug-trace-atb.md). As a stream it has:
- `ATVALID`/`ATREADY` handshake, `ATDATA` (a power of two, ≥ 8 bits), `ATBYTES` (number of valid bytes − 1) and `ATID` (7-bit source ID) (ATB-C ch. 2–3).
- **Strict byte order across all IDs** (ATB-C §4.1).

## CXS: Credited eXtensible Stream (CXS-D)

- Purpose: "transport packets between an on-chip interconnect and PCIe controller". Figure 1-1 shows CCIX and CXL packets over CXS to PCIe (CXS-D §1.2). CXS is "specifically optimized for wide interfaces", so several packets can be merged into one transfer (CXS-D §1.1). It is also used between the CHI C2C packetiser and its transport (G-SYS §4.4.1).
- **Credits**, not READY: `CXSCRDGNT` grants one credit per cycle and `CXSVALID` uses one. An optional `CXSCRDRTN` returns credits unused (CXS-D §2.1.2).
- **Flits carry packets**: `CXSDATA` is 8–2048 bits (a multiple of 8), and it must be 256, 512, 1024 or 2048 bits when more than one packet fits in a flit. `CXSCNTL` holds START/END flags and pointers for up to 4 packets per flit (`CXSMAXPKTPERFLIT`). Packets start on 16- or 4-byte boundaries and end on 4-byte boundaries (CXS-D §4.1–4.3).
- **CXS-Lite**: `CXSMAXPKTPERFLIT = 1`, so one flit = one packet occupying all bytes (CXS-D §2.2).
- Options: `CXSLAST` (contiguous packets), `CXSPRCLTYPE` (protocol multiplexing), `CXSSRCID`/`CXSTGTID` (multi-node), `CXSUSER`, odd-byte parity, and link activation (`CXSACTIVEREQ`/`ACK`, `CXSDEACTHINT`) (CXS-D §2.3–2.6, §3).

## Comparison

| | AXI-Stream | ATB | CXS |
|---|---|---|---|
| Flow control | TVALID/TREADY | ATVALID/ATREADY | Credits |
| End of packet | TLAST | (none, trace is a continuous byte stream) | END bits and pointers in CXSCNTL |
| Byte qualifiers | TKEEP, TSTRB | ATBYTES (contiguous low bytes) | Packet pointers |
| Stream ID | TID, TDEST | ATID | CXSSRCID, CXSTGTID, CXSPRCLTYPE |
| Reordering | Not supported (interleave by stream) | None, even across IDs | Same stream stays in order |
| Extras | TUSER, TWAKEUP | Flush (AFVALID/AFREADY), SYNCREQ, triggers | Link activation, credit return |

AXIS-B Appendix A says AXI-Stream "has many similarities to an AXI write data channel" and lists the key differences:
- the AXI W channel does not permit interleaving;
- AXI-Stream has no defined or maximum burst or packet length;
- its data width can be any whole number of bytes;
- it has TID/TDEST for source and destination;
- it defines TUSER manipulation more precisely;
- it has TKEEP for inserting and removing null bytes.

AXIS-B §2.6 also says "An AXI-Stream packet is similar to an AXI burst".

## Where the sources agree

- All three are **point-to-point**, unidirectional and data-agnostic ("This specification describes how data is transferred but does not describe the meaning of the data": AXIS-B §1.1. "Data-agnostic": ATB-C §1.2. CXS packet length encoding is "outside the scope": CXS-D §2.2).
- Parity protection uses the same **odd byte parity** scheme as the other AMBA 5 interfaces (AXIS-B ch. 5; CXS-D §3.2).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Who the AXI-Stream sides are | G-AXI §2: AXI4-Stream transfers data "from **manager to subordinate**" | AXIS-B §1.1: a single **Transmitter** and a single **Receiver** | The guide uses memory-mapped words. The spec uses stream words. Same meaning |
| What CXS is for | CXS-B/CXS-D §1.2: "The primary use case for a CXS interface is to transport packets between an on-chip interconnect and PCIe controller" (CCIX/CXL) | G-SYS §4.4.1 (2025): CXS connects the **CHI C2C** packetiser to its transport (UCIe or PCIe PHY). C2C-B §B13.2 uses CXS as its example wake-up handshake | Both are true. CXS-D still names PCIe as the *primary* use, while CXS-D §1.1 allows "any point-to-point packetized communication". C2C is one such use |
| CXS credit limit | CXS-B Table 2-2: `CXS_MAX_CREDIT` **1–15** | CXS-D Table 2-2: **1–63** | Changed in **Issue C** (CXS-D Table A1-3), with no reason given. *Editor's note: more credits cover longer credit loops (CXS-D §2.1.2)* |
| Is AXI-Stream "ideal for FPGAs"? | G-AXI §2: AXI4-Stream has "reduced signal routing, which is ideal for implementation in FPGAs" | AXIS-B makes no statement about implementation technology. DTI-J ch. B5 uses AXI5-Stream as its example transport for SMMU messages | Not a protocol rule. The guide's remark is an opinion about suitability, and the spec neither supports nor contradicts it |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- If your Receiver can't handle null bytes, say so and leave out TKEEP. Any interconnect that **inserts** null bytes must remove them before such a Receiver (AXIS-B §2.4.3).
- Don't merge AXI-Stream transfers across a TLAST or across different TID/TDEST (AXIS-B §2.4).
- In CXS, a Receiver must guarantee buffer space for every credit it has granted (CXS-D §2.1.2).

## Related articles

- [Debug trace (ATB)](debug-trace-atb.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Chiplets and chip-to-chip](chiplets-and-chip-to-chip.md)
- [DVM and address translation](dvm-and-address-translation.md) (DTI over AXI5-Stream)
- [Interface properties and user signals](interface-properties-and-user-signals.md)

## Sources

AXIS-A, AXIS-B, ATB-C, CXS-B, CXS-D, DTI-J, G-AXI, G-SYS. See [Source key](sources.md).
