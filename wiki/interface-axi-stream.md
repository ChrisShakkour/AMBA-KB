# AXI-Stream interface hub

> Everything about one AXI-Stream (AXI4-Stream / AXI5-Stream) interface on one page: every signal with its presence and default, a transfer in brief, the rules a design must follow, and protocol assertions. Each line links to the concept article that explains it in depth. This page summarises; it does not replace [Streaming interfaces](streaming-interfaces.md#axi-stream-axis-b).

## In plain words

AXI-Stream "is a point-to-point protocol, connecting a single Transmitter and a single Receiver" (AXIS-B §1.1). It has one channel, with a VALID/READY handshake, and no addresses. Each transfer carries `TDATA` bytes, which byte qualifiers (`TKEEP`, `TSTRB`) mark as data, position or null bytes. `TLAST` marks packet boundaries, and `TID`/`TDEST` identify interleaved streams. Issue A defined AXI4-Stream; Issue B adds AXI5-Stream, with wake-up signalling and parity (AXIS-B §1.1).

## Signals

From AXIS-B Table 2-1 (meaning) and Table B-1 (presence). Presence codes: **Y** mandatory, **O** optional, **C** present if the property is True or non-zero, **N** not present (AXIS-B Appendix B).

| Signal | Source | Width | AXI5-Stream / AXI4-Stream | Default if absent | Meaning | Explained in |
|---|---|---|---|---|---|---|
| `ACLK` | Clock | 1 | Y / Y | — | Global clock; all signals sampled on its rising edge | |
| `ARESETn` | Reset | 1 | Y / Y | — | Active-LOW reset | |
| `TVALID` | Transmitter | 1 | Y / Y | — | A valid transfer is being driven | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| `TREADY` | Receiver | 1 | O / O | HIGH | The Receiver can accept a transfer | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| `TDATA` | Transmitter | `TDATA_WIDTH` (whole bytes; 8–1024 recommended) | C / O | — | The payload | [Streaming](streaming-interfaces.md#axi-stream-axis-b) |
| `TSTRB` | Transmitter | `TDATA_WIDTH/8` | O / O | = TKEEP | Data byte (HIGH) or position byte (LOW) | [Streaming](streaming-interfaces.md#axi-stream-axis-b) |
| `TKEEP` | Transmitter | `TDATA_WIDTH/8` | O / O | all HIGH | Byte is part of the stream (HIGH) or a null byte (LOW) | [Streaming](streaming-interfaces.md#axi-stream-axis-b) |
| `TLAST` | Transmitter | 1 | O / O | see below | Packet boundary | [Streaming](streaming-interfaces.md#axi-stream-axis-b) |
| `TID` | Transmitter | `TID_WIDTH` (≤ 8 recommended) | C / O | LOW | Data stream identifier | [Ordering: streams](transaction-ids-and-ordering.md#streams-total-order) |
| `TDEST` | Transmitter | `TDEST_WIDTH` (≤ 8 recommended) | C / O | LOW | Routing information | [Ordering: streams](transaction-ids-and-ordering.md#streams-total-order) |
| `TUSER` | Transmitter | `TUSER_WIDTH` | C / O | LOW | User sideband | [User signals](interface-properties-and-user-signals.md#user-signals) |
| `TWAKEUP` | Transmitter | 1 | C (`Wakeup_Signal`) / N | — | Activity on the interface; glitch-free | [Low power](low-power-and-wakeup.md#wake-up-signals-on-bus-interfaces) |
| `T*CHK` (parity) | both | per payload | C (`Check_Type`) / N | — | Interface parity (AXIS-B ch. 5) | [Parity and RAS](interface-protection-parity-and-ras.md#parity-check-signals) |

Default rules (AXIS-B §3.1): "If TKEEP is absent, TKEEP defaults to all bits HIGH"; "If TSTRB is absent, TSTRB = TKEEP". TLAST has no single default: a component that does not support TLAST, in an interconnect whose behaviour is unknown, "must default to HIGH". A Receiver with extra TID, TDEST and TUSER inputs "must have all undriven bits fixed LOW". If TDATA is absent, TSTRB must be absent too.

| TKEEP | TSTRB | Byte type (AXIS-B Table 2-3) |
|---|---|---|
| HIGH | HIGH | Data byte |
| HIGH | LOW | Position byte |
| LOW | LOW | Null byte |
| LOW | HIGH | Reserved: "Must not be used" |

## A transfer in brief

A transfer happens at a rising edge where TVALID and TREADY are both HIGH. Either may rise first (AXIS-B §2.2). A packet is a sequence of transfers with the same TID and TDEST, ending with TLAST HIGH (AXIS-B §2.6). Different streams may be interleaved transfer by transfer, but transfers are never reordered (AXIS-B §4.1–4.2).

## Key rules checklist

| # | Rule | Source | Explained in |
|---|---|---|---|
| 1 | TVALID is LOW during reset, and may first go HIGH at an edge after the edge where ARESETn is HIGH | AXIS-B §2.8 | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| 2 | A Transmitter must not wait for TREADY before asserting TVALID; once asserted, TVALID stays until the handshake | AXIS-B §2.2 | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| 3 | "The valid data bytes and control information from the Transmitter must remain unchanged once TVALID has been asserted" | AXIS-B §2.2 | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| 4 | TKEEP LOW with TSTRB HIGH must not be used | AXIS-B §2.5.3 | [Streaming](streaming-interfaces.md#axi-stream-axis-b) |
| 5 | If TWAKEUP and TVALID are HIGH together, TWAKEUP stays HIGH until TREADY; a Receiver may wait for TWAKEUP before TREADY | AXIS-B §2.3 | [Low power](low-power-and-wakeup.md#wake-up-signals-on-bus-interfaces) |
| 6 | The number of packets and TLAST assertions must be preserved; transfers of different packets, or with different TID or TDEST, must not be merged | AXIS-B §2.6 | [Streaming](streaming-interfaces.md#axi-stream-axis-b) |
| 7 | Width converters must preserve data and position bytes, and may add or remove null bytes | AXIS-B §2.4, §3.2.3 | [Bridges: width converters](bridges-and-adapters.md#3-width-converters-upsizers-and-downsizers) |
| 8 | "The reordering of transfers is not permitted" | AXIS-B §4.2 | [Ordering: streams](transaction-ids-and-ordering.md#streams-total-order) |
| 9 | With `Continuous_Packets` True: when TLAST is LOW, TID and TDEST must not change in the next transfer; TSTRB is absent; if TLAST is LOW all TKEEP bits are HIGH | AXIS-B §3.3 | [Streaming](streaming-interfaces.md#axi-stream-axis-b) |

## Protocol assertions

SystemVerilog assertions for rules 1–5 and 9. They come from `assertions/axis_checker.sv` in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository, which also has a test for every assertion. Parameters switch on the TWAKEUP and Continuous_Packets checks.

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.**

| Assertion | Rule | Source |
|---|---|---|
| `axis_reset_tvalid_low` | TVALID LOW during reset and at the first edge after it | AXIS-B §2.8 |
| `axis_tvalid_held` | TVALID held until TREADY | AXIS-B §2.2 |
| `axis_payload_stable` | Control signals and kept data bytes stable until TREADY | AXIS-B §2.2 |
| `axis_keep_strb_reserved` | No byte with TKEEP LOW and TSTRB HIGH | AXIS-B §2.5.3 |
| `axis_twakeup_held` | TWAKEUP held until TREADY once TVALID is HIGH | AXIS-B §2.3 |
| `axis_cont_no_interleave`, `axis_cont_no_null` | Continuous packets: no TID/TDEST change mid-packet, no null bytes before TLAST | AXIS-B §3.3 |

```systemverilog
// AXIS-B §2.2: TVALID stays asserted until the handshake ...
axis_tvalid_held: assert property (@(posedge ACLK) disable iff (!ARESETn)
    (TVALID && !TREADY) |=> TVALID);
// ... and valid data bytes and control information remain unchanged
axis_payload_stable: assert property (@(posedge ACLK) disable iff (!ARESETn)
    (TVALID && !TREADY) |=>
      $stable({TSTRB, TKEEP, TLAST, TID, TDEST, TUSER, tdata_kept}));

// AXIS-B Table 2-3: TKEEP LOW with TSTRB HIGH is reserved
axis_keep_strb_reserved: assert property (@(posedge ACLK) disable iff (!ARESETn)
    TVALID |-> ((~TKEEP & TSTRB) == '0));
```

`tdata_kept` is TDATA with null bytes (TKEEP LOW) forced to zero, because only "valid data bytes" must stay unchanged.

*Editor's note (not from the sources): treating position bytes (TKEEP HIGH, TSTRB LOW) as bytes that must stay stable is a conservative reading of "valid data bytes and control information".*

Not covered: parity, the meaning of TUSER, merging rules inside interconnects, and a Receiver's interleaving limit.

## Related articles

- [Streaming interfaces](streaming-interfaces.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [CXS interface hub](interface-cxs.md)
- [AXI interface hub](interface-axi.md)

## Sources

AXIS-B (Tables 2-1, 2-3, B-1, B-3; §1.1, §2.2–2.8, ch. 3–4). See [Source key](sources.md).
