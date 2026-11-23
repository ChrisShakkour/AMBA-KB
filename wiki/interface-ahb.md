# AHB interface hub

> Everything about one AHB (AHB-Lite / AHB5) interface on one page: every signal, a transfer in brief, the rules a design must follow, and protocol assertions. Each line links to the concept article that explains it in depth. This page summarises; it does not replace those articles.

## In plain words

AHB is a pipelined bus: the **address phase** of one transfer overlaps the **data phase** of the previous one (AHB-C §3.1). One Manager drives address and control. A decoder selects one Subordinate with `HSELx`, and a multiplexor returns the selected Subordinate's `HRDATA`, `HREADYOUT` (as `HREADY`) and `HRESP` (AHB-C §2.4–2.5, §4). Wait states stretch the data phase, and errors take two cycles so the Manager can cancel the transfer already on the bus (AHB-C §5.1.3).

## Signals

From AHB-C Tables 2-1 to 2-5 (meaning) and Table A-2 (presence on Manager and Subordinate interfaces). Presence codes: **Y** mandatory, **O** optional, **C** present if the named property is True, **OC** optional, and allowed only if the property is True, **N** not present (AHB-C Appendix A).

| Signal | Source | Width | Presence (Manager / Subordinate) | Default if absent | Meaning | Explained in |
|---|---|---|---|---|---|---|
| `HCLK` | Clock source | 1 | Y / Y | — | Clock; all timing relates to its rising edge | [Transfer phases](transfer-phases-and-pipelining.md#ahb-address-phase-overlaps-the-previous-data-phase) |
| `HRESETn` | Reset controller | 1 | Y / Y | — | Active-LOW reset, "the only active LOW signal" | |
| `HADDR` | Manager | `ADDR_WIDTH` (10–64 recommended) | Y / Y | — | Byte address of the transfer | [Bursts and alignment](bursts-sizes-and-alignment.md) |
| `HBURST` | Manager | `HBURST_WIDTH` (0 or 3) | O / O | `0x1` (INCR) | Burst type and length | [Bursts](bursts-sizes-and-alignment.md#burst-encodings-side-by-side) |
| `HMASTLOCK` | Manager | 1 | O / O | `0b0` | Transfer is part of a locked sequence | [Locked transfers](exclusive-locked-and-atomic-access.md#1-locked-transfers) |
| `HPROT` | Manager | `HPROT_WIDTH` (0, 4 or 7) | O / O | `0x03` | Protection and memory type; width set by `Extended_Memory_Types` | [Memory types: HPROT](memory-types-and-cache-attributes.md#ahb-hprot-ahb-c-3839) |
| `HSIZE` | Manager | 3 | Y / Y | — | Transfer size | [Bursts: size](bursts-sizes-and-alignment.md#size) |
| `HNONSEC` | Manager | 1 | C (`Secure_Transfers`) | `0b0` | Non-secure (HIGH) or Secure transfer | [Protection and security](protection-and-security.md#the-signals) |
| `HEXCL` | Manager | 1 | C (`Exclusive_Transfers`) | `0b0` | Transfer is part of an Exclusive Access sequence | [Exclusive access](exclusive-locked-and-atomic-access.md#2-exclusive-access) |
| `HMASTER` | Manager | `HMASTER_WIDTH` (0–8 recommended) | C (`Exclusive_Transfers`) | 0 | Manager identifier for the exclusive monitor | [Exclusive access](exclusive-locked-and-atomic-access.md#2-exclusive-access) |
| `HTRANS[1:0]` | Manager | 2 | Y / Y | — | IDLE, BUSY, NONSEQ or SEQ | [Transfer phases](transfer-phases-and-pipelining.md#ahb-address-phase-overlaps-the-previous-data-phase) |
| `HWDATA` | Manager | `DATA_WIDTH` (8–1024; 32–256 recommended) | Y / Y | — | Write data, in the data phase | |
| `HWSTRB` | Manager | `DATA_WIDTH/8` | C (`Write_Strobes`) | all ones | Write strobes; data-phase signal | [Bursts: write strobes](bursts-sizes-and-alignment.md#write-strobes) |
| `HWRITE` | Manager | 1 | Y / Y | — | HIGH = write; constant throughout a burst | |
| `HSELx` | Decoder | 1 | N / Y | — | Selects this Subordinate | [Interconnect](interconnect-topology-and-bridges.md) |
| `HRDATA` | Subordinate → multiplexor | `DATA_WIDTH` | Y / Y | — | Read data | |
| `HREADYOUT` | Subordinate | 1 | N / Y | — | This Subordinate's "transfer has finished"; LOW extends the transfer | [Handshakes](handshakes-and-flow-control.md#1-wait-state-style) |
| `HREADY` | Multiplexor | 1 | Y / Y | — | Bus-wide "previous transfer is complete", seen by the Manager and all Subordinates | [Handshakes](handshakes-and-flow-control.md#1-wait-state-style) |
| `HRESP` | Subordinate → multiplexor | 1 | Y / Y | — | LOW = OKAY, HIGH = ERROR | [Responses and errors](responses-and-errors.md#timing-why-ahb-errors-take-two-cycles) |
| `HEXOKAY` | Subordinate → multiplexor | 1 | C (`Exclusive_Transfers`) | — | Exclusive transfer succeeded | [Exclusive access](exclusive-locked-and-atomic-access.md#2-exclusive-access) |
| `HAUSER`, `HWUSER`, `HRUSER`, `HBUSER` | Manager (A, W) / Subordinate (R, B) | `USER_*_WIDTH` | OC / OC | — | User extensions | [User signals](interface-properties-and-user-signals.md#user-signals) |
| `H*CHK` (parity) | Both | per payload | C (`Check_Type`) | — | Interface parity (AHB-C ch. 12) | [Parity and RAS](interface-protection-parity-and-ras.md#parity-check-signals) |

## A transfer in brief

```
cycle:        1            2            3
address:   A (NONSEQ)   B (NONSEQ)   C ...
data:          -        data A       data B      HREADY HIGH each cycle: no wait states
```

- A transfer is sampled when `HSELx` and `HREADY` are both HIGH. "A Subordinate must only sample the HSELx, address, and control signals when HREADY is HIGH" (AHB-C §4.2).
- Write data (`HWDATA`, `HWSTRB`) belongs to the data phase, one cycle after its address phase.
- `HREADYOUT` LOW adds wait states. The Manager then holds its next address phase, with limited exceptions (AHB-C §3.7).
- ERROR takes two cycles: `HRESP` HIGH with `HREADYOUT` LOW, then `HRESP` HIGH with `HREADYOUT` HIGH (AHB-C §5.1.3).

See [Transfer phases](transfer-phases-and-pipelining.md#ahb-address-phase-overlaps-the-previous-data-phase) and [Responses and errors](responses-and-errors.md#timing-why-ahb-errors-take-two-cycles).

## Key rules checklist

| # | Rule | Source | Explained in |
|---|---|---|---|
| 1 | IDLE and BUSY transfers get "a zero wait state OKAY response" and are ignored by the Subordinate | AHB-C §3.2 | [Transfer phases](transfer-phases-and-pipelining.md#ahb-address-phase-overlaps-the-previous-data-phase) |
| 2 | Only undefined-length bursts may end with BUSY; fixed-length bursts end with SEQ; no BUSY straight after a SINGLE burst | AHB-C §3.2, §3.6.2 | [Bursts](bursts-sizes-and-alignment.md) |
| 3 | HSIZE must not exceed the data bus width | AHB-C §3.4 | [Bursts: size](bursts-sizes-and-alignment.md#size) |
| 4 | HWRITE, HSIZE, HPROT and HNONSEC stay constant throughout a burst | AHB-C §2.2, §3.4, §3.8, §3.10 | [Bursts](bursts-sizes-and-alignment.md) |
| 5 | Transfers are aligned to their size, and incrementing bursts must not cross a 1KB boundary | AHB-C §3.6.1 | [Interconnect: decode granules](interconnect-topology-and-bridges.md#decode-granules-why-1-kb-and-4-kb-matter) |
| 6 | During wait states the Manager must not change the transfer type, except IDLE→NONSEQ and the BUSY cases; once NONSEQ or SEQ, HTRANS and the address stay constant until HREADY is HIGH | AHB-C §3.7.1–3.7.2 | [Transfer phases](transfer-phases-and-pipelining.md#ahb-address-phase-overlaps-the-previous-data-phase) |
| 7 | A Subordinate inserting wait states drives HRESP OKAY | AHB-C §5.1 | [Responses and errors](responses-and-errors.md) |
| 8 | ERROR is a two-cycle response | AHB-C §5.1.3 | [Responses and errors](responses-and-errors.md#timing-why-ahb-errors-take-two-cycles) |
| 9 | After an ERROR the Manager may cancel the rest of the burst, but must then drive IDLE | AHB-C §3.6.2, §5.1.3 | [Responses and errors](responses-and-errors.md) |
| 10 | During reset, Managers drive HTRANS IDLE and Subordinates drive HREADYOUT HIGH | AHB-C §7.1 | |
| 11 | HSELx for a non-IDLE transfer is asserted with the address phase; a memory map with gaps needs a default Subordinate | AHB-C §2.4, §4.2 | [Bridges: default slave](bridges-and-adapters.md) |
| 12 | Validity: HTRANS, HADDR, HSEL, HMASTLOCK, HREADY, HREADYOUT and HRESP always; HBURST, HPROT, HSIZE, HNONSEC, HEXCL, HMASTER, HWRITE and HAUSER when HTRANS is not IDLE; HWDATA, HWSTRB and HWUSER in a write's data phase | AHB-C §8.2 | |

## Protocol assertions

SystemVerilog assertions for rules 1, 3–6, 8, 10 and 12. They come from `assertions/ahb_checker.sv` in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository, which also has a test for every assertion. There are two checker modules: `ahb_manager_checker` (Manager outputs plus the HREADY and HRESP it sees) and `ahb_subordinate_checker` (one Subordinate's HSEL, HREADYOUT and HRESP).

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.** Treat these as reviewed drafts until `python assertions/run_tests.py ahb` passes.

| Assertion | Side | Rule | Source |
|---|---|---|---|
| `ahb_mgr_reset_idle` | Manager | HTRANS is IDLE during reset | AHB-C §7.1 |
| `ahb_mgr_wait_stable` | Manager | NONSEQ/SEQ: HTRANS and HADDR stable while HREADY is LOW (not during ERROR) | AHB-C §3.7.1–3.7.2 |
| `ahb_mgr_size_le_bus` | Manager | HSIZE ≤ bus width | AHB-C §3.4 |
| `ahb_mgr_aligned` | Manager | Address aligned to HSIZE | AHB-C §3.6.1 |
| `ahb_mgr_1kb` | Manager | Incrementing bursts stay inside one 1KB region | AHB-C §3.6.1 |
| `ahb_mgr_burst_const` | Manager | HWRITE, HSIZE and HPROT constant within a burst | AHB-C §2.2, §3.4, §3.8 |
| `ahb_sub_idle_busy_okay` | Subordinate | IDLE/BUSY get zero-wait OKAY | AHB-C §3.2 |
| `ahb_sub_error_two_cycle` | Subordinate | First ERROR cycle is followed by the final one | AHB-C §5.1.3 |
| `ahb_sub_error_first_cycle` | Subordinate | Final ERROR cycle is preceded by the first one | AHB-C §5.1.3 |
| `ahb_sub_reset_hreadyout` | Subordinate | HREADYOUT HIGH during reset | AHB-C §7.1 |
| `ahb_mgr_valid`, `ahb_sub_valid` | Both | No X/Z when a signal must be valid (4-state simulators only) | AHB-C §8.2 |

```systemverilog
// ---- Subordinate side
// AHB-C §3.2: zero wait state OKAY response to IDLE and BUSY transfers
ahb_sub_idle_busy_okay: assert property (@(posedge HCLK) disable iff (!HRESETn)
    (HSEL && HREADY && !HTRANS[1]) |=> (HREADYOUT && !HRESP));

// AHB-C §5.1.3: ERROR takes two cycles: (HRESP=1, HREADYOUT=0) then (HRESP=1, HREADYOUT=1)
ahb_sub_error_two_cycle: assert property (@(posedge HCLK) disable iff (!HRESETn)
    (HRESP && !HREADYOUT) |=> (HRESP && HREADYOUT));
ahb_sub_error_first_cycle: assert property (@(posedge HCLK) disable iff (!HRESETn)
    (HRESP && HREADYOUT) |-> $past(HRESP && !HREADYOUT));

// AHB-C §7.1: HREADYOUT HIGH during reset (rst_q: reset was also LOW at the previous edge)
ahb_sub_reset_hreadyout: assert property (@(posedge HCLK)
    (!HRESETn && rst_q) |-> HREADYOUT);

// ---- Manager side
// AHB-C §3.7: a waited NONSEQ/SEQ transfer keeps HTRANS and HADDR; ERROR (HRESP=1) excluded
ahb_mgr_wait_stable: assert property (@(posedge HCLK) disable iff (!HRESETn)
    (HTRANS[1] && !HREADY && !HRESP) |=> $stable(HTRANS) && $stable(HADDR));

// AHB-C §3.6.1: aligned to size; incrementing bursts do not cross 1KB
ahb_mgr_aligned: assert property (@(posedge HCLK) disable iff (!HRESETn)
    HTRANS[1] |-> ((HADDR & ((ADDR_WIDTH'(1) << HSIZE) - 1)) == '0));
ahb_mgr_1kb: assert property (@(posedge HCLK) disable iff (!HRESETn)
    (HTRANS == SEQ && HREADY && incr_burst(burst_q)) |->
      (HADDR[ADDR_WIDTH-1:10] == addr_q[ADDR_WIDTH-1:10]));
```

`addr_q` and `burst_q` hold the last accepted NONSEQ/SEQ transfer. See the checker file for the full code.

*Editor's note (not from the sources):*
- *`ahb_mgr_wait_stable` covers only the NONSEQ/SEQ case of rule 6. The IDLE and BUSY exceptions, and "the Manager can only change the address once", need more state and are not checked.*
- *The reset checks skip the first reset cycle, so a synchronously reset design is not flagged before its first reset clock edge.*

Not covered: locked transfers, exclusives, BUSY rules, user signals and parity.

## Versions

AHB (AMBA 2, with arbitration and SPLIT/RETRY) → AHB-Lite (one Manager, 1-bit HRESP) → AHB5 Issue B (extended memory types, HNONSEC, exclusives, user signals) → Issue C (width properties, HWSTRB, parity, signal-validity rules). Details: [Protocol evolution: AHB](protocol-evolution-and-versions.md#ahb-ahb-c-12-appendix-b).

## Related articles

- [Transfer phases and pipelining](transfer-phases-and-pipelining.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Responses and error signalling](responses-and-errors.md)
- [Bursts, sizes, alignment and write strobes](bursts-sizes-and-alignment.md)
- [Interconnect, topology and bridges](interconnect-topology-and-bridges.md)
- [Bridges, adapters and converters](bridges-and-adapters.md)
- [APB interface hub](interface-apb.md)
- [AXI interface hub](interface-axi.md)

## Sources

AHB-C (Tables 2-1 to 2-5, Appendix A, §3.1–3.10, §4.2, §5.1, §7.1, §8.2). See [Source key](sources.md).
