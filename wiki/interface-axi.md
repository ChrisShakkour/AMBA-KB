# AXI interface hub

> Everything about one AXI interface on one page: the core signals of the five channels, the optional AXI5 signal groups and the properties that enable them, a transaction in brief, the rules a design must follow, and protocol assertions. Each line links to the concept article that explains it in depth. This page summarises; it does not replace those articles.

## In plain words

AXI splits every interface into five independent channels: write request (AW), write data (W), write response (B), read request (AR) and read data (R) (AXI-L ch. A2–A3). Each channel has its own VALID/READY handshake, or credits with credited transport in Issue L (AXI-L §A2.2). Transactions carry IDs, so a Subordinate may answer different IDs out of order (AXI-L §A5). AXI-L describes AXI5 as one fully featured protocol whose optional parts are switched on by **properties**. AXI3, AXI4 and AXI4-Lite are described in AXI-Hc, not in AXI-L (AXI-L ch. B2).

## Core signals

From AXI-L Appendix B1, Tables B1.1–B1.8 (name, width, source) and Table B2.2 (the property that controls presence). AXI4 has the same core signals except credited transport (see [Protocol evolution: AXI](protocol-evolution-and-versions.md#axi-axi-hc-appendix-g7-axi-l-b4)).

| Channel | Signal | Width | Source | Present when | Meaning | Explained in |
|---|---|---|---|---|---|---|
| — | `ACLK`, `ARESETn` | 1 | External | always | Clock; active-LOW reset | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| AW | `AWVALID` / `AWREADY` | 1 | Manager / Subordinate | always / `AXI_Transport == Ready` | Handshake | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| AW | `AWID` | `ID_W_WIDTH` | Manager | `ID_W_WIDTH > 0` | Transaction identifier | [IDs and ordering](transaction-ids-and-ordering.md#axi-the-id-based-model) |
| AW | `AWADDR` | `ADDR_WIDTH` | Manager | always | Address of the first transfer | [Bursts](bursts-sizes-and-alignment.md) |
| AW | `AWLEN` | 8 | Manager | `LEN_Present` | Length = AWLEN + 1 transfers | [Bursts](bursts-sizes-and-alignment.md#burst-encodings-side-by-side) |
| AW | `AWSIZE` | 3 | Manager | `SIZE_Present` | Bytes per transfer | [Bursts: size](bursts-sizes-and-alignment.md#size) |
| AW | `AWBURST` | 2 | Manager | `BURST_Present` | FIXED, INCR or WRAP | [Bursts](bursts-sizes-and-alignment.md#burst-encodings-side-by-side) |
| AW | `AWLOCK` | 1 | Manager | `Exclusive_Accesses` | Exclusive access | [Exclusive access](exclusive-locked-and-atomic-access.md#2-exclusive-access) |
| AW | `AWCACHE` | 4 | Manager | `CACHE_Present` | Memory attributes | [Memory types: AxCACHE](memory-types-and-cache-attributes.md#axi-axcache30-axi-l-a42) |
| AW | `AWPROT` | 3 | Manager | `PROT_Present` | Protection attributes | [Protection and security](protection-and-security.md#the-signals) |
| AW | `AWQOS` | 4 | Manager | `QOS_Present` | QoS identifier | [QoS](qos-and-traffic-modelling.md) |
| AW | `AWREGION` | 4 | Manager | `REGION_Present` | Region identifier | [Interconnect](interconnect-topology-and-bridges.md) |
| AW | `AWUSER` | `USER_REQ_WIDTH` | Manager | `USER_REQ_WIDTH > 0` | User extension to a request | [User signals](interface-properties-and-user-signals.md#user-signals) |
| W | `WVALID` / `WREADY` | 1 | Manager / Subordinate | always / `AXI_Transport == Ready` | Handshake | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| W | `WDATA` | `DATA_WIDTH` | Manager | always | Write data | |
| W | `WSTRB` | `DATA_WIDTH/8` | Manager | `WSTRB_Present` | Write strobes | [Bursts: write strobes](bursts-sizes-and-alignment.md#write-strobes) |
| W | `WLAST` | 1 | Manager | `WLAST_Present` | Last write transfer of the transaction | |
| W | `WUSER` | `USER_DATA_WIDTH` | Manager | `USER_DATA_WIDTH > 0` | User extension to write data | [User signals](interface-properties-and-user-signals.md#user-signals) |
| B | `BVALID` / `BREADY` | 1 | Subordinate / Manager | always / `AXI_Transport == Ready` | Handshake | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| B | `BID` | `ID_W_WIDTH` | Subordinate | `ID_W_WIDTH > 0` | Echoes AWID | [IDs and ordering](transaction-ids-and-ordering.md#axi-the-id-based-model) |
| B | `BRESP` | `BRESP_WIDTH` | Subordinate | `BRESP_WIDTH > 0` | Write response | [Responses and errors](responses-and-errors.md#response-vocabularies) |
| B | `BUSER` | `USER_RESP_WIDTH` | Subordinate | `USER_RESP_WIDTH > 0` | User extension to a write response | |
| AR | `ARVALID` / `ARREADY`, `ARID`, `ARADDR`, `ARLEN`, `ARSIZE`, `ARBURST`, `ARLOCK`, `ARCACHE`, `ARPROT`, `ARQOS`, `ARREGION`, `ARUSER` | as AW (`ID_R_WIDTH` for ARID) | Manager (ARREADY: Subordinate) | as AW | The read-request equivalents of the AW signals | as AW |
| R | `RVALID` / `RREADY` | 1 | Subordinate / Manager | always / `AXI_Transport == Ready` | Handshake | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| R | `RID` | `ID_R_WIDTH` | Subordinate | `ID_R_WIDTH > 0` | Echoes ARID | [IDs and ordering](transaction-ids-and-ordering.md#axi-the-id-based-model) |
| R | `RDATA` | `DATA_WIDTH` | Subordinate | always | Read data | |
| R | `RRESP` | `RRESP_WIDTH` | Subordinate | `RRESP_WIDTH > 0` | Read response, per transfer | [Responses and errors](responses-and-errors.md#response-vocabularies) |
| R | `RLAST` | 1 | Subordinate | `RLAST_Present` | Last read transfer of the transaction | |
| R | `RUSER` | `USER_DATA_WIDTH + USER_RESP_WIDTH` | Subordinate | user widths > 0 | User extension to read data and response | |

## Optional AXI5 signal groups

Each group is switched on by the property shown, which comes from AXI-L Table B2.2. Use AXI-L Appendix B1 for the exact signal list of each group.

| Group | Example signals | Enabling property | Explained in |
|---|---|---|---|
| Credited transport | `xPENDING`, `xCRDT`, `xCRDTSH`, `xRP`, `xSHAREDCRD`; `ACTIVATEREQ/ACK`, `ASKSTOP` | `AXI_Transport == Credited`, `Num_RP_*`, `Shared_Credits_*` | [Handshakes: credits](handshakes-and-flow-control.md#3-credit-based-flow-control) |
| Security and RME | `AxNSE`, `AxPAS`, `AxINST`, `AxPRIV` | `RME_Support`, `PAS_WIDTH > 0`, `INSTPRIV_Present` | [Protection and security](protection-and-security.md) |
| Coherent and shareable requests | `AxDOMAIN`, `AxSNOOP` | `Shareable_Transactions`, `AxSNOOP_WIDTH > 0` | [ACE](ace-coherency-extensions.md), [Coherency](cache-coherency-fundamentals.md) |
| Cache stashing | `AWSTASHNID(EN)`, `AWSTASHLPID(EN)` | `STASHNID_Present`, `STASHLPID_Present` | [Memory types: other hints](memory-types-and-cache-attributes.md#other-axi5-hints-and-attributes-axi-l-ch-a8-a10a11) |
| Atomic transactions | `AWATOP` | `Atomic_Transactions` | [Atomics](exclusive-locked-and-atomic-access.md#3-atomic-transactions-axi5-chi-b) |
| Untranslated transactions (SMMU) | `AxMMUVALID`, `AxMMUSID`, `AxMMUSSID(V)`, `AxMMUATST`, `AxMMUFLOW` … | `Untranslated_Transactions`, `SID_WIDTH`, `SSID_WIDTH`, `MMUFLOW_Present` | [DVM and address translation](dvm-and-address-translation.md) |
| Memory tagging (MTE) | `AxTAGOP`, `WTAG`, `WTAGUPDATE`, `RTAG`, `BTAGMATCH` | `MTE_Support` | [Protection and security](protection-and-security.md#newer-security-features-axi5--chi) |
| Memory partitioning and encryption | `AxMPAM`, `AxMECID`, `AxNSAID`, `AxSUBSYSID`, `AxPBHA` | `MPAM_Support`, `MEC_Support`, `NSAccess_Identifiers`, `SUBSYSID_WIDTH > 0`, `PBHA_Support` | [QoS](qos-and-traffic-modelling.md), [Protection](protection-and-security.md) |
| Unique ID | `AxIDUNQ`, `BIDUNQ`, `RIDUNQ` | `Unique_ID_Support` | [IDs and ordering](transaction-ids-and-ordering.md) |
| Cache maintenance on writes | `AWCMO` | `CMO_On_Write` | [Coherency](cache-coherency-fundamentals.md) |
| Poison and read-data chunking | `WPOISON`, `RPOISON`; `ARCHUNKEN`, `RCHUNKV`, `RCHUNKNUM`, `RCHUNKSTRB` | `Poison`; `Read_Data_Chunking` | [Parity and RAS](interface-protection-parity-and-ras.md#poison-datacheck-and-data-errors), [Ordering](transaction-ids-and-ordering.md#interleaving) |
| Busy indicators | `BBUSY`, `RBUSY` | `Busy_Support` | [QoS](qos-and-traffic-modelling.md) |
| Arm Compression Technology | `AxACT`, `AxACTV` | `ACT_Support` | [Protocol evolution](protocol-evolution-and-versions.md) |
| Trace and loopback | `xTRACE`, `xLOOP` | `Trace_Signals`, `Loopback_Signals` | [User signals](interface-properties-and-user-signals.md) |
| DVM on the snoop channels | `AC*`, `CR*`; `SYSCOREQ/ACK` | `DVM_Message_Support`; `Coherency_Connection_Signals` | [DVM](dvm-and-address-translation.md), [Low power](low-power-and-wakeup.md) |
| Wake-up and QoS accept | `AWAKEUP`, `ACWAKEUP`; `VAWQOSACCEPT`, `VARQOSACCEPT` | `Wakeup_Signals`; `QoS_Accept` | [Low power](low-power-and-wakeup.md#wake-up-signals-on-bus-interfaces), [QoS](qos-and-traffic-modelling.md) |
| Broadcast tie-offs | `BROADCASTATOMIC`, `BROADCASTSHAREABLE`, `BROADCASTCACHEMAINT` … | static inputs | [Properties: broadcast pins](interface-properties-and-user-signals.md#broadcast-pins-tie-offs-that-switch-features-off) |
| Parity | `*CHK` signals | `Check_Type` | [Parity and RAS](interface-protection-parity-and-ras.md#parity-check-signals) |

## A transaction in brief

```
Write:  AW (address, ID, LEN, SIZE, BURST) --->
        W  (DATA, STRB) x (AWLEN+1), last beat with WLAST --->
                                    <--- B (BID = AWID, BRESP), only after AW and the WLAST beat
Read:   AR (address, ID, LEN, SIZE, BURST) --->
                                    <--- R (RID = ARID, DATA, RRESP) x (ARLEN+1), last with RLAST
```

Every channel transfer happens at a rising edge where VALID and READY are both HIGH (AXI-L §A2.3). See [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family), [Transfer phases](transfer-phases-and-pipelining.md#axi-five-independent-channels) and [IDs and ordering](transaction-ids-and-ordering.md#axi-the-id-based-model).

## Key rules checklist

| # | Rule | Source | Explained in |
|---|---|---|---|
| 1 | VALID signals are LOW during reset, and stay LOW until the rising edge after ARESETn goes HIGH | AXI-L §A2.1.2, §A2.3 | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| 2 | A transmitter must not wait for READY before asserting VALID | AXI-L §A2.3 | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| 3 | Once asserted, VALID stays asserted, with the information stable, until the handshake | AXI-L §A2.3 | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| 4 | BVALID only after the AW handshake and the last W transfer; RVALID only after the AR handshake | AXI-L §A2.3.2.1–A2.3.2.2 | [Handshakes](handshakes-and-flow-control.md#2-validready-handshake-axi-family) |
| 5 | A transaction must not cross a 4KB address boundary | AXI-L §A3.1 | [Interconnect: decode granules](interconnect-topology-and-bridges.md#decode-granules-why-1-kb-and-4-kb-matter) |
| 6 | AxSIZE must not exceed the data width | AXI-L §A3.1.1 | [Bursts: size](bursts-sizes-and-alignment.md#size) |
| 7 | WRAP: length 2, 4, 8 or 16 and a start address aligned to the size. FIXED: length up to 16. AxBURST 0b11 is reserved. With `Wrap_CLS_Modifiable` True (the default), WRAP must be one cache line and Modifiable | AXI-L §A3.1.2, §A3.1.4 | [Bursts](bursts-sizes-and-alignment.md#burst-encodings-side-by-side) |
| 8 | No early termination: the Manager sends AxLEN+1 write transfers, the Subordinate AxLEN+1 read transfers, with xLAST on the final one | AXI-L §A3.1.2, §A3.2 | [Bursts](bursts-sizes-and-alignment.md) |
| 9 | BID and RID echo AWID and ARID; responses with the same ID return in order | AXI-L §A5.1.1, §A5.3 | [IDs and ordering](transaction-ids-and-ordering.md#what-is-guaranteed-axi-l-a53) |
| 10 | Interconnects and bridges must not resize, split or merge Non-modifiable transactions, except to split bursts longer than 16 | AXI-L §A4.2.2 | [Memory types](memory-types-and-cache-attributes.md) |

## Protocol assertions

SystemVerilog assertions for rules 1 and 3–7, for the five channels with Valid-Ready transport. They come from `assertions/axi_checker.sv` in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository, which also has a test for every assertion.

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.** Treat these as reviewed drafts until `python assertions/run_tests.py axi` passes.

| Assertion | Rule | Source |
|---|---|---|
| `axi_reset_valid_low` | All VALIDs LOW during reset and at the first edge after it | AXI-L §A2.1.2, §A2.3 |
| `axi_{aw,w,b,ar,r}_valid_held` | VALID held until READY | AXI-L §A2.3 |
| `axi_{aw,w,b,ar,r}_stable` | Payload stable until READY | AXI-L §A2.3 |
| `axi_burst_reserved` | AxBURST is not 0b11 | AXI-L §A3.1.4 |
| `axi_wrap_len`, `axi_wrap_aligned` | WRAP length 2/4/8/16, start aligned to size | AXI-L §A3.1.2, §A3.1.4 |
| `axi_fixed_len` | FIXED length at most 16 | AXI-L §A3.1.2 |
| `axi_size` | AxSIZE within the data width | AXI-L §A3.1.1 |
| `axi_4kb` | INCR bursts do not cross 4KB | AXI-L §A3.1 |
| `axi_bvalid_after`, `axi_rvalid_after` | Responses only for accepted requests (and, for B, completed write data) | AXI-L §A2.3.2.1–A2.3.2.2 |

```systemverilog
// AXI-L §A2.3: VALID LOW during reset; §A2.1.2: still LOW at the edge after reset (rst_q)
axi_reset_valid_low: assert property (@(posedge ACLK)
    rst_q |-> !(AWVALID || WVALID || BVALID || ARVALID || RVALID));

// AXI-L §A2.3: VALID stays asserted, with stable information, until the handshake
axi_aw_valid_held: assert property (@(posedge ACLK) disable iff (!ARESETn)
    (AWVALID && !AWREADY) |=> AWVALID);
axi_aw_stable: assert property (@(posedge ACLK) disable iff (!ARESETn)
    (AWVALID && !AWREADY) |=>
      $stable({AWID, AWADDR, AWLEN, AWSIZE, AWBURST, AWLOCK, AWCACHE, AWPROT, AWQOS}));

// AXI-L §A3.1.2: wrapping bursts have length 2, 4, 8 or 16
axi_wrap_len: assert property (@(posedge ACLK) disable iff (!ARESETn)
    (!(AWVALID && AWBURST == WRAP) || (AWLEN inside {8'd1, 8'd3, 8'd7, 8'd15})) &&
    (!(ARVALID && ARBURST == WRAP) || (ARLEN inside {8'd1, 8'd3, 8'd7, 8'd15})));

// AXI-L §A3.1: a transaction must not cross a 4KB address boundary
axi_4kb: assert property (@(posedge ACLK) disable iff (!ARESETn)
    (!(AWVALID && AWBURST == INCR) || !crosses_4k(AWADDR, AWLEN, AWSIZE)) &&
    (!(ARVALID && ARBURST == INCR) || !crosses_4k(ARADDR, ARLEN, ARSIZE)));

// AXI-L §A2.3.2.1: BVALID only after the AW handshake and the WLAST transfer
axi_bvalid_after: assert property (@(posedge ACLK) disable iff (!ARESETn)
    BVALID |-> (aw_cnt > b_cnt) && (wlast_cnt > b_cnt));
```

`aw_cnt`, `wlast_cnt` and `b_cnt` count completed handshakes; `crosses_4k` compares the 4KB page of the first and last byte. See the checker file for the full code.

*Editor's note (not from the sources):* `axi_bvalid_after` and `axi_rvalid_after` compare totals, so they catch a response with nothing outstanding, but not a response with the wrong ID.

Not covered: WLAST/RLAST beat counts, ID matching and ordering, exclusive-access rules, `Wrap_CLS_Modifiable`, credited transport and the optional AXI5 signal groups.

## Versions

AXI3 (Issue B, 2004) → AXI4 and AXI4-Lite (Issue C, 2010: 256-beat INCR, no WID, no locked transfers, QoS, REGION, USER) → ACE (Issue D) → AXI5 and the ACE5 variants (Issue F, 2017) → … → Issue J (2023) removes AXI3, AXI4 and ACE → Issue L (2025) adds credited transport and `Wrap_CLS_Modifiable`. Details: [Protocol evolution: AXI](protocol-evolution-and-versions.md#axi-axi-hc-appendix-g7-axi-l-b4).

## Related articles

- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Transaction IDs, outstanding transactions and ordering](transaction-ids-and-ordering.md)
- [Bursts, sizes, alignment and write strobes](bursts-sizes-and-alignment.md)
- [Memory types and cache attributes](memory-types-and-cache-attributes.md)
- [Responses and error signalling](responses-and-errors.md)
- [Interface properties, optional signals and user signals](interface-properties-and-user-signals.md)
- [ACE: AXI Coherency Extensions](ace-coherency-extensions.md)
- [APB interface hub](interface-apb.md)
- [AHB interface hub](interface-ahb.md)

## Sources

AXI-L (Appendix B1–B2, ch. A2–A5, §A4.2.2), AXI-Hc. See [Source key](sources.md).
