# Generic Flash Bus (GFB)

> A simple point-to-point command interface between a reusable, generic flash controller and a process-specific embedded-flash (eFlash) macro wrapper.

## In plain words

Embedded flash differs for every silicon process: timings, page sizes and programming sequences all change. Arm splits the flash controller into two halves:
- a **generic** part (the Manager), for example Arm CoreLink GFC-100/200, which is the same in every chip,
- a **process-specific** part (the Subordinate) that knows the real flash macro.

**GFB** is the small, standard interface between the two halves. Changing process then only means replacing the Subordinate side (GFB-Ab §1.1; G-SYS §4.4.2). GFB carries the *data path*. Control and configuration go over other interfaces.

## Signals (GFB-Ab Table 2-1)

| Signal | From | Purpose |
|---|---|---|
| `FCLK`, `FRESETn` | system | Clock. Active-LOW reset (asynchronous assert, synchronous deassert) |
| `FCMD[2:0]` | Manager | Command |
| `FADDR` | Manager | Address. `FADDR_WIDTH` ≥ 12 recommended |
| `FWDATA` | Manager | Write data. A power of two, ≥ 32 bits recommended |
| `FABORT` | Manager (optional) | Request to cancel a long command |
| `FRDATA` | Subordinate | Read data. Its width may differ from FWDATA |
| `FREADY` | Subordinate | HIGH = previous command done and ready for the next |
| `FRESP` | Subordinate | Error |

## Commands (GFB-Ab §3.1)

| Command | Meaning |
|---|---|
| IDLE | Nothing to do |
| READ | Full-width read at FADDR |
| WRITE | Program one full-width word |
| ROW WRITE | Like WRITE, but a hint to keep programming active if the next command is also a ROW WRITE |
| ERASE | Erase the page containing FADDR. Can take millions of FCLK cycles |
| MASS ERASE | Erase everything mapped to the interface |

Encodings 0b101 and 0b110 are invalid.

## Protocol rules (GFB-Ab §3.3)

- A command is **accepted** in the cycle FCMD ≠ IDLE and FREADY is HIGH. It is then ongoing until the next FREADY HIGH, which is AHB-like pipelining with separate address and data phases.
- While FREADY is LOW, FCMD, FADDR and FWDATA must hold.
- **Errors take two cycles**: (FREADY=0, FRESP=1) then (FREADY=1, FRESP=1). After an error on WRITE, ERASE or the like, the memory content is UNDEFINED.
- A Subordinate need not support every command. It may answer unsupported ones with an error.
- **Abort**: the Manager may raise FABORT during an ongoing command. The Subordinate may ignore it or end the command with an error response.
- **Housekeeping**: the Subordinate may hold FREADY LOW for initialisation, self-test and similar work, even after accepting IDLE.

## Where the sources agree

- GFB is point-to-point, with one Manager and one Subordinate (GFB-Ab §1.1; G-SYS §4.4.2).
- Like AHB and APB, it uses a ready signal for wait states and a two-cycle error response (compare [Responses and errors](responses-and-errors.md)).

## Where the sources disagree (and why)

No substantive disagreements were found between GFB-A, GFB-Ab and G-SYS. Issue A.b is a minor update of Issue A (2018 → 2022). GFB borrows AHB-style ideas (pipelined address/data phases, wait states through a ready signal, two-cycle error) but is **not** AHB-compatible: it has commands and aborts, and no bursts, sizes or strobes.

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Keep `FWDATA` stable for the whole (possibly very long) data phase of a WRITE: "The Manager must keep FWDATA stable through this period" (GFB-Ab §3.2).
- FABORT may be asserted only while a non-IDLE command is ongoing, and must stay HIGH while FREADY is LOW. The Subordinate may ignore the request, or accept it and give an error response. An abort raised in the same cycle as FREADY HIGH is ignored (GFB-Ab §3.3). *Editor's note (not from the sources): what an aborted ERASE leaves in the Flash array is macro-specific, so check the Flash macro documentation.*

## Protocol assertions

SystemVerilog assertions for the rules in GFB-Ab §3.3. They come from `assertions/atb_gfb_checker.sv` (module `gfb_checker`) in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository, which also has a test for every assertion. The checker tracks the *ongoing* command: the one accepted at the last edge where FREADY was HIGH ("A command is then ongoing until the next cycle when FREADY is HIGH", GFB-Ab §3.3).

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.**

| Assertion | Rule | Source |
|---|---|---|
| `gfb_reset` | During reset FCMD is IDLE, and FABORT, FREADY and FRESP are LOW | GFB-Ab §3.3.3 |
| `gfb_cmd_legal` | FCMD is never 0b101 or 0b110 | GFB-Ab §3.3, Table 2-1 |
| `gfb_cmd_stable` | A non-IDLE FCMD, and FADDR, do not change while FREADY and FRESP are LOW | GFB-Ab §3.3 |
| `gfb_wdata_stable` | Active FWDATA does not change while FREADY and FRESP are LOW | GFB-Ab §3.3 |
| `gfb_addr_aligned` | FADDR aligned to the read data width for READ, and to the write data width for WRITE and ROW WRITE | GFB-Ab §3.3 |
| `gfb_error_two_cycle` | "If FRESP is HIGH and FREADY is LOW, then FRESP must be HIGH and FREADY must be HIGH in the next cycle" | GFB-Ab §3.3 |
| `gfb_resp_needs_cmd` | "FRESP can only be asserted if there is an ongoing non-IDLE command" | GFB-Ab §3.3 |
| `gfb_abort_needs_cmd`, `gfb_abort_held` | FABORT only during an ongoing non-IDLE command, and held while FREADY is LOW | GFB-Ab §3.3 |

```systemverilog
// GFB-Ab §3.3: command accepted when FREADY is HIGH, ongoing until the next FREADY HIGH
always_ff @(posedge FCLK)
  if (!FRESETn)    ongoing <= IDLE;
  else if (FREADY) ongoing <= FCMD;

// GFB-Ab §3.3: hold the command and address while waiting
gfb_cmd_stable: assert property (@(posedge FCLK) disable iff (!FRESETn)
    ((FCMD != IDLE) && !FREADY && !FRESP) |=> $stable(FCMD) && $stable(FADDR));

// GFB-Ab §3.3: a two-cycle error response, only for an ongoing command
gfb_error_two_cycle: assert property (@(posedge FCLK) disable iff (!FRESETn)
    (FRESP && !FREADY) |=> (FRESP && FREADY));
gfb_resp_needs_cmd: assert property (@(posedge FCLK) disable iff (!FRESETn)
    FRESP |-> (ongoing != IDLE));
```

Not covered: FRDATA and FWDATA legality, housekeeping, and which commands a Subordinate supports.

## Related articles

- [Transfer phases and pipelining](transfer-phases-and-pipelining.md)
- [Responses and errors](responses-and-errors.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)

## Sources

GFB-A, GFB-Ab, G-SYS. See [Source key](sources.md).
