# Low power: Q-Channel, P-Channel, wake-up and link activation

> How AMBA interfaces let a power controller safely stop clocks or remove power, and how activity wakes things back up.

## In plain words

To save power you want to stop the clock of a block, or switch it off, whenever it's idle. But you must not do this in the middle of a transaction, and something has to say "wake up, work is coming". AMBA provides three kinds of mechanism:

1. **Device ↔ power controller handshakes** (the AMBA Low Power Interface, LPI):
   - **Q-Channel**: "may I stop you?" → "yes" or "no". This is a simple run/stop switch.
   - **P-Channel**: "please go to power state *N*" → "done" or "denied". This supports many power states.
2. **Wake-up signals** on bus interfaces (PWAKEUP, AWAKEUP, TWAKEUP…): "there is activity coming on this interface, so make sure the clocks are on".
3. **Link activation** on credited links (CHI, CXS, C2C): an orderly STOP/RUN handshake that returns all credits before the link sleeps.

## Q-Channel (LPI-D ch. 2)

Signals: `QREQn` (controller→device, active LOW request to stop), `QACCEPTn` (device, active LOW accept), `QDENY` (device, deny) and `QACTIVE` (device: "I have work").

| State | QREQn | QACCEPTn | QDENY | Clock/power guaranteed? |
|---|---|---|---|---|
| Q_RUN | 1 | 1 | 0 | Yes |
| Q_REQUEST | 0 | 1 | 0 | Yes |
| Q_STOPPED | 0 | 0 | 0 | **No** |
| Q_EXIT | 1 | 0 | 0 | After an implementation-defined delay |
| Q_DENIED | 0 | 1 | 1 | Yes |
| Q_CONTINUE | 1 | 1 | 1 | Yes |

- Only **one** of QACCEPTn or QDENY changes per step, so the handshake is safe across asynchronous clock domains. "All signals are assumed to be asynchronous" (LPI-D §2.1).
- Polarities are chosen so the **quiescent state has all signals LOW**, which makes isolation simple.
- `QACTIVE` HIGH is a hint that should make the controller exit Q_STOPPED. QACTIVE LOW only hints that a request *might* be accepted.
- Subsets: omit QDENY (tie LOW at the controller) if you never deny. Omit QACTIVE (tie LOW) if no wake hint is needed. A QACTIVE-only interface is possible but gives no guarantee.
- Q-Channel "is an evolution of the AXI low-power interface" (`CSYSREQ`/`CSYSACK`/`CACTIVE`) and is backward-compatible in most cases (LPI-D §2.1, §2.6).

## P-Channel (LPI-D ch. 3)

Signals: `PSTATE[M-1:0]` (requested state), `PREQ`, `PACCEPT`, `PDENY` and `PACTIVE[N-1:0]` (per-requirement activity hints).
- Sequence: P_STABLE → (controller sets PSTATE, raises PREQ) P_REQUEST → (device raises PACCEPT or PDENY) → (controller drops PREQ) → (device drops PACCEPT/PDENY) → P_STABLE.
- PSTATE must be stable when the device sees PREQ rise. PREQ, PSTATE, PACCEPT and PDENY must come directly from registers.
- The device's documentation must list every power state, the allowed transitions, which transitions can be denied, and the PACTIVE bit meanings.
- "The P-Channel interface should be used only if Q-Channel functionality is insufficient" (LPI-D §1.2).

**Parity-extended Q/P-Channel**: every signal gets an odd-parity `*CHK` companion. The state machine advances only when signal and check agree, and a long stay in an in-between encoding indicates a fault (LPI-D §2.2, §3.2).

## Wake-up signals on bus interfaces

| Interface | Signal | Since |
|---|---|---|
| APB5 | `PWAKEUP` (Requester) | APB Issue D (APB-E §3.7) |
| AXI5 | `AWAKEUP` (Manager), `ACWAKEUP` (Subordinate, for the snoop channel) | AXI5 (AXI-L §A14.1) |
| AXI5-Stream | `TWAKEUP` (Transmitter) | AXIS Issue B (AXIS-B §2.3) |
| ATB-C | `ATWAKEUP` | ATB Issue C (ATB-C ch. 6) |

Common rules (APB-E §3.7; AXI-L §A14.1; AXIS-B §2.3):
- Synchronous to the interface clock but **glitch-free**, so it can be sampled in another clock domain (drive it from a register or a glitch-free OR tree).
- Recommended to assert it **one cycle before** VALID/PSEL, so the first transfer is not delayed.
- A receiver **may wait for wake-up** before accepting. If wake-up is present but never asserted, the interface **can deadlock**.
- Once asserted with a pending request, keep it HIGH until the request is accepted.
- AXI wake-up signals exist only with Valid-Ready transport, not credited transport.

## Clock gating hints and link activation

- **CHI** `*FLITPEND` and **AXI5 credited** `*PENDING`: asserted exactly (CHI) or at least (AXI) one cycle before a transfer, so the receiver can gate registers cycle by cycle (CHI-H §B14.4; AXI-L §A2.4.4).
- **CHI link activation**: `TXLINKACTIVEREQ/ACK` and `RXLINKACTIVEREQ/ACK`, a four-phase handshake per direction. STOP(00) → ACTIVATE(10) → RUN(11) → DEACTIVATE(01). Before STOP the transmitter returns **every** L-Credit (dedicated and shared) with LCrdReturn flits, so the link is in its "just after reset" state (CHI-H §B14.5).
  - The receiver may send credits only once it has raised ACK. The transmitter must not use credits received in ACTIVATE until RUN.
  - TX and RX directions are linked. If the other side activates your RX link, you **must** activate your TX link "in a timely manner", and likewise for deactivation. Do not delay a state change while waiting for an outstanding transaction to finish (CHI-H §B14.6).
  - If two inputs change in the same cycle but are seen in different cycles (an "async input race"), wait until both have arrived before changing any output (CHI-H §B14.6.3.4).
- **CHI protocol activity**: `TXSACTIVE` is high from before the first flit of a transaction until after its last flit. A component that raises TXSACTIVE must start link activation itself. Only the interconnect may generate TXSACTIVE directly from RXSACTIVE. Use higher-level clock gating only when both SACTIVE and the links are idle (CHI-H §B14.7).
- **CHI coherency connect**: `SYSCOREQ/SYSCOACK`. An RN-F or RN-D must be able to answer snoops from the moment it raises SYSCOREQ. It must not issue cacheable coherent requests or DVMs until it sees SYSCOACK, must finish all of them before dropping SYSCOREQ, and keeps answering snoops until SYSCOACK falls (CHI-H §B15.2).
- **AXI5 Coherency Connection**: the same signal names, but it controls only whether the Manager receives **DVM messages** on AC. AXI has no data snooping. The Manager must accept DVMs even before SYSCOACK rises, and `AWAKEUP` must be asserted to let the handshake progress (AXI-L §A14.1.2, §A15.6).
- **CXS**: `CXSACTIVEREQ`/`CXSACTIVEACK` and `CXSDEACTHINT` (CXS-D §3.1).
- **AXI5 credited**: `ACTIVATEREQ`/`ACTIVATEACK`, a stop-request signal `ASKSTOP`, and STOP/ACTIVATE/RUN/DEACTIVATE states. Only the Manager starts activation. **Credits are returned implicitly when the channel reaches STOP**, and credits received in STOP are discarded (AXI-L §A14.2). DVM snoop channels have their own `ACTIVATEREQD`/`ACKD`/`ASKSTOPD` set with the roles swapped (AXI-L §A15.7).

## Where the sources agree

- Wake-up signals are **hints that can gate acceptance**, so the same deadlock warning appears in APB-E §3.7, AXIS-B §2.3 and AXI-L §A14.1.1.
- Credited links **start with no credits** after reset, and none are left at the transmitter after sleeping (CHI-H §B14.5; CXS-D §2.1; AXI-L §A14.2). They differ on *how* the credits come back (see below).
- Controller and device handshakes are four-phase and safe across asynchronous domains (LPI-D §2.1, §3.1; CHI-H §B15.2).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Is the peripheral bus clocked at all? | INTRO96 §1.2.2 (1996): APB uses select and strobe "i.e. **no clock**", giving almost zero power when idle | AMBA2 §5.1–5.2: APB transfers are timed by the rising edge of PCLK. §1.7 still lists, among APB slave interface features, a "zero-power interface during non-peripheral bus activity" and "timing can be provided by decode with strobe timing (unclocked interface)". APB5 adds PWAKEUP (APB-E) | AMBA 2 moved APB to rising-edge PCLK timing (AMBA2 §5.1), and §5.8 shows how to adapt older strobe-timed (rev D, `PSTB`) peripherals. *Editor's note (not from the sources): the idea that modern low power comes mainly from clock-gating protocols is our summary, not a statement in these specs* |
| Where AXI low-power lives | AXI3/AXI4 specs contained an AXI low-power interface (CSYSREQ, CSYSACK, CACTIVE) | AXI-Hc §D1.1: "References to the Low-Power Interface have been removed … superseded by the AMBA Low Power Interface Specification (IHI 0068)" | LPI-D §1.1 describes the result: interfaces "that can be used to control the clock and power states of devices", with Q-Channel described as "an evolution of the AXI low-power interface" and backward-compatible "in most situations" (LPI-D §2.1.1, §2.6). The spec does not say why the material moved out of the AXI spec |
| Wake-up after a transaction starts | APB-E §3.7: PWAKEUP "must remain asserted until PREADY is asserted" if HIGH together with PSEL | AXI-L §A14.1: once the transaction is in progress, the wake-up level is "IMPLEMENTATION DEFINED", but the interconnect "must remain active until the transaction has completed" | The same goal, worded differently. AXI puts the burden on the interconnect to stay awake, APB on the Requester |
| How credits come back before sleep | CHI-H §B14.5: in DEACTIVATE the transmitter **must explicitly return every credit** with LCrdReturn link flits, and the receiver waits for all of them before dropping ACK | AXI-L §A14.2: credits are **implicitly returned** on entering STOP. Transmitters are not required to return them, and credits that arrive in STOP are discarded | A design difference that neither spec explains. *Editor's note (not from the sources): CHI already has link flits (LCrdReturn) that can carry returned credits, while AXI5 credited transport has no such flit. A CHI↔AXI credited bridge must handle both behaviours* |
| What SYSCOREQ/SYSCOACK means | CHI-H §B15: join the **coherency (snoop) and DVM** domains | AXI-L §A15.6: opt in to receiving **DVM messages** only | AXI does not snoop data (AXI-L §A8.1), so only DVM needs a connect handshake |
| Pending-signal timing | CHI-H §B14.4: FLITPEND is asserted **exactly** one cycle before a flit | AXI-L §A2.4.4: PENDING must be asserted in the cycle before VALID, and may stay HIGH permanently | Both allow a permanently HIGH pending signal, so in practice the difference is only one of wording |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Never connect a wake-up input that your logic *waits on* to a source that might never assert it. Tie it HIGH if the other side lacks the output (AXI-L §A14.1.1 suggests tying HIGH or deriving it from VALID).
- Generate wake-up signals from **flops**, not combinational logic, because they cross clock domains.
- Clock-gate the Requester and Completer of an APB link **together**, otherwise the Completer may miss a SETUP phase (APB-E §3.7).

## Related articles

- [Handshakes and flow control](handshakes-and-flow-control.md)
- [CHI architecture](chi-architecture.md)
- [Streaming interfaces](streaming-interfaces.md) (CXS activation)
- [Interface protection, parity and RAS](interface-protection-parity-and-ras.md)

## Sources

INTRO96, AMBA2, APB-E, AXI-Hc, AXI-L (read in full), AXIS-B, ATB-C, CHI-H (read in full), CXS-D, LPI-C, LPI-D. See [Source key](sources.md).
