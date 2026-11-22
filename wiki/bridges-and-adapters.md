# Bridges, adapters and converters

> The small modules that join AMBA interfaces together: protocol bridges (AHB→APB, AXI→AHB), register and memory endpoints, upsizers and downsizers, clock- and power-domain bridges, register slices, ID and burst shapers, and the trace and debug equivalents. This article lists what the **specifications require** of any such module, and what **real component libraries** provide.

## In plain words

An SoC rarely uses one protocol everywhere. A fast AXI or CHI backbone carries the heavy traffic, and slower AHB and APB "islands" hang off it (AMBA2 §1.7; APB-E §1.1). Every border between two interfaces needs a translator, and so does every border where something else changes:

- the **protocol** (AXI→APB),
- the **data width** (64-bit → 32-bit),
- the **clock or power domain** (fast core clock → slow peripheral clock),
- the **timing** (a long wire that needs a pipeline stage),
- the **ID width, burst shape or feature set** (wide IDs → narrow IDs, AXI4 long bursts → AXI3 16-beat bursts).

The AMBA specifications don't define a catalogue of these modules. They define the interfaces, and a set of rules that any module in the middle must obey. The modules themselves come from component libraries: Arm's own (CMSDK, CoreLink NIC-400, CoreSight SoC-400), EDA vendors' (Synopsys DesignWare), FPGA vendors' (AMD) and open source (PULP, verilog-axi).

A bridge plays both roles at once. It is a Completer or Subordinate on one side and a Requester or Manager on the other, for example the APB bridge (APB-E §1.1). An AXI interconnect likewise uses one interface definition on both sides (AXI-L §A1.2.1).

## What the specifications require of any bridge or adapter

These rules come from the specifications in this wiki's source set. They apply whichever library you use, or if you write the module yourself.

| Module kind | Rule | Source |
|---|---|---|
| AHB/ASB → APB bridge | Appears as one Subordinate on the system bus, latches address, data and control, and does a second-level decode to generate `PSELx` | AMBA2 §1.7, §5.4 |
| AHB → APB bridge | A read straight after a write costs 3 wait states in the AMBA 2 example bridge | AMBA2 §5.6.3 |
| Any → APB bridge | `PSLVERR` maps to `RRESP`/`BRESP` = SLVERR (AXI) or `HRESP` = ERROR (AHB) | APB-E §3.4.3; APB-B §2.3.3 |
| APB endpoint | `PSLVERR` is optional; tie it LOW if unused | APB-E §3.4.1 |
| AXI endpoint without BRESP/RRESP | Assume OKAY | AXI-L §A3.3 |
| Register slice | Allowed on any AXI channel, because channels have no fixed timing relation. VALID and payload must be delayed together | AXI-L §A2.5 |
| Upsizer, downsizer, splitter, merger | Must honour Non-modifiable (AxCACHE[1]=0): never change address, size, length or burst type, except to split bursts longer than 16 beats | AXI-L §A4.2.2 |
| Burst splitter | An AXI transaction must not cross 4 KB. AXI5 `Max_Transaction_Bytes` can lower that to 64…4096 bytes, so that a striped interconnect needn't split | AXI-L §A3.1, §A3.1.3 |
| AHB narrow/wide adapter | A 32-bit AHB Subordinate can sit on a 64-bit bus, using `HADDR[2]` to pick the half. A Manager may sit on a narrower bus only if it never issues an HSIZE wider than that bus | AMBA2 §3.15 |
| AXI-Stream width converter | Must preserve data and byte positions; may add or remove null bytes | AXIS-B §2.4 |
| Any width converter | User bits on data channels are defined per byte, so they survive width conversion | AHB-C §11.1; AXIS-B §2.9 |
| Interconnects and bridges | Should carry user signals. Managers and Subordinates are not required to have them | APB-E §3.8.3; AHB-C §11.1 |
| Manager with IDs → Subordinate without | Not directly connectable, because BID and RID must echo AWID and ARID. An adapter must reflect the ID | AXI-L §A5.1.1 |
| AXI4 → AXI3 adapter | AXI4 allows INCR bursts up to 256 beats, and removed locked transfers and WID | AXI-C §13.1, §13.15–13.16 |
| AXI5 atomics → CHI | AWATOP sub-encodings are the same eight operations as CHI's sub-opcodes, so a bridge maps them one to one | AXI-L §A6.4 |
| AXI ↔ CHI bridge | Deferrable writes: AXI uses a 3-bit `BRESP` DEFER/UNSUPPORTED; CHI uses RespErr = OK with `Resp` = Defer/Unsupported. The bridge must translate | AXI-L §A11.2.3; CHI-H Table B4.29 |
| AXI → CHI bridge | CHI has no Write-Through memory type, so the bridge has to choose its own mapping | CHI-H §B2.8.3 |
| CHI I/O bridge | An RN-I "is used by an IO coherent Request Node such as a GPU or IO bridge" and has no SNP channel | CHI-H §B13.6.1.3 |
| Clock/power-domain bridge | Q-Channel and P-Channel handshakes are safe across asynchronous domains: "All signals are assumed to be asynchronous" | LPI-D §2.1 |
| ATB funnel | Must forward a flush to all sources, and acknowledge downstream only after all have acknowledged | ATB-C §1.2 |
| DTI transport | DTI messages can be carried over AXI4-Stream | DTI-E §6.2 |

See also the protection article for the `HPROT[0]` ↔ `AxPROT[2]` inverter in AHB↔AXI bridges, and the endianness article for BE32 byte swapping when bridging old big-endian AHB blocks. Both of those are editor's implementation tips, not spec rules.

## Catalogue by function

The **Examples** column names real components. Arm components are cited from their Technical Reference Manuals (see [Arm reference components](#arm-reference-components)). Third-party names come from the web references at the end of this article.

### 1. Register and memory endpoints (bus → simple interface)

| Module | What it does | Examples |
|---|---|---|
| APB → registers | Turns APB transfers into register read/write strobes | CMSDK `cmsdk_apb3_eg_slave.v` and `cmsdk_apb4_eg_slave.v`: each provides "four words of hardware RW registers and additional read-only ID registers" (CMSDK-C §4.1) |
| AXI4-Lite → registers | The same for AXI4-Lite; has to arbitrate between the independent read and write channels | verilog-axi `axil_reg_if` (W-VAXI); PULP `axi_lite_regs` (W-PULP) |
| AHB → SRAM | Zero-wait-state on-chip SRAM | CMSDK `cmsdk_ahb_to_sram.v` (CMSDK-C §3.7) |
| AHB → flash / external memory | Read-only flash with wait states; 8/16-bit external SRAM | CMSDK `cmsdk_ahb_to_flash32.v`, `cmsdk_ahb_to_flash16.v` (§3.8), `cmsdk_ahb_to_extmem16.v` (§3.10) |
| AXI → memory (req/gnt) | AXI4 to a simple SRAM-like request/grant interface | PULP `axi_to_mem` (W-PULP); verilog-axi `axi_ram`, `axi_ram_wr_rd_if` (W-VAXI) |
| Memory → AXI | Reverse direction: an SRAM-like port that issues AXI requests | PULP `axi_from_mem`, `axi_lite_from_mem` (W-PULP) |

### 2. Protocol bridges

| Bridge | Examples |
|---|---|
| AHB → APB (synchronous, slower APB clock) | CMSDK `cmsdk_ahb_to_apb.v`: "Supports APB2, APB3, and APB4" and "Runs the APB interface semi-synchronously slower than the AHB interface" (CMSDK-C §3.6) |
| AHB → APB (asynchronous) | CMSDK `cmsdk_ahb_to_apb_async.v` (CMSDK-C §5.4) |
| AHB → AHB + APB (asynchronous) | CMSDK `cmsdk_ahb_to_ahb_apb_async.v`, "supports AHB-Lite and APB4" (CMSDK-C §5.5.1) |
| AXI → APB | Synopsys `DW_axi_x2p` (W-SNPS); AMD AXI to APB Bridge, PG073: "Translates AXI4-Lite transactions into APB transactions" (W-AMD); PULP `axi_to_apb`, `axi_lite_to_apb` (W-PULP) |
| AXI → APB inside an interconnect | NIC-400 APB master interfaces: "An APB AMIB can have up to 16 subports. Each subport can be APB3 or APB4" (NIC400-J §1.2) |
| AXI → AHB | Synopsys `DW_axi_x2h` (W-SNPS); NIC-400 TLX configured as an AXI3/AXI4 to AHB-Lite bridge (NIC400-J §2.4.3) |
| AHB → AXI | Synopsys `DW_axi_hmx`, `DW_axi_a2x` (W-SNPS); NIC-400 AHB-Lite slave interfaces (NIC400-J §1.2) |
| AXI4 ↔ AXI3 | NIC-400 "AXI4 long bursts are split into multiple AXI3 bursts, up to a length of 16 beats" (NIC400-J §2.3.1); AMD AXI Protocol Converter (W-AMD) |
| AXI4 → AXI4-Lite and back | PULP `axi_to_axi_lite`, `axi_lite_to_axi` (W-PULP); verilog-axi `axi_axil_adapter` (W-VAXI); AMD AXI Protocol Converter (W-AMD) |
| AXI ↔ AXI-Stream (DMA) | AMD AXI DataMover, PG022, and AXI4-Stream FIFO, PG080 (W-AMD); verilog-axi `axi_dma` (W-VAXI) |

### 3. Width converters (upsizers and downsizers)

| Module | Examples |
|---|---|
| AHB 32 → 64 bit | CMSDK `cmsdk_ahb_upsizer64.v` "enables a 32-bit AHB bus master to connect to a 64-bit AHB slave" (CMSDK-C §5.2) |
| AHB 64 → 32 bit | CMSDK `cmsdk_ahb_downsizer64.v` "enables a 64-bit AHB bus master to connect to a 32-bit AHB slave" (CMSDK-C §5.3.1) |
| AXI up/down | NIC-400: upsizing ratios 1:2, 1:4, 1:8, and downsizing 2:1, 4:1, 8:1 (NIC400-J §2.3.3–2.3.4); PULP `axi_dw_converter`, `axi_dw_upsizer`, `axi_dw_downsizer` (W-PULP); verilog-axi `axi_adapter` (W-VAXI); AMD AXI Data Width Converter (W-AMD) |
| AXI4-Lite up/down | PULP `axi_lite_dw_converter` (W-PULP); verilog-axi `axil_adapter` (W-VAXI) |
| AXI-Stream | AMD AXI4-Stream Data Width Converter, PG085 (W-AMD); verilog-axis `axis_adapter` (W-VAXIS) |
| ATB | CoreSight `cxatbupsizer` (1:2 to 1:16) and `cxatbdownsizer` (2:1 to 16:1) (CSSOC-F §2.3.3–2.3.4) |

NIC-400 adds two cache-attribute rules on top of the AXI ones: upsizing "only packs write data for write or read transactions that are cacheable", and downsizing "does not merge data narrower than the destination bus if the transaction is marked as non-cacheable" (NIC400-J §2.3.3–2.3.4). These agree with the Non-modifiable rule above (AXI-L §A4.2.2).

### 4. Clock-domain and power-domain bridges

| Module | Examples |
|---|---|
| AHB ↔ AHB, synchronous | CMSDK `cmsdk_ahb_to_ahb_sync.v` "provides timing isolation in a large AHB system" (CMSDK-C §5.6.1) |
| AHB fast → slow / slow → fast | CMSDK `cmsdk_ahb_to_ahb_sync_down.v` and `cmsdk_ahb_to_ahb_sync_up.v`, each with an optional write buffer enabled through HPROT[2] (CMSDK-C §5.7.1, §5.8.1) |
| AHB ↔ AHB, low bandwidth with downsizing | Synopsys `DW_ahb_h2h`, and the higher-bandwidth `DW_ahb_eh2h` (W-SNPS) |
| AXI clock crossing | NIC-400 FIFOs, configurable as "SYNC 1:1", "SYNC 1:n", "SYNC n:1", "ASYNC" or "SYNC m:n", with a depth of 2–32 (NIC400-J §2.3.5); PULP `axi_cdc` (W-PULP); verilog-axi `axil_cdc` (W-VAXI); AMD AXI Clock Converter (W-AMD) |
| AXI-Stream clock crossing | AMD AXI4-Stream Clock Converter (W-AMD); verilog-axis `axis_async_fifo` (W-VAXIS) |
| APB clock crossing | CoreSight `cxapbasyncbridge` and `cxapbsyncbridge`, both with an LPI for power gating (CSSOC-F §2.2.2–2.2.3) |
| ATB clock crossing | CoreSight `cxatbasyncbridge`, "designed to exist across two power domains, and provides an LPI" (CSSOC-F §2.3.5), and `cxatbsyncbridge` (§2.3.6) |

### 5. Timing: register slices and pipeline stages

| Module | Examples |
|---|---|
| AXI register slice | Synopsys `DW_axi_rs` (W-SNPS); PULP `axi_cut`, `axi_multicut` (W-PULP); verilog-axi `axi_register` (W-VAXI); AMD AXI Register Slice (W-AMD) |
| AXI-Stream register slice | AMD AXI4-Stream Register Slice (W-AMD); verilog-axis `axis_register` (W-VAXIS) |
| FIFO buffering | PULP `axi_fifo` (W-PULP); verilog-axi `axi_fifo` (W-VAXI); AMD AXI Data FIFO (W-AMD) |

### 6. ID and transaction shapers (mostly AXI)

| Module | Examples |
|---|---|
| ID width converter or remapper | PULP `axi_iw_converter`, `axi_id_remap`, `axi_id_serialize`, `axi_id_prepend` (W-PULP); NIC-400 global ID and ID reduction (NIC400-J §2.3.12) |
| Serializer (all IDs → one ID) | PULP `axi_serializer` (W-PULP) |
| Burst splitter | PULP `axi_burst_splitter` (single beats), `axi_burst_splitter_gran` (W-PULP); NIC-400 burst limiter (NIC400-J §2.3.1) |
| WRAP → INCR | PULP `axi_burst_unwrap`, "into up to two incremental bursts" (W-PULP) |
| Atomic filter | PULP `axi_atop_filter` (W-PULP) |
| Outstanding-transaction limiter | PULP `axi_throttle` (W-PULP) |
| Isolation (stop new traffic before power-down or reset) | PULP `axi_isolate` (W-PULP) |

### 7. Infrastructure: muxes, default slaves and monitors

| Module | Examples |
|---|---|
| Default slave (answers unmapped addresses) | CMSDK `cmsdk_ahb_default_slave.v`: "A zero wait state OKAY response is generated for IDLE or BUSY transfers, and an ERROR response is generated for NONSEQUENTIAL or SEQUENTIAL transfers" (CMSDK-C §3.1); PULP `axi_err_slv` (W-PULP) |
| Slave mux / decoder | CMSDK `cmsdk_ahb_slave_mux.v` (up to ten slaves, §3.3); `cmsdk_apb_slave_mux.v` (up to 16 APB slaves, decoding four bits of PADDR, §4.6) |
| Master mux | CMSDK `cmsdk_ahb_master_mux.v` (up to three masters, CMSDK-C §3.4); PULP `axi_mux`, `axi_lite_mux` (W-PULP) |
| Bus matrix / crossbar | CMSDK AHB bus matrix: 1–16 slave and master ports, round-robin, fixed or burst arbitration (CMSDK-C §5.1.1); Synopsys `DW_ahb_icm` (W-SNPS); PULP `axi_xbar` (W-PULP); verilog-axi `axi_crossbar` (W-VAXI); AMD AXI Crossbar, SmartConnect PG247 (W-AMD) |
| Timeout monitor | CMSDK `cmsdk_ahb_timeout_mon.v` and `cmsdk_apb_timeout_mon.v`: if the slave holds HREADY (or PREADY) LOW too long, "the monitor generates an error response to the bus master" (CMSDK-C §3.9, §4.8) |
| Bit-band wrapper | CMSDK `cmsdk_ahb_bitband.v`, for software compatibility when moving from Cortex-M3/M4 to M0/M0+ (CMSDK-C §3.11) |
| Generic manager/subordinate gaskets | Synopsys `DW_axi_gm`, `DW_axi_gs` (W-SNPS) |

### 8. Trace and debug

| Module | Examples |
|---|---|
| ATB funnel and replicator | Defined in ATB-C §1.2; CoreSight `cxatbfunnel`, `cxatbreplicator` (CSSOC-F Table 1-1) |
| Debug access ports (debugger → bus Manager) | CoreSight AXI-AP, which "is an AXI bus master and enables a debugger to issue AXI transactions" (CSSOC-F §2.1.6); AHB-AP (§2.1.7); APB-AP (§2.1.8) |
| Timestamp bridges | CoreSight narrow timestamp asynchronous and synchronous bridges (CSSOC-F Table 1-1) |

### 9. Verification components

| Module | Examples |
|---|---|
| Protocol checkers | CMSDK `AhbLitePC.v` and `ApbPC.v`, simulation models that "detect bus protocol violations during simulation" (CMSDK-C §7.1–7.2) |
| Random Managers and Subordinates, scoreboards | PULP `axi_rand_master`, `axi_rand_slave`, `axi_scoreboard` (simulation only) (W-PULP) |

## Arm reference components

These three Arm Technical Reference Manuals are now part of the source set ([Source key](sources.md#arm-ip-product-manuals-not-specifications)). They describe products, not protocols, so they show how Arm itself builds adapters.

- **Cortex-M System Design Kit (CMSDK-C).** A library of AHB-Lite and APB components for microcontroller-class systems. Chapter 3 covers basic AHB-Lite components, chapter 4 APB components, chapter 5 advanced AHB-Lite components (bus matrix, upsizer, downsizer, asynchronous and synchronous bridges), and chapter 7 verification components.
- **CoreLink NIC-400 (NIC400-J).** A configurable interconnect, which "can range from a single bridge component, for example an AHB to AXI protocol conversion bridge, to a complex interconnect that consists of up to 128 masters and 64 slaves" (NIC400-J §1.1). Protocol conversion, upsizing, downsizing and clock crossing are functions inside the generated network (§2.3), not separate modules. The TLX option "reduce[s] the number of signals in an AXI point-to-point connection" and can be configured as one of eight AHB-Lite/AXI3/AXI4 bridge pairings (§2.4.3).
- **CoreSight SoC-400 (CSSOC-F).** Debug and trace infrastructure. Table 1-1 lists every block: APB interconnect and bridges, ATB funnel, replicator, upsizer, downsizer and bridges, timestamp components, cross-trigger, TPIU, ETB and the debug access ports.

## Where the sources agree

- Width converters must not merge or repack data that the attributes forbid touching. The AXI spec states this for Non-modifiable transactions (AXI-L §A4.2.2), and NIC-400 implements it for non-cacheable ones (NIC400-J §2.3.3–2.3.4).
- AXI4 has no locked transfers. NIC-400's AXI3-to-AXI4 conversion note says "you must only use exclusive atomic accesses to access an AXI4 slave from an AXI3 master" (NIC400-J §2.3.1), which matches AXI-C §13.15.
- Bridges between clock and power domains use the LPI handshakes. The CoreSight APB and ATB bridges each "provides an LPI" (CSSOC-F §2.2.2, §2.3.5), and LPI-D §2.1 says the handshake is safe across asynchronous domains.

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Role names | The product manuals (CMSDK-C, NIC400-J, CSSOC-F, 2011–2017) say **master** and **slave** | AHB-C and AXI-J onwards say **Manager** and **Subordinate**; APB-E says **Requester** and **Completer** | A terminology change, not a technical one. The manuals predate the renaming. See [Terminology and roles](terminology-and-roles.md) |
| Register slices in trace | AXI-L §A2.5: register slices may go on any AXI channel | CSSOC-F §8.5: "There is no register slice component" for cross-trigger paths; "You can place additional registers on these paths" | Not a conflict. AXI permits them and products supply them, while CoreSight SoC-400 leaves cross-trigger pipelining to the integrator |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Every APB or AHB island needs a default response for unmapped addresses: ERROR for real transfers, zero-wait OKAY for IDLE and BUSY, as CMSDK's default slave does (CMSDK-C §3.1).
- Before writing an adapter, list what changes across the border (protocol, width, clock, IDs, burst shape) and handle each one in a separate, testable stage.
- A downsizer or splitter must check AxCACHE[1] before touching a transaction (AXI-L §A4.2.2).
- Splitting an exclusive transaction destroys its exclusivity: when NIC-400's upsizer splits one, it "removes the exclusive information from the multiple transactions it creates" (NIC400-J §2.3.3). *Editor's note (not from the sources): the likely effect is that the exclusive sequence fails instead of silently losing atomicity, so keep exclusive accesses within one output beat where you can.*
- Put a timeout monitor in front of any third-party Subordinate that could hang the bus (CMSDK-C §3.9, §4.8).
- For learning, write three modules yourself: an APB → register block, an AXI4-Lite → register block, and an AHB → APB bridge. Together they exercise most of the handshake, response and phase rules in this wiki.

## Related articles

- [Interconnect, topology and bridges](interconnect-topology-and-bridges.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Bursts, sizes, alignment and write strobes](bursts-sizes-and-alignment.md)
- [Memory types and cache attributes](memory-types-and-cache-attributes.md)
- [Responses and error signalling](responses-and-errors.md)
- [Low power and wake-up](low-power-and-wakeup.md)
- [Streaming interfaces](streaming-interfaces.md)
- [Debug trace: ATB](debug-trace-atb.md)
- [Networks-on-chip (NoC)](networks-on-chip.md)

## Sources

AMBA2, APB-B, APB-E, AHB-C, AXI-C, AXI-L, AXIS-B, CHI-H, LPI-D, ATB-C, DTI-E, CMSDK-C, NIC400-J, CSSOC-F. See [Source key](sources.md).

### Web references (not specifications; read 2026-11-22)

These are component catalogues, cited only for module names and their one-line descriptions. They are not part of the audited source set.

| Code | Reference |
|---|---|
| W-PULP | PULP Platform `axi` library README, [github.com/pulp-platform/axi](https://github.com/pulp-platform/axi) (Solderpad Hardware License, per the README badge) |
| W-VAXI | Alex Forencich `verilog-axi` README, [github.com/alexforencich/verilog-axi](https://github.com/alexforencich/verilog-axi). The README says it "is superseded by https://github.com/fpganinja/taxi" and is deprecated |
| W-VAXIS | Alex Forencich `verilog-axis` README, [github.com/alexforencich/verilog-axis](https://github.com/alexforencich/verilog-axis), with the same deprecation notice |
| W-SNPS | Synopsys DesignWare AMBA fabric page, [synopsys.com](https://www.synopsys.com/designware-ip/soc-infrastructure-ip/amba/amba-fabric.html) |
| W-AMD | AMD product guides: AXI Interconnect [PG059](https://docs.amd.com/r/en-US/pg059-axi-interconnect/AXI-Infrastructure-Cores), SmartConnect [PG247](https://docs.amd.com/r/en-US/pg247-smartconnect), AXI4-Stream Infrastructure [PG085](https://docs.amd.com/r/en-US/pg085-axi4stream-infrastructure), AXI to APB Bridge [PG073](https://docs.amd.com/r/en-US/pg073-axi-apb-bridge), AXI DataMover [PG022](https://docs.amd.com/r/en-US/pg022_axi_datamover), AXI4-Stream FIFO [PG080](https://docs.amd.com/r/en-US/pg080-axi-fifo-mm-s) |
