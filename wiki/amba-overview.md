# AMBA overview: what it is and which protocol to use

> AMBA is Arm's free, open family of rules for how blocks inside a chip talk to each other. Each protocol in the family is tuned for a different job, from tiny register buses to coherent multi-chip networks.

## In plain words

Inside a System-on-Chip (SoC) you have CPUs, DMA engines, memories, timers, UARTs, GPUs and so on. They all need to exchange data. If every team invented its own wiring and timing rules, nothing would plug together. **AMBA** (Advanced Microcontroller Bus Architecture) is a set of agreed "plug shapes and conversation rules". When your block follows one of them, it can connect to anyone else's block that follows the same one.

Think of it like a family of connectors in a house:
- **APB** is a cheap, slow light switch: simple and low power.
- **AHB** is a household socket: a decent amount of power, and still simple.
- **AXI** is a high-current industrial socket with many independent lanes.
- **CHI** is a whole smart power grid that also keeps everyone's copy of the data in sync.
- Specialised connectors (AXI-Stream, ATB, CXS, DTI, LTI, GFB, Q/P-Channel) each do one job.

The specs define **signals and cycle-level behaviour only**. They do not define voltages, clock frequencies, layout or the interconnect's internal design (INTRO96 §1.2; AMBA2 §1.9).

## Key ideas

1. **It is open and royalty-free.** INTRO96 §1.1.2 says anyone can get the spec and use it free, with no royalty. Every modern spec carries the *AMBA Specification Licence*, which grants a perpetual, royalty-free licence to build compliant products (APB-E preface). CHI C2C keeps the same model (C2C-B).
2. **The protocols form a performance/complexity ladder.** G-SYS §4.4 groups them as:
   - *APB and AHB*: low cost, low power, low complexity. Used for configuration and low-bandwidth peripherals. AHB is "generally used with M-profile" (Cortex-M).
   - *AXI*: high-performance, I/O-coherent or non-coherent.
   - *CHI*: high performance and scalability, full coherency, credit-based flow control.
   - *CHI C2C*: packetised CHI for chip(let)-to-chip(let) links.
3. **Older generations are kept, not deleted.** New issues add optional features behind *properties* (named switches such as `Wakeup_Signal` or `Check_Type`). A block that ignores a new feature usually still connects to one that uses it. See [Interface properties and user signals](interface-properties-and-user-signals.md).
4. **Bridges glue the levels together.** A typical SoC has an AXI or CHI backbone, with AHB or APB islands hanging off bridges (AMBA2 §1.7; APB-E §1.1). See [Interconnect, topology and bridges](interconnect-topology-and-bridges.md).

## The family at a glance

| Protocol | Generation | One-line purpose | Main article |
|---|---|---|---|
| ASB | AMBA 1–2 | First system bus. Tri-state, falling-edge, multi-master. Obsolete | [Protocol evolution](protocol-evolution-and-versions.md) |
| APB (2, 3, 4, 5) | AMBA 1→5 | Simple, unpipelined register bus for peripherals | [Transfer phases](transfer-phases-and-pipelining.md) |
| AHB / AHB-Lite / AHB5 | AMBA 2→5 | Pipelined single-edge bus. Common with Cortex-M | [Transfer phases](transfer-phases-and-pipelining.md) |
| AXI3 / AXI4 / AXI5 (+ -Lite) | AMBA 3→5 | Point-to-point, 5 independent channels, IDs, outstanding transactions | [Transaction IDs and ordering](transaction-ids-and-ordering.md) |
| AXI-Stream | AMBA 4→5 | Unidirectional data streams, no addresses | [Streaming interfaces](streaming-interfaces.md) |
| ACE / ACE-Lite / ACE5-* | AMBA 4→5 | Coherency added to AXI. Superseded by CHI | [ACE](ace-coherency-extensions.md) |
| CHI | AMBA 5 | Layered, packet/flit-based coherent interconnect | [CHI architecture](chi-architecture.md) |
| CHI C2C | AMBA 5 | CHI packed into 256-byte containers for chiplets | [Chiplets](chiplets-and-chip-to-chip.md) |
| ATB | AMBA 3→5 | Trace data transport (CoreSight) | [Debug trace (ATB)](debug-trace-atb.md) |
| CXS | AMBA 5 | Credited streaming of packets (PCIe/CCIX/CXL, C2C) | [Streaming interfaces](streaming-interfaces.md) |
| DTI / LTI | AMBA 5 | Address-translation messages for an SMMU | [DVM and address translation](dvm-and-address-translation.md) |
| Q-Channel / P-Channel | AMBA 4→5 | Clock- and power-state handshakes | [Low power and wake-up](low-power-and-wakeup.md) |
| GFB | AMBA 5 | Flash controller ↔ flash macro | [Generic Flash Bus](generic-flash-bus.md) |
| ATP | AMBA 5 | Not a bus: a format for describing traffic for modelling | [QoS and traffic modelling](qos-and-traffic-modelling.md) |

## Choosing a protocol (a junior engineer's rule of thumb)

| If your block is... | Start with | Why (source) |
|---|---|---|
| A peripheral with a few control registers | APB (APB4/APB5) | "Designed for accessing the programmable control registers of peripheral devices" (APB-E §1.1) |
| A simple memory or peripheral on a Cortex-M system | AHB5 / AHB-Lite | Pipelined, single manager, widely used with M-profile (G-SYS §4.4.1) |
| A DMA engine, accelerator, memory controller or anything needing bandwidth | AXI5 | Multiple outstanding transactions, out-of-order completion (AXI-L §A1.1). Arm recommends AXI5 for new designs (AXI-J/AXI-L §B4.1) |
| A register block on an AXI system that never bursts | AXI5-Lite (or AXI4-Lite) | Burst length always 1 (AXI-L §B2.1.5; AXI-Hc §B1.1) |
| A video/packet/DSP pipeline with no addresses | AXI-Stream | Point-to-point Transmitter→Receiver data stream (AXIS-B §1.1) |
| A CPU cluster with caches that must be coherent | CHI | ACE is superseded. CHI is "recommended for fully coherent agents" (AXI-L §B4.1) |

## Where the sources agree

- AMBA is **technology-independent** and defines only cycle-level protocol (INTRO96 §1.2; AMBA2 §1.9; restated in every later spec's scope).
- **APB is for low-bandwidth register access behind a bridge.** This has been true from 1996 (INTRO96 §1.2.2) to 2023 (APB-E §1.1).
- **CHI is the successor to ACE** for full coherency (G-CHI §1; G-SYS §4.4.1; AXI-L §B4.1).

## Where the sources disagree (and why)

| Topic | Source A says | Source B says | Why they differ |
|---|---|---|---|
| When AMBA started | INTRO96 (dated Oct 1996): the spec "has been stable from September 1995" and was used in the ARM7100 | G-AXI §2: "Arm introduced AMBA in the late 1990s" | The 1996 primary source is earlier and more precise: AMBA was stable by September 1995. The guide's "late 1990s" is approximate |
| When CHI appeared | G-AXI §2: "In 2014, the AMBA 5 Coherent Hub Interface (CHI) specification was introduced" | CHI-H release table: Issue A (Jun 2014) was a *limited* release; the *first public* release was Issue B (Aug 2017) | Both are true. 2014 is the first (limited) release, 2017 the first public one |
| When AHB5 appeared | G-AXI §2: "In 2016, AHB-Lite was updated to AHB5" | AHB-C revision table: Issue B (which introduced AHB5) is dated 25 June 2015; B.b Oct 2015 | The spec's own revision table is authoritative (2015). G-AXI ties AHB5 to Armv8-M ("to complement the Armv8-M architecture"). *Editor's note (not from the sources): the guide may be dating it by Armv8-M rather than by the spec issue* |
| AHB-Lite's generation | G-AXI §2 lists AHB-Lite under AMBA 3 (2003) | AHB-A (the AHB-Lite spec) is dated June 2006 | AHB-Lite is branded AMBA 3, but its stand-alone spec was published later than the 2003 AMBA 3 AXI spec |
| Is ACE still current? | G-AXI (2025) still teaches ACE as part of AMBA 4 | AXI-J/AXI-L: ACE and ACE5 "removed" from the spec. G-SYS: ACE "has been superseded by CHI" | G-AXI §1 says it "focuses on the key concepts of AXI, as defined in AXI4", so it describes ACE as part of AMBA 4 history. The specs (AXI-J/L) and G-SYS give the current position: ACE is removed and superseded by CHI |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Always record **which issue** of a spec your IP targets (for example "APB5, IHI0024E"). Features such as `PNSE` (RME) exist only from APB Issue E.
- When you inherit a block, look at its port list. `PENABLE` means AMBA 2 APB or later. `PSTB` means the 1990s APB Rev D (AMBA2 §5.8). `WID` means AXI3 (AXI-Hc §A5.2).

## Related articles

- [Terminology and roles](terminology-and-roles.md)
- [Protocol evolution and version differences](protocol-evolution-and-versions.md)
- [Interconnect, topology and bridges](interconnect-topology-and-bridges.md)

## Sources

INTRO96, AMBA2, APB-E, AXI-J, AXI-L, CHI-H, C2C-B, G-AXI, G-CHI, G-SYS. See [Source key](sources.md).
