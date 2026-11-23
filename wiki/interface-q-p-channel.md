# Q-Channel and P-Channel interface hub

> Everything about the two AMBA low-power interfaces on one page: their signals, their handshake states, the exact transition rules, and protocol assertions. Each line links to the concept article that explains it in depth. This page summarises; it does not replace [Low power and wake-up](low-power-and-wakeup.md).

## In plain words

Both interfaces connect a **device** to a clock or power **controller**. The controller asks, and the device accepts or denies (LPI-D ch. 2–3):
- **Q-Channel** asks a device to become *quiescent*, so its clock or power can be removed. It is "an evolution of the AXI low-power interface" (LPI-D §2.1.1).
- **P-Channel** asks a device to move to a power state given on `PSTATE`.

The handshakes are built so that only one acknowledgement signal changes per step, which "ensures that the interface can be implemented safely across asynchronous boundaries". "All signals are assumed to be asynchronous" (LPI-D §2.1.1, §3.1).

## Q-Channel signals

From LPI-D §2.1.1.

| Signal | Driven by | Meaning | Rules |
|---|---|---|---|
| `QREQn` | Controller | Quiescence request (LOW = request) | Driven by a register |
| `QACCEPTn` | Device | Accepts the request (LOW = accepted) | Driven by a register |
| `QDENY` | Device | Denies the request (HIGH = denied) | Driven by a register. May be omitted, then tied LOW at the controller (LPI-D §2.1.4) |
| `QACTIVE` | Device | The device has operations to perform; a hint, not part of the handshake | May be omitted, then tied LOW at the controller (LPI-D §2.1.4) |

### Q-Channel states (LPI-D Table 2-1)

| QREQn QACCEPTn QDENY | State | Meaning |
|---|---|---|
| 1 1 0 | Q_RUN | Device operational; controller guarantees clock or power |
| 0 1 0 | Q_REQUEST | Device operational, asked to become quiescent |
| 0 0 0 | Q_STOPPED | Device quiescent; clock or power not guaranteed |
| 1 0 0 | Q_EXIT | Clock or power guaranteed after an implementation-dependent delay |
| 0 1 1 | Q_DENIED | Device refused and stays operational; controller must deassert QREQn |
| 1 1 1 | Q_CONTINUE | Controller has deasserted QREQn after Q_DENIED |
| x 0 1 | — | "Unused (illegal)" |

Accepted sequence: Q_RUN → Q_REQUEST → Q_STOPPED → Q_EXIT → Q_RUN. Denied sequence: Q_RUN → Q_REQUEST → Q_DENIED → Q_CONTINUE → Q_RUN (LPI-D §2.1.2).

## P-Channel signals

From LPI-D §3.1.

| Signal | Driven by | Meaning | Rules |
|---|---|---|---|
| `PSTATE[M-1:0]` | Controller | The requested power state; encodings are IMPLEMENTATION DEFINED | Driven by a register; must be stable when the device sees PREQ rise |
| `PREQ` | Controller | Request to move to the state on PSTATE (HIGH) | Driven by a register |
| `PACCEPT` | Device | Accepts the transition (HIGH) | Driven by a register |
| `PDENY` | Device | Denies the transition (HIGH) | Driven by a register |
| `PACTIVE[N-1:0]` | Device | Per-state activity requirements; independent of the handshake | |

### P-Channel states (LPI-D Table 3-1)

| RESETn PREQ PACCEPT PDENY | State |
|---|---|
| 0 x 0 0 | P_RESET: device in reset |
| 1 0 0 0 | P_STABLE: device state is stable |
| 1 1 0 0 | P_REQUEST: asked to move to the state on PSTATE |
| 1 1 1 0 | P_ACCEPT: accepted; controller must set PREQ LOW |
| 1 0 1 0 | P_COMPLETE: device must set PACCEPT LOW |
| 1 1 0 1 | P_DENIED: device stays in its current state |
| 1 0 0 1 | P_CONTINUE: controller has set PREQ LOW after a denial |
| x x 1 1 | Unused |

## Key rules checklist

| # | Rule | Source | Explained in |
|---|---|---|---|
| 1 | Q-Channel: QREQn falls only when QACCEPTn is HIGH and QDENY LOW; it rises only when QACCEPTn and QDENY are both LOW or both HIGH | LPI-D §2.1.3 | [Low power: Q-Channel](low-power-and-wakeup.md#q-channel-lpi-d-ch-2) |
| 2 | Q-Channel: QACCEPTn falls only when QREQn and QDENY are LOW; it rises only when QREQn is HIGH and QDENY LOW | LPI-D §2.1.3 | [Low power: Q-Channel](low-power-and-wakeup.md#q-channel-lpi-d-ch-2) |
| 3 | Q-Channel: QDENY falls only when QREQn and QACCEPTn are HIGH; it rises only when QREQn is LOW and QACCEPTn HIGH | LPI-D §2.1.3 | [Low power: Q-Channel](low-power-and-wakeup.md#q-channel-lpi-d-ch-2) |
| 4 | Q-Channel reset: the device drives QACCEPTn and QDENY LOW. The controller releases reset in Q_STOPPED or Q_EXIT, and asserts device reset only in Q_STOPPED (or when both are reset together) | LPI-D §2.1.2 | [Low power: Q-Channel](low-power-and-wakeup.md#q-channel-lpi-d-ch-2) |
| 5 | An unused Q-Channel interface ties QREQn HIGH if the device is to be operational | LPI-D §2.1.4 | |
| 6 | P-Channel: PREQ rises only when PACCEPT and PDENY are LOW; it falls only when exactly one of PACCEPT and PDENY is HIGH | LPI-D §3.1 | [Low power: P-Channel](low-power-and-wakeup.md#p-channel-lpi-d-ch-3) |
| 7 | P-Channel: PSTATE changes only when PREQ, PACCEPT and PDENY are all LOW, or when PREQ and PDENY are HIGH and PACCEPT LOW | LPI-D §3.1 | [Low power: P-Channel](low-power-and-wakeup.md#p-channel-lpi-d-ch-3) |
| 8 | P-Channel: PACCEPT rises only when PREQ is HIGH and PDENY LOW, and falls only when PREQ and PDENY are LOW; PDENY rises only when PREQ is HIGH and PACCEPT LOW, and falls only when PREQ and PACCEPT are LOW | LPI-D §3.1 | [Low power: P-Channel](low-power-and-wakeup.md#p-channel-lpi-d-ch-3) |
| 9 | P-Channel reset: the device sets PACCEPT and PDENY LOW; device reset is asserted only in P_STABLE (or together with the controller); PSTATE must be stable at reset deassertion, and the device defines an initialisation period t<sub>init</sub> | LPI-D §3.1 | [Low power: P-Channel](low-power-and-wakeup.md#p-channel-lpi-d-ch-3) |

## Protocol assertions

SystemVerilog assertions for rules 1–4 and 6–9 (the handshake and reset-value parts). They come from `assertions/lpi_checker.sv` in the [amba-kb-agent](https://github.com/ChrisShakkour/amba-kb-agent) repository, which also has a test for every assertion. There are two modules, `q_channel_checker` and `p_channel_checker`.

**Status: syntax-checked and elaborated with slang 11. The Verilator tests have not been run yet.**

| Assertions | Rule | Source |
|---|---|---|
| `q_reset_low`, `p_reset_low` | Acknowledge signals LOW during reset | LPI-D §2.1.2, §3.1 |
| `q_illegal_state`, `p_illegal_state` | The unused state never occurs | LPI-D Tables 2-1, 3-1 |
| `q_qreqn_fall`, `q_qreqn_rise`, `q_qacceptn_fall`, `q_qacceptn_rise`, `q_qdeny_fall`, `q_qdeny_rise` | The six Q-Channel transition rules | LPI-D §2.1.3 |
| `p_preq_rise`, `p_preq_fall`, `p_pstate_change`, `p_paccept_rise`, `p_paccept_fall`, `p_pdeny_rise`, `p_pdeny_fall` | The seven P-Channel transition rules | LPI-D §3.1 |

Each transition rule takes the form "signal X can only change when Y", checked against the values at the previous clock edge:

```systemverilog
// LPI-D §2.1.3: "QREQn can only transition from HIGH to LOW when QACCEPTn is HIGH and QDENY is LOW."
q_qreqn_fall: assert property (@(posedge CLK) disable iff (!RESETn)
    (!QREQn && $past(QREQn)) |-> ($past(QACCEPTn) && !$past(QDENY)));

// LPI-D §3.1: "PSTATE can only transition when either: PREQ, PACCEPT, and PDENY are all LOW.
//             PREQ and PDENY are both HIGH and PACCEPT is LOW."
p_pstate_change: assert property (@(posedge CLK) disable iff (!RESETn)
    (PSTATE != $past(PSTATE)) |->
      ((!$past(PREQ) && !$past(PACCEPT) && !$past(PDENY)) ||
       ( $past(PREQ) && !$past(PACCEPT) &&  $past(PDENY))));
```

*Editor's note (not from the sources): the signals are asynchronous, so the checker must sample them on a clock fast enough to see every handshake step, for example the device clock after the synchronisers. If one sample sees two signals change together, a rule can fire falsely, because the specification's guarantee is about one change at a time.*

Not covered: QACTIVE/PACTIVE policy, PSTATE values, t<sub>init</sub>, the controller's reset sequencing and parity (LPI-D §2.2, §3.2).

## Related articles

- [Low power and wake-up](low-power-and-wakeup.md)
- [CHI interface hub](interface-chi.md) (link activation, a similar four-state handshake)
- [CXS interface hub](interface-cxs.md)

## Sources

LPI-D (§2.1, Table 2-1, §3.1, Table 3-1). See [Source key](sources.md).
