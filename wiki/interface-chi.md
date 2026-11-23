# CHI interface hub

> Everything about one CHI interface on one page: which channels each node type has, every link-layer signal, the flit formats, the link-activation, SACTIVE and SYSCO handshakes, the rules a design must follow, and protocol assertions. Each line links to the concept article that explains it in depth. This page summarises; it does not replace [CHI: Coherent Hub Interface](chi-architecture.md).

## In plain words

A CHI interface is a set of **links**. Each link is one Transmitter sending **flits** to one Receiver, and two-way communication needs a pair of links (CHI-H §B13.2). A link carries up to four **channels**: REQ (requests), RSP (responses without data), SNP (snoops) and DAT (data) (CHI-H §B13.4). There is no VALID/READY: the Receiver hands out **L-Credits**, and the Transmitter spends one per flit (CHI-H §B14.2). Before flits can flow, each direction is switched on with a four-phase **LINKACTIVEREQ/LINKACTIVEACK** handshake, and before it is switched off every credit must come back (CHI-H §B14.5). Two more handshakes sit beside the links: **SACTIVE** ("transactions in progress") and, for coherent Request Nodes, **SYSCOREQ/SYSCOACK** (joining and leaving the coherency domain) (CHI-H §B14.7, ch. B15).

## Channels per node type

From CHI-H Table B13.1. Signal names take a `TX` or `RX` prefix seen from the node, for example `TXREQFLITV`. The interconnect has the mirror-image interface.

| Channel | Carries | Request Node | Subordinate Node |
|---|---|---|---|
| REQ | All requests | TXREQ | RXREQ |
| RSP | Responses from the Completer; snoop responses and completion acknowledge | RXRSP, TXRSP | TXRSP |
| SNP | Snoop and SnpDVMOp requests | RXSNP | — |
| DAT | Write data and snoop response data from a Request Node; read data | TXDAT, RXDAT | RXDAT, TXDAT |

An RN-I "uses all channels, with the exception of the SNP channel" (CHI-H §B13.6.1.3). See [CHI: Nodes](chi-architecture.md#nodes-chi-h-b16-g-chi-3).

## Signals

### Per channel

From CHI-H Tables B13.2–B13.5. `<CH>` is REQ, RSP, SNP or DAT.

| Signal | Driven by | Width | Present | Meaning | Explained in |
|---|---|---|---|---|---|
| `<CH>FLITPEND` | Transmitter | 1 | Always | "Early indication that a … flit could be transmitted in the following cycle" | [Low power: clock gating hints](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| `<CH>FLITV` | Transmitter | 1 | Always | The flit on `<CH>FLIT` is valid | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| `<CH>FLIT` | Transmitter | per flit format | Always | The flit (see [Flit formats](#flit-formats)) | [CHI: Channels and identifiers](chi-architecture.md#channels-and-identifiers) |
| `<CH>LCRDV` | Receiver | 1, or `Num_RP_<CH>` bits on REQ/SNP | Always | Grants one L-Credit (one per Resource Plane per cycle) | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| `REQFLITRP`, `SNPFLITRP` | Transmitter | `clog2(Num_RP_<CH>)` | `Num_RP_<CH> > 1` | Resource Plane of the flit | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| `REQSHAREDCRD`, `SNPSHAREDCRD` | Transmitter | 1 | `Shared_Credits_<CH> == True` | The flit uses a shared credit | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| `REQLCRDSHV`, `SNPLCRDSHV` | Receiver | 1 | `Shared_Credits_<CH> == True` | Grants one shared L-Credit | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |

Resource Planes and shared credits exist only on REQ and SNP (CHI-H §B14.2.1.2).

### Per interface

| Signal | Driven by | Meaning | Source | Explained in |
|---|---|---|---|---|
| `TXLINKACTIVEREQ`, `TXLINKACTIVEACK` | Node (REQ) / interconnect (ACK) | Activation handshake for all the node's transmit channels | CHI-H §B14.5 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| `RXLINKACTIVEREQ`, `RXLINKACTIVEACK` | Interconnect (REQ) / node (ACK) | Activation handshake for all the node's receive channels | CHI-H §B14.5 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| `TXSACTIVE` | Node | "there is a transaction either in progress or about to start" | CHI-H §B14.7.1 | [CHI: Link-level behaviour](chi-architecture.md#link-level-behaviour-chi-h-ch-b13b15) |
| `RXSACTIVE` | Other side | The other side has ongoing Protocol layer activity | CHI-H §B14.7.1 | [CHI: Link-level behaviour](chi-architecture.md#link-level-behaviour-chi-h-ch-b13b15) |
| `SYSCOREQ` | RN-F or RN-D | Request to join (HIGH) or leave (LOW) system coherency | CHI-H §B15.1 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| `SYSCOACK` | Interconnect | Coherency enabled (HIGH) or disabled (LOW) | CHI-H §B15.1 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |

Clock and reset are generic (`CLK`, `RESETn`): "This specification does not define a specific clocking microarchitecture" (CHI-H §B14.1.1).

### Properties that shape the interface

The widths of the flits depend on these properties (CHI-H §B16.1): `NodeID_Width` (7 to 16 bits for SrcID, TgtID and the other node IDs), `Req_Addr_Width`, `Data_Width` (128, 256 or 512), `Num_RP_REQ` and `Num_RP_SNP`, `Shared_Credits_REQ` and `Shared_Credits_SNP`, `Data_Check` and `Data_Poison`, `Check_Type` (interface parity), `MPAM_Support`, `MEC_Support`, `PBHA_Support`, and `Req_RSVDC_Width` / `Dat_RSVDC_Width` (user fields). See [Interface properties](interface-properties-and-user-signals.md).

## Flit formats

All four flit formats start with `QoS`, then node IDs and `TxnID` (CHI-H §B13.9). The main fields of each flit:

| Flit | Main fields | Source |
|---|---|---|
| Request (REQFLIT) | QoS, TgtID, SrcID, TxnID, ReturnNID/StashNID, ReturnTxnID, Opcode, MultiReq/NumReq, Size, Addr, PAS, LikelyShared, AllowRetry, Order, PCrdType, MemAttr, SnpAttr, DoDWT, LPID/PGroupID/StashGroupID/TagGroupID, Excl, SnoopMe, CAH, ExpCompAck, TagOp, TraceTag, then optional MPAM, PBHA, MECID, StreamID, SecSID1, RSVDC | CHI-H Table B13.6 |
| Response (RSPFLIT) | QoS, TgtID, SrcID, TxnID, Opcode, RespErr, Resp, FwdState/DataPull, CBusy, DBID/PGroupID/StashGroupID/TagGroupID, PCrdType, TagOp, TraceTag, CacheLineID | CHI-H Table B13.7 |
| Snoop (SNPFLIT) | QoS, SrcID, TxnID, FwdNID, FwdTxnID/StashLPID/VMIDExt, Opcode, Addr, PAS, DoNotGoToSD, RetToSrc, TraceTag, then optional MPAM, MECID. **No TgtID** | CHI-H Table B13.8 |
| Data (DATFLIT) | QoS, TgtID, SrcID, TxnID, HomeNID, Opcode, RespErr, Resp, DataSource/FwdState/DataPull, CBusy, DBID, CCID, DataID, CacheLineID, TagOp, Tag, TU, TraceTag, CAH, NumDat, Replicate, RSVDC, BE, Data, DataCheck, Poison | CHI-H Table B13.9 |

Several fields share bits depending on the message, and exact bit positions depend on the properties. Use the table for your issue and configuration (see [CHI: RTL tips](chi-architecture.md#rtl-tips)). DataCheck is 0 bits or Data/8 bits wide, and Poison is 0 bits or Data/64 bits wide (CHI-H §B13.9.4).

## Key rules checklist

| # | Rule | Source | Explained in |
|---|---|---|---|
| 1 | During reset, TX\*\*\*LCRDV, TX\*\*\*FLITV, TXLINKACTIVEREQ and RXLINKACTIVEACK are LOW. They may first go HIGH at a rising edge after RESETn is HIGH | CHI-H §B14.1.3 | [CHI RTL tips](chi-architecture.md#rtl-tips) |
| 2 | Every flit consumes one L-Credit. A Receiver provides 1 to 15 credits per channel, and must be able to accept every flit it has credited. "An L-Credit cannot be used in the same cycle as being received" | CHI-H §B14.2.1.1 | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| 3 | With Resource Planes: credits are per RP (at most 15 outstanding each, plus at most 15 shared); one RP sends per cycle; FLITV only with a dedicated credit for that RP or a shared one; `SHAREDCRD` says which | CHI-H §B14.2.1.2 | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| 4 | FLITPEND is asserted exactly one cycle before a flit. FLITPEND LOW means no flit in the next cycle. It may stay HIGH permanently, and may be HIGH without a credit | CHI-H §B14.4 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| 5 | Link states from (REQ, ACK): STOP 00, ACTIVATE 10, RUN 11, DEACTIVATE 01. No flits in STOP or ACTIVATE; no credits in STOP or ACTIVATE, though ACK and a first credit may come in the same cycle | CHI-H §B14.5.1, Tables B14.1–B14.3 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| 6 | The Receiver stays in RUN until it sees LINKACTIVEREQ deasserted. In DEACTIVATE the Transmitter returns every credit, normally with LCrdReturn link flits, and "The Receiver must wait for all credits to be returned before deasserting LINKACTIVEACK" | CHI-H §B14.5.1, Table B14.2 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| 7 | The Transmitter starts each change between STOP and RUN; each direction has its own handshake, and the two directions interact as described in B14.6 | CHI-H §B14.5.1.2, §B14.6 | [Low power](low-power-and-wakeup.md) |
| 8 | TXSACTIVE goes HIGH before or with the first flit of a transaction and stays HIGH until after the last flit. A component that asserts it must also start link activation. Only an interconnect interface may derive TXSACTIVE from RXSACTIVE | CHI-H §B14.7.1–§B14.7.2 | [CHI: Link-level behaviour](chi-architecture.md#link-level-behaviour-chi-h-ch-b13b15) |
| 9 | SYSCOREQ/SYSCOACK is four-phase: SYSCOREQ changes only when SYSCOACK equals it, and SYSCOACK changes only when it differs. A Request Node may not issue transactions that let a coherent location be cached until SYSCOACK is HIGH | CHI-H §B15.2, §B15.2.1 | [Low power](low-power-and-wakeup.md) |
| 10 | Channel dependencies: a Request Node makes progress on inbound RSP and DAT without depending on any other channel, and on inbound SNP without needing outbound REQ | CHI-H §B13.4.1 | [Handshakes](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| 11 | Bandwidth can be raised with multiple interfaces or replicated channels | CHI-H §B13.7 | [CHI: Performance features](chi-architecture.md#performance-features) |

## Protocol assertions

SystemVerilog assertions for rules 1, 2, 4–6, 8 and 9, for one channel of one link direction without Resource Planes. They come from `assertions/chi_checker.sv` in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository, which also has a test for every assertion. There are three modules:

- `chi_link_checker`: instantiate once per channel and direction. Connect the channel's `FLITPEND`, `FLITV` and `LCRDV`, and that direction's `LINKACTIVEREQ`/`ACK`.
- `chi_sysco_checker`: the SYSCOREQ/SYSCOACK handshake.
- `chi_sactive_checker`: TXSACTIVE against a Request Node's TXREQFLITV.

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.** Treat these as reviewed drafts until `python assertions/run_tests.py chi` passes.

| Assertion | Rule | Source |
|---|---|---|
| `chi_reset_quiet` | FLITV, LCRDV, LINKACTIVEREQ and LINKACTIVEACK LOW during reset | CHI-H §B14.1.3 |
| `chi_flitpend_before_flit` | Every flit is preceded by FLITPEND in the previous cycle | CHI-H §B14.4 |
| `chi_flit_needs_credit` | No flit without a credit held from an earlier cycle | CHI-H §B14.2, §B14.2.1.1 |
| `chi_credit_max` | At most 15 credits outstanding | CHI-H §B14.2.1.1 |
| `chi_no_flit_when_stopped` | No flits in STOP or ACTIVATE | CHI-H Table B14.3 |
| `chi_no_credit_when_stopped` | No credits in STOP or ACTIVATE | CHI-H Table B14.3 |
| `chi_ack_rise_needs_req` | LINKACTIVEACK rises only while LINKACTIVEREQ is HIGH | CHI-H §B14.5, Table B14.1 |
| `chi_ack_fall_needs_noreq` | LINKACTIVEACK falls only after LINKACTIVEREQ is LOW | CHI-H Table B14.2 |
| `chi_credits_returned_before_stop` | All credits returned before LINKACTIVEACK falls | CHI-H Table B14.2 |
| `chi_sysco_req_change`, `chi_sysco_ack_change` | Four-phase SYSCOREQ/SYSCOACK handshake | CHI-H §B15.2 |
| `chi_txsactive_with_req` | TXSACTIVE HIGH whenever TXREQFLITV is HIGH in RUN | CHI-H §B14.7.2.1 |

```systemverilog
// Credits held by the Transmitter: a credit received at an edge counts from
// the next edge ("An L-Credit cannot be used in the same cycle as being received").
always_ff @(posedge CLK)
  if (!RESETn) credits <= '0;
  else         credits <= credits + 6'(LCRDV) - 6'(FLITV);

// CHI-H §B14.4: FLITPEND is asserted exactly one cycle before a flit
chi_flitpend_before_flit: assert property (@(posedge CLK) disable iff (!RESETn)
    FLITV |-> $past(FLITPEND));

// CHI-H §B14.2: a flit needs an L-Credit; §B14.2.1.1: at most 15 credits
chi_flit_needs_credit: assert property (@(posedge CLK) disable iff (!RESETn)
    FLITV |-> (credits > 0));
chi_credit_max: assert property (@(posedge CLK) disable iff (!RESETn)
    credits <= MAX_CREDITS);

// CHI-H Table B14.3: no flits and no credits in STOP or ACTIVATE (LINKACTIVEACK LOW)
chi_no_flit_when_stopped: assert property (@(posedge CLK) disable iff (!RESETn)
    FLITV |-> LINKACTIVEACK);
chi_no_credit_when_stopped: assert property (@(posedge CLK) disable iff (!RESETn)
    LCRDV |-> LINKACTIVEACK);

// CHI-H Table B14.2: the Receiver waits for all credits before deasserting LINKACTIVEACK
chi_credits_returned_before_stop: assert property (@(posedge CLK) disable iff (!RESETn)
    (!LINKACTIVEACK && $past(LINKACTIVEACK)) |-> (credits == 0));

// CHI-H §B15.2: SYSCOREQ changes only when SYSCOACK equals it, SYSCOACK only when it differs
chi_sysco_req_change: assert property (@(posedge CLK) disable iff (!RESETn)
    (SYSCOREQ != $past(SYSCOREQ)) |-> ($past(SYSCOREQ) == $past(SYSCOACK)));
chi_sysco_ack_change: assert property (@(posedge CLK) disable iff (!RESETn)
    (SYSCOACK != $past(SYSCOACK)) |-> ($past(SYSCOREQ) != $past(SYSCOACK)));
```

*Editor's notes (not from the sources):*
- *`chi_ack_rise_needs_req` reads the "four-phase" handshake and the four states of Table B14.1 as saying that ACK only rises from ACTIVATE. Figure B14.7 marks some other transitions as permitted when signals race; those are not modelled.*
- *`chi_txsactive_with_req` skips flits sent while TXLINKACTIVEREQ is LOW, because B14.7.2 permits TXSACTIVE to be LOW while link flits are sent during deactivation.*
- *Every flit, including LCrdReturn, counts as using a credit, following "Each transfer of a flit from the Transmitter to the Receiver consumes one L-Credit" (CHI-H §B14.2.1.1).*

Not covered: Resource Planes and shared credits, flit contents, protocol-level rules (transaction flows, retry, ordering), the combined Tx/Rx state machine of B14.6, and the SYSCO rules that depend on outstanding transactions.

## Versions

Link-layer changes across issues include wider NodeIDs (up to 16 bits in Issue H), multiple interfaces and replicated channels (Issue E), and Resource Planes with shared credits plus optional Retry (Issue H). See [CHI: Issues of CHI](chi-architecture.md#issues-of-chi) for the full table.

## Related articles

- [CHI: Coherent Hub Interface](chi-architecture.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Low power and wake-up](low-power-and-wakeup.md)
- [Cache coherency fundamentals](cache-coherency-fundamentals.md)
- [Networks-on-chip](networks-on-chip.md)
- [Chiplets and chip-to-chip](chiplets-and-chip-to-chip.md)
- [AXI interface hub](interface-axi.md)

## Sources

CHI-H (§B13.2–§B13.9, ch. B14, ch. B15, §B16.1). See [Source key](sources.md).
