# CXS interface hub

> Everything about one CXS link on one page: every signal with the property that enables it, the properties that shape the link, the credit and link-control rules, and protocol assertions. Each line links to the concept article that explains it in depth. This page summarises; it does not replace [Streaming interfaces](streaming-interfaces.md#cxs-credited-extensible-stream-cxs-d).

## In plain words

CXS streams packets of another protocol, typically CHI, across a link, for example to another chip. "A single instance of the interface has one Transmitter (TX) connected to one Receiver (RX). The data is sent in one direction. The data that is transferred in one cycle is known as a flit." (CXS-D §2.1.) Flow control uses credits: the Receiver grants one credit per cycle with `CXSCRDGNT`, and each flit uses one. With link control enabled, the link is switched on and off with `CXSACTIVEREQ`/`CXSACTIVEACK`, and spare credits go back with `CXSCRDRTN` (CXS-D §2.1.2, ch. 5). See [Chiplets: where CXS fits](chiplets-and-chip-to-chip.md#where-cxs-fits).

## Signals

From CXS-D Tables 2-1 and 3-1. Port names may add TX or RX after "CXS", for example `CXSTXVALID` (CXS-D §2.1.2).

| Signal | Direction | Width | Present | Meaning | Explained in |
|---|---|---|---|---|---|
| `CLK`, `RESETn` | External | 1 | Always | Clock; active-LOW reset | |
| `CXSVALID` | TX → RX | 1 | Always | "Current cycle has a valid data flit" | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| `CXSDATA` | TX → RX | `CXSDATAFLITWIDTH` (8 to 2048, a multiple of 8; default 256) | Always | Data bytes of the flit | [Streaming](streaming-interfaces.md#cxs-credited-extensible-stream-cxs-d) |
| `CXSCNTL` | TX → RX | `CXSCNTLWIDTH` (0, 14, 18, 22, 27, 33, 36 or 44) | if width > 0 | Packet start, end and error information | [Streaming](streaming-interfaces.md#cxs-credited-extensible-stream-cxs-d) |
| `CXSLAST` | TX → RX | 1 | `CXS_LAST` | Flits can be inserted into the stream after this cycle | |
| `CXSPRCLTYPE` | TX → RX | 3 | `CXS_PROTOCOL_TYPE` | Protocol type of the flit | |
| `CXSSRCID`, `CXSTGTID` | TX → RX | 0–8 | `CXS_SRCID_WIDTH`, `CXS_TGTID_WIDTH` | Source and target node of the flit | [Chiplets: routing](chiplets-and-chip-to-chip.md#routing-c2c-b-ch-b6b7) |
| `CXSUSER` | TX → RX | 0–128 | `CXS_USER_WIDTH` | User bits | [User signals](interface-properties-and-user-signals.md#user-signals) |
| `CXSCRDGNT` | RX → TX | 1 | Always | Grants one credit | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| `CXSCRDRTN` | TX → RX | 1 | `CXSLINKCONTROL = Explicit_Credit_Return` | Returns one credit without a flit | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| `CXSACTIVEREQ` | TX → RX | 1 | `CXSLINKCONTROL = Explicit_Credit_Return` | Link activation or deactivation request | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| `CXSACTIVEACK` | RX → TX | 1 | `CXSLINKCONTROL = Explicit_Credit_Return` | Link activation or deactivation acknowledge | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| `CXSDEACTHINT` | RX → TX | 1 | `CXSLINKCONTROL = Explicit_Credit_Return` | The Receiver wants the link deactivated | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| Check signals | both | per payload | `CXSCHECKTYPE = Odd_Byte_Parity` | Interface parity (CXS-D §3.2) | [Parity and RAS](interface-protection-parity-and-ras.md#parity-check-signals) |

Other properties (CXS-D Table 2-2): `CXS_MAX_CREDIT` (1–63, default 15), `CXS_MAX_CREDIT_LATENCY`, `CXSCONTINUOUSDATA`, `CXSERRORFULLPKT` and `CXSMAXPKTPERFLIT` (1–4, default 2). When `CXSMAXPKTPERFLIT` is greater than 1, `CXSDATAFLITWIDTH` must be 256, 512, 1024 or 2048. CXS-Lite is a reduced form (CXS-D ch. 6).

## Link states

With link control, (`CXSACTIVEREQ`, `CXSACTIVEACK`) gives four states, like CHI (CXS-D §5.2):

| State | REQ ACK | Transmitter | Receiver |
|---|---|---|---|
| STOP | 0 0 | Must not send flits or credit returns | Must not send credit |
| ACTIVATE | 1 0 | Must accept credit; cannot send flits until it observes RUN | Not permitted to send credit, except in the cycle it moves to RUN |
| RUN | 1 1 | Sends flits; credit returns permitted but not expected | Sends credit |
| DEACTIVATE | 0 1 | Must stop sending flits before entering; returns all credits | May send credit when entering, then must stop; moves to STOP only when all credits are returned |

"The Transmitter is always responsible for initiating the state change from RUN to STOP, or from STOP to RUN" (CXS-D §5.3).

## Key rules checklist

| # | Rule | Source | Explained in |
|---|---|---|---|
| 1 | During reset CXSVALID, CXSCRDGNT, CXSCRDRTN, CXSACTIVEREQ, CXSACTIVEACK and CXSDEACTHINT must be deasserted, and all credits are at the Receiver | CXS-D §2.1.1 | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| 2 | "There must be no combinatorial paths between input and output signals on an interface" | CXS-D §2.1.1 | |
| 3 | Data is sent only with a credit. A credit granted in one cycle can be used from the next cycle; a consumed or returned credit can be reused by the Receiver from the next cycle | CXS-D §2.1.2 | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| 4 | At most `CXS_MAX_CREDIT` credits; a non-configurable Transmitter must track 15 | CXS-D §2.1.2 | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| 5 | "The CXSCRDRTN and CXSVALID signals must not be asserted in the same cycle" | CXS-D §2.1.2 | |
| 6 | Full bandwidth needs credits ≥ credit latency | CXS-D §2.1.2 | [Handshakes](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| 7 | Link states and behaviour as in the table above | CXS-D §5.2–5.4 | [Low power](low-power-and-wakeup.md#clock-gating-hints-and-link-activation) |
| 8 | Packet position, size and CXSCNTL rules | CXS-D ch. 4 | [Streaming](streaming-interfaces.md#cxs-credited-extensible-stream-cxs-d) |

## Protocol assertions

SystemVerilog assertions for rules 1, 3–5 and 7. They come from `assertions/cxs_checker.sv` in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository, which also has a test for every assertion.

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.**

| Assertion | Rule | Source |
|---|---|---|
| `cxs_reset_quiet` | All control signals LOW during reset | CXS-D §2.1.1 |
| `cxs_valid_needs_credit` | No flit without a credit held from an earlier cycle | CXS-D §2.1.2 |
| `cxs_credit_max` | At most `CXS_MAX_CREDIT` credits | CXS-D §2.1.2 |
| `cxs_crdrtn_not_with_valid` | CXSCRDRTN and CXSVALID never together | CXS-D §2.1.2 |
| `cxs_crdrtn_needs_credit` | A credit return needs a credit to return | CXS-D §2.1.2 (see note) |
| `cxs_valid_only_in_run` | Flits only in RUN | CXS-D §5.2, §5.4 |
| `cxs_no_credit_when_stopped` | No credits in STOP or ACTIVATE (the cycle ACK rises is allowed) | CXS-D §5.2 |
| `cxs_credits_returned_before_stop` | CXSACTIVEACK falls only after all credits are back | CXS-D §5.2 |

```systemverilog
// Transmitter credits: a grant is usable from the next cycle (CXS-D §2.1.2)
always_ff @(posedge CLK)
  if (!RESETn) credits <= '0;
  else         credits <= credits + 8'(CXSCRDGNT) - 8'(CXSVALID) - 8'(CXSCRDRTN);

cxs_valid_needs_credit: assert property (@(posedge CLK) disable iff (!RESETn)
    CXSVALID |-> (credits > 0));
cxs_crdrtn_not_with_valid: assert property (@(posedge CLK) disable iff (!RESETn)
    !(CXSCRDRTN && CXSVALID));
cxs_valid_only_in_run: assert property (@(posedge CLK) disable iff (!RESETn)
    CXSVALID |-> (CXSACTIVEREQ && CXSACTIVEACK));
cxs_credits_returned_before_stop: assert property (@(posedge CLK) disable iff (!RESETn)
    (!CXSACTIVEACK && $past(CXSACTIVEACK)) |-> (credits == 0));
```

*Editor's note (not from the sources): `cxs_crdrtn_needs_credit` follows from the credit counting in §2.1.2 rather than from a sentence in the spec: a Transmitter cannot return a credit it does not hold.*

Not covered: CXSCNTL and packet rules (ch. 4), CXSLAST, CXSDEACTHINT behaviour after reset, CXS-Lite and parity.

## Related articles

- [Streaming interfaces](streaming-interfaces.md)
- [Chiplets and chip-to-chip](chiplets-and-chip-to-chip.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [CHI interface hub](interface-chi.md)
- [AXI-Stream interface hub](interface-axi-stream.md)

## Sources

CXS-D (Tables 2-1, 2-2, 3-1; §2.1, ch. 5). See [Source key](sources.md).
