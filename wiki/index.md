# AMBA Knowledge Wiki: Index

A concept-organised wiki of Arm's AMBA on-chip interface protocols, written for **junior RTL design engineers**. Each article explains one concept across *all* the protocols that use it: what it is, what the sources say, where they agree, and where (and why) they disagree.

- **Sources:** 39 official Arm documents, downloaded into [`../raw/`](../raw/) with `python tools/download_sources.py` (they are not stored in the repository). Codes such as `AXI-L §A5.3` are explained in the [Source key](sources.md). The latest AXI (Issue L) and CHI (Issue H) specifications were read in full.
- **Disagreements:** every article has a "Where the sources disagree" section. All 71 are collected in [Protocol evolution and version differences](protocol-evolution-and-versions.md#register-of-disagreements-across-the-sources).

## Articles

### Start here
| Article | One-line description |
|---|---|
| [AMBA overview](amba-overview.md) | What AMBA is, the full protocol family on one page, and a rule of thumb for which protocol to use |
| [Terminology and roles](terminology-and-roles.md) | Manager/Subordinate vs Requester/Completer vs Transmitter/Receiver (and old master/slave), plus transfer, beat, burst, flit and other size words |
| [Protocol evolution and version differences](protocol-evolution-and-versions.md) | Timeline of every generation and issue, per-protocol change tables, and the register of all 71 disagreements |

### How data moves
| Article | One-line description |
|---|---|
| [Interconnect, topology and bridges](interconnect-topology-and-bridges.md) | Shared buses with arbiters, multi-layer AHB, AXI point-to-point fabrics, CHI rings and meshes, bridges, and the 1 KB/4 KB decode rules |
| [Handshakes and flow control](handshakes-and-flow-control.md) | PREADY/HREADY wait states, the VALID/READY rules, and credit-based flow control (CHI, CXS, AXI5 credited, C2C) |
| [Transfer phases and pipelining](transfer-phases-and-pipelining.md) | APB SETUP/ACCESS, AHB address/data overlap, AXI's five independent channels, and CHI's protocol/network/link layers |
| [Bursts, sizes, alignment and write strobes](bursts-sizes-and-alignment.md) | INCR/WRAP/FIXED bursts, size and length encodings, wrap maths, narrow/unaligned transfers, PSTRB/HWSTRB/WSTRB, Lite subsets |
| [Endianness and byte lanes](endianness-and-byte-lanes.md) | Which wires carry which byte, little-endian vs BE8 vs BE32, and byte invariance |
| [Transaction IDs, outstanding transactions and ordering](transaction-ids-and-ordering.md) | The AXI ID ordering model, interleaving, interconnect ID widening, CHI Request/Endpoint order and CompAck, and stream ordering |
| [Responses and error signalling](responses-and-errors.md) | OKAY/ERROR/SLVERR/DECERR/SPLIT/RETRY, the two-cycle AHB error, what errors do (and don't) guarantee, and bridge mapping |

### What a transaction means
| Article | One-line description |
|---|---|
| [Memory types and cache attributes](memory-types-and-cache-attributes.md) | Device vs Normal memory, AxCACHE and HPROT bits, bufferable/modifiable/allocate, and the rules for merging, splitting and prefetching |
| [Protection and security attributes](protection-and-security.md) | Privileged/instruction/Non-secure bits, physical address spaces (Secure, Non-secure, Root, Realm, GDI), and the RME, MEC and MTE extensions |
| [Exclusive access, locked transfers and atomics](exclusive-locked-and-atomic-access.md) | Bus locking, exclusive monitors (EXOKAY/HEXOKAY), AXI5/CHI atomic operations, and single-/multi-copy atomicity |

### Coherency and virtual memory
| Article | One-line description |
|---|---|
| [Cache coherency fundamentals](cache-coherency-fundamentals.md) | Why coherency is needed, software vs hardware coherency, cache-line states (ACE 5, CHI 7), snoop filters, shareability domains, CMOs, and the PoC/PoS/PoP… terms |
| [ACE: AXI Coherency Extensions](ace-coherency-extensions.md) | Snoop channels AC/CR/CD, RACK/WACK, ACE-Lite, the ACE5 variants, barriers, and why ACE was superseded |
| [CHI: Coherent Hub Interface](chi-architecture.md) | Nodes, channels and IDs, transaction classes, snoops and hazards, ordering and multi-request, retry and Resource Planes, DMT/DCT/DWT, stashing, link layer, and the issue history A–H |
| [DVM and address translation](dvm-and-address-translation.md) | TLB-invalidate and sync messages in ACE/AXI5/CHI (flow-control rules, range TLBI), SMMU TCU/TBU, DTI (tokens, invalidation and deadlock rules, AXI5-Stream transport), LTI (channels, integration styles, translation cache) and untranslated transactions v1–v4 |

### Specialised interfaces
| Article | One-line description |
|---|---|
| [Streaming interfaces: AXI-Stream, ATB and CXS](streaming-interfaces.md) | Address-less point-to-point streams: byte types, TKEEP/TSTRB/TLAST/TID/TDEST, and CXS packets and credits |
| [Debug trace: the Advanced Trace Bus](debug-trace-atb.md) | CoreSight trace transport: ATID rules, flush (AFVALID/AFREADY), triggers, sync requests, ATWAKEUP, ATB versions and what each issue changed |
| [Chiplets and chip-to-chip](chiplets-and-chip-to-chip.md) | CHI C2C: 256-byte containers (formats X/Y/Z for UCIe/CXL), message types, WritePush and multi-request, features that don't cross the link, credits and Resource Planes, routing and multi-hop, DVM, link states, property negotiation, RME-DA and IDE |
| [Generic Flash Bus](generic-flash-bus.md) | Flash controller ↔ eFlash macro commands (READ/WRITE/ROW WRITE/ERASE/MASS ERASE), abort and housekeeping |

### Power, robustness and configuration
| Article | One-line description |
|---|---|
| [Low power: Q-Channel, P-Channel, wake-up and link activation](low-power-and-wakeup.md) | Clock/power handshakes with a controller, xWAKEUP signals, FLITPEND/PENDING clock gating, CHI/CXS link activation and SYSCOREQ |
| [Interface protection: parity, poison and RAS](interface-protection-parity-and-ras.md) | The common odd-byte-parity scheme, inverted checks for controls, poison and DataCheck, and error-handling policy |
| [Interface properties, optional signals and user signals](interface-properties-and-user-signals.md) | How properties switch features and signals on and off, reading compatibility and tie-off tables, and user-signal rules (and why to avoid them) |
| [Quality of Service and traffic modelling](qos-and-traffic-modelling.md) | AxQOS, QoS-accept, Busy indicators, resource planes, CHI retry and MPAM, and ATP traffic profiles for modelling |

### Reference
| Page | One-line description |
|---|---|
| [Source key](sources.md) | Maps every citation code to its Arm documentation page and local PDF in `raw/`, and records how deeply each source was read |

## Suggested reading paths

- **First week on an APB/AHB peripheral:** Overview → Terminology → Transfer phases → Handshakes → Bursts → Responses → Protection → Properties.
- **Writing an AXI Manager or Subordinate:** Handshakes → Transfer phases → Bursts → Endianness → Transaction IDs → Responses → Memory types → Atomics.
- **Joining a coherent-SoC team:** Cache coherency → ACE → CHI → DVM → Low power → Parity/RAS → Chiplets.

## Find articles by protocol

| Protocol | Most relevant articles |
|---|---|
| APB | [Phases](transfer-phases-and-pipelining.md), [Handshakes](handshakes-and-flow-control.md), [Responses](responses-and-errors.md), [Security](protection-and-security.md), [Low power](low-power-and-wakeup.md), [Parity](interface-protection-parity-and-ras.md) |
| AHB | [Topology](interconnect-topology-and-bridges.md), [Phases](transfer-phases-and-pipelining.md), [Bursts](bursts-sizes-and-alignment.md), [Endianness](endianness-and-byte-lanes.md), [Responses](responses-and-errors.md), [Memory types](memory-types-and-cache-attributes.md), [Atomics](exclusive-locked-and-atomic-access.md) |
| AXI (3/4/5, Lite) | [Handshakes](handshakes-and-flow-control.md), [Bursts](bursts-sizes-and-alignment.md), [Ordering](transaction-ids-and-ordering.md), [Responses](responses-and-errors.md), [Memory types](memory-types-and-cache-attributes.md), [Atomics](exclusive-locked-and-atomic-access.md), [QoS](qos-and-traffic-modelling.md) |
| ACE / ACE-Lite | [ACE](ace-coherency-extensions.md), [Coherency](cache-coherency-fundamentals.md), [DVM](dvm-and-address-translation.md) |
| CHI / CHI C2C | [CHI](chi-architecture.md), [Coherency](cache-coherency-fundamentals.md), [Chiplets](chiplets-and-chip-to-chip.md), [Flow control](handshakes-and-flow-control.md) |
| AXI-Stream, ATB, CXS | [Streaming](streaming-interfaces.md), [ATB](debug-trace-atb.md) |
| DTI, LTI | [DVM and translation](dvm-and-address-translation.md) |
| Q-Channel, P-Channel | [Low power](low-power-and-wakeup.md) |
| GFB | [Generic Flash Bus](generic-flash-bus.md) |
| ATP | [QoS and traffic modelling](qos-and-traffic-modelling.md) |
