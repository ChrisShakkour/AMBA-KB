# APB interface hub

> Everything about one APB interface on one page: every signal, a transfer in brief, the rules a design must follow, and protocol assertions. Each line links to the concept article that explains it in depth. This page summarises; it does not replace those articles.

## In plain words

APB is the simplest AMBA bus, made for low-bandwidth register access behind a bridge (APB-E §1.1). One **Requester** (normally a bridge from AHB or AXI) talks to one or more **Completers** (peripherals), selecting each with its own `PSELx`. "The APB interface is not pipelined" and every transfer takes at least two cycles: SETUP, then ACCESS (APB-E §1.1, §4.1).

## Signals

From APB-E Table 2-1 (meaning) and Table B-1 (which APB version has the signal). Presence codes: **Y** mandatory, **O** optional, **OO** optional for outputs but mandatory for inputs, **C** present if the named property is True, **OC** optional, and allowed only if the property is True, **N** not present (APB-E Appendix B).

| Signal | Source | Width | APB5 / APB4 / APB3 / APB2 | Meaning | Explained in |
|---|---|---|---|---|---|
| `PCLK` | Clock | 1 | Y / Y / Y / Y | Clock; all signals are timed against its rising edge | [Transfer phases](transfer-phases-and-pipelining.md#apb-setup-then-access) |
| `PRESETn` | System bus reset | 1 | Y / Y / Y / Y | Active-LOW reset | |
| `PADDR` | Requester | `ADDR_WIDTH` (up to 32) | Y / Y / Y / Y | Byte address. May be unaligned, but the result is UNPREDICTABLE (APB-E §2.1.1) | [Bursts and alignment](bursts-sizes-and-alignment.md) |
| `PPROT[2:0]` | Requester | 3 | O / O / N / N | Normal/privileged, Secure/Non-secure, data/instruction | [Protection and security](protection-and-security.md#the-signals) |
| `PNSE` | Requester | 1 | C (`RME_Support`) / N / N / N | Extends PPROT for RME physical address spaces | [Protection and security](protection-and-security.md#physical-address-space-encodings) |
| `PSELx` | Requester | 1 | Y / Y / Y / Y | One select per Completer: "a data transfer is required" | [Transfer phases](transfer-phases-and-pipelining.md#apb-setup-then-access) |
| `PENABLE` | Requester | 1 | Y / Y / Y / Y | "the second and subsequent cycles of an APB transfer" | [Transfer phases](transfer-phases-and-pipelining.md#apb-setup-then-access) |
| `PWRITE` | Requester | 1 | Y / Y / Y / Y | HIGH = write, LOW = read | |
| `PWDATA` | Requester | `DATA_WIDTH` (8, 16 or 32) | Y / Y / Y / Y | Write data | |
| `PSTRB` | Requester | `DATA_WIDTH/8` | O / O / N / N | Write strobes, one per byte lane; all LOW on reads | [Bursts: write strobes](bursts-sizes-and-alignment.md#write-strobes) |
| `PREADY` | Completer | 1 | OO / OO / OO / N | Extends a transfer (wait states) | [Handshakes: wait-state style](handshakes-and-flow-control.md#1-wait-state-style) |
| `PRDATA` | Completer | `DATA_WIDTH` | Y / Y / Y / Y | Read data | |
| `PSLVERR` | Completer | 1 | OO / OO / OO / N | Transfer error, valid only in the last ACCESS cycle | [Responses and errors](responses-and-errors.md) |
| `PWAKEUP` | Requester | 1 | C (`Wakeup_Signal`) / N / N / N | Activity on the interface; glitch-free | [Low power: wake-up signals](low-power-and-wakeup.md#wake-up-signals-on-bus-interfaces) |
| `PAUSER`, `PWUSER`, `PRUSER`, `PBUSER` | Requester (A, W) / Completer (R, B) | `USER_*_WIDTH` | OC / N / N / N | User extensions. "Generally, it is recommended that User signals are not used" (APB-E §3.8) | [User signals](interface-properties-and-user-signals.md#user-signals) |
| `P*CHK` (parity) | Both | per payload | C (`Check_Type`) / N / N / N | Interface parity, APB5 only (APB-E Table B-2) | [Parity and RAS](interface-protection-parity-and-ras.md#parity-check-signals) |

## A transfer in brief

```
IDLE --(transfer)--> SETUP  PSEL=1 PENABLE=0   (exactly 1 cycle)
SETUP ------------> ACCESS  PSEL=1 PENABLE=1   (repeats while PREADY=0)
ACCESS --(PREADY=1)--> IDLE, or straight to SETUP for the next transfer
```

The state machine is APB-E §4.1. A write or read completes in the ACCESS cycle in which `PREADY` is HIGH. See [Transfer phases and pipelining](transfer-phases-and-pipelining.md#apb-setup-then-access) for timing diagrams in words, and [Handshakes](handshakes-and-flow-control.md#1-wait-state-style) for wait states.

## Key rules checklist

| # | Rule | Source | Explained in |
|---|---|---|---|
| 1 | SETUP lasts one cycle and always moves to ACCESS | APB-E §4.1 | [Transfer phases](transfer-phases-and-pipelining.md#apb-setup-then-access) |
| 2 | PADDR, PPROT, PWRITE, PWDATA (writes), PSTRB, PAUSER and PWUSER must not change from SETUP to ACCESS, or during ACCESS | APB-E §4.1 | [Transfer phases](transfer-phases-and-pipelining.md#apb-setup-then-access) |
| 3 | While PREADY is LOW the interface stays in ACCESS | APB-E §4.1 | [Handshakes](handshakes-and-flow-control.md#1-wait-state-style) |
| 4 | The Requester must drive all PSTRB bits LOW for reads | APB-E §3.2 | [Bursts: write strobes](bursts-sizes-and-alignment.md#write-strobes) |
| 5 | PSLVERR "is only considered valid during the last cycle of an APB transfer, when PSEL, PENABLE, and PREADY are all HIGH". Driving it LOW at other times is recommended, not required | APB-E §3.4.1 | [Responses and errors](responses-and-errors.md) |
| 6 | A transfer that gets an error "might or might not have changed the state of the peripheral" | APB-E §3.4.1 | [Responses and errors](responses-and-errors.md#what-happens-to-state-and-data-on-error) |
| 7 | A bridge maps PSLVERR to SLVERR (AXI) or ERROR (AHB) | APB-E §3.4.3 | [Bridges and adapters](bridges-and-adapters.md) |
| 8 | PWAKEUP must stay asserted until PREADY if PWAKEUP and PSELx are HIGH in the same cycle. A Completer may wait for PWAKEUP before asserting PREADY | APB-E §3.7 | [Low power](low-power-and-wakeup.md#wake-up-signals-on-bus-interfaces) |
| 9 | If PNSE is present, PPROT must also be present | APB-E §3.6.2 | [Protection and security](protection-and-security.md) |
| 10 | Validity: PSEL and PWAKEUP are always valid; PADDR, PPROT, PNSE, PENABLE, PWRITE, PAUSER, PSTRB and PWDATA when PSEL is HIGH; PREADY when PSEL and PENABLE are HIGH; PRDATA, PSLVERR, PRUSER and PBUSER when PSEL, PENABLE and PREADY are HIGH. "It is recommended that signals which are not required to be valid are driven to zero" | APB-E Appendix A.1 | |

Rule 2 means PENABLE without PSEL is not an error in itself: PENABLE only has to be valid when PSEL is HIGH (APB-E Appendix A.1).

## Protocol assertions

SystemVerilog assertions for rules 1–5, 8 and 10. Each one names the rule it encodes. They come from `assertions/apb_checker.sv` in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository. That repository also has a test for every assertion: legal traffic that must not trigger it, and an injected violation that must.

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.** Treat these as reviewed drafts until `python assertions/run_tests.py apb` passes.

| Assertion | Rule | Source |
|---|---|---|
| `apb_setup_to_access` | SETUP is followed by ACCESS | APB-E §4.1 |
| `apb_ctrl_stable` | Control and write data stable from SETUP through ACCESS | APB-E §4.1 |
| `apb_wait_holds_access` | PREADY LOW keeps the interface in ACCESS | APB-E §4.1 |
| `apb_access_exits` | After PREADY HIGH, the next cycle is not ACCESS | APB-E §4.1 |
| `apb_pstrb_read_low` | PSTRB all LOW for reads | APB-E §3.2 |
| `apb_pwakeup_held` | PWAKEUP held until PREADY once PSEL is HIGH (only if `Wakeup_Signal`) | APB-E §3.7 |
| `apb_valid_*` | No X/Z when a signal must be valid (4-state simulators only) | APB-E A.1 |
| `apb_pslverr_low_rec` | PSLVERR LOW outside the last cycle. A **recommendation**, off by default | APB-E §3.4.1 |

```systemverilog
wire setup  = PSEL && !PENABLE;
wire access = PSEL &&  PENABLE;
wire last   = access && PREADY;

// APB-E §4.1: SETUP lasts one cycle and always moves to ACCESS
apb_setup_to_access: assert property (@(posedge PCLK) disable iff (!PRESETn)
    setup |=> access);

// APB-E §4.1: control signals must not change SETUP->ACCESS or during ACCESS
apb_ctrl_stable: assert property (@(posedge PCLK) disable iff (!PRESETn)
    (setup || (access && !PREADY)) |=>
      $stable(PADDR) && $stable(PPROT) && $stable(PWRITE) && $stable(PSTRB) &&
      (!PWRITE || $stable(PWDATA)));

// APB-E §4.1: PREADY LOW keeps the interface in ACCESS
apb_wait_holds_access: assert property (@(posedge PCLK) disable iff (!PRESETn)
    (access && !PREADY) |=> access);

// APB-E §4.1: with PREADY HIGH the ACCESS state is exited
apb_access_exits: assert property (@(posedge PCLK) disable iff (!PRESETn)
    last |=> !access);

// APB-E §3.2: PSTRB must be all LOW for reads
apb_pstrb_read_low: assert property (@(posedge PCLK) disable iff (!PRESETn)
    (PSEL && !PWRITE) |-> (PSTRB == '0));

// APB-E §3.7: PWAKEUP held until PREADY if PWAKEUP and PSEL are HIGH together
apb_pwakeup_held: assert property (@(posedge PCLK) disable iff (!PRESETn)
    (PWAKEUP && PSEL && !last) |=> PWAKEUP);
```

*Editor's note (not from the sources): `apb_pwakeup_held` reads "until PREADY is asserted" as meaning until the last ACCESS cycle, because PREADY is only sampled in ACCESS (APB-E §4.1).*

Not covered: user signals, PNSE, parity, and anything that depends on a Completer's address map.

## Versions

APB2 (AMBA 2) → APB3 adds `PREADY` and `PSLVERR` → APB4 adds `PPROT` and `PSTRB` → APB5 adds `PWAKEUP`, user signals, parity and width properties (Issue D), then `PNSE` for RME (Issue E). Details: [Protocol evolution: APB](protocol-evolution-and-versions.md#apb-apb-e-preface--appendix-c).

## Related articles

- [Transfer phases and pipelining](transfer-phases-and-pipelining.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Responses and error signalling](responses-and-errors.md)
- [Bridges, adapters and converters](bridges-and-adapters.md)
- [AHB interface hub](interface-ahb.md)
- [AXI interface hub](interface-axi.md)

## Sources

APB-E (Table 2-1, Appendices A and B, §1.1, §2.1, §3.2, §3.4, §3.6, §3.7, §3.8, §4.1). See [Source key](sources.md).
