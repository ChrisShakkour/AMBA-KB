# Networks-on-chip (NoC)

> A network-on-chip moves transactions as packets through routers instead of over shared wires or one big crossbar. This article maps NoC ideas (network interfaces, packets and flits, routing, credits, virtual channels, deadlock freedom) onto the AMBA terms in this wiki, and lists open-source NoC designs, generators and simulators.

## In plain words

There are three ways to connect many Managers to many Subordinates:

1. **A shared bus.** One transfer at a time, with an arbiter choosing who goes next (AMBA 2 AHB, ASB).
2. **A crossbar.** Every Manager has a path to every Subordinate, so many transfers happen at once. The wire count grows with *Managers × Subordinates*, so it works well for tens of ports.
3. **A network-on-chip.** Each component plugs into a **network interface (NI)**, which turns its transactions into **packets**. Packets hop through **routers** connected by short links, in a ring, mesh or other topology, much like a computer network.

*Editor's note (not from the sources): this three-way split is the usual textbook framing, not wording from an AMBA spec.*

AMBA covers both ends of this picture. **AXI** is the interface at the *edge* of a NoC: the network interface speaks AXI to the component and packets to the network. **CHI** already *is* a packet protocol. Its messages are flits that carry source and target node IDs, so routers can carry them across "a ring, mesh or crossbar" (see [CHI](chi-architecture.md)).

## How NoC concepts map to AMBA

| NoC concept | AMBA equivalent | Source |
|---|---|---|
| Topology | "The CHI architecture is primarily topology-independent." The spec shows crossbar, ring and mesh examples | CHI-H §B1.2; G-CHI §2 |
| Topology (AXI fabrics) | Shared request and data channels, a shared request channel with multiple data channels, or a fully multilayer fabric. Request bandwidth is usually much smaller than data bandwidth | AXI-L §A1.2.1.1 |
| Layers | CHI splits protocol (transactions), network (packets, adding SrcID/TgtID) and link (flits, credit-based flow control) | CHI-H §B1.3 |
| Packet, flit, phit | In CHI, one packet = one flit = one phit | CHI-H §B1.3 |
| Routing address | `SrcID` / `TgtID` node IDs, 7 to 16 bits wide (`NodeID_Width`) | CHI-H §B13.9 (see [CHI](chi-architecture.md)) |
| Routing in the network | The interconnect may remap `TgtID`, which is why write data goes to the SrcID of the DBIDResp, not the original TgtID | CHI-H §B2.4 |
| Snoop routing | The SNP flit has no TgtID; snoop routing is implementation-defined, for example from a snoop filter | CHI-H §B13.9.3; G-CHI §3 |
| Link-level flow control | Credits: 1–15 L-Credits per channel, one per flit, never used in the cycle they arrive. All credits start at the receiver after reset | CHI-H §B14.2, §B14.1.3 |
| Credits at AXI edges | AXI5 credited transport (`AXI_Transport = Credited`) | AXI-L §A2.4 |
| Virtual channels | Resource Planes: up to 8 independent credit pools per channel (AXI5 credited, CHI Issue H, C2C). They "are used to enable independence between traffic sharing a channel. This could be to avoid deadlock scenarios or to improve quality-of-service". *Editor's note (not from the sources): they play the role that virtual channels play in NoC literature* | AXI-L §A2.4.2; CHI-H §B14.2.1.2 |
| Deadlock freedom | CHI channel-dependency rules, for example a Request Node must make progress on inbound RSP and DAT without depending on any other channel | CHI-H §B13.4.1 |
| Quality of service | AXI `AxQOS`; CHI QoS, MPAM and CBusy | AXI-L; CHI-H ch. B11 (see [QoS](qos-and-traffic-modelling.md)) |
| Clock gating of links | `FLITPEND` one cycle before a flit; `LINKACTIVE` handshakes | CHI-H §B14.5–§B14.6 |
| Leaving the chip | CHI C2C carries CHI between chiplets, with its own message credits per class | C2C-B (see [Chiplets](chiplets-and-chip-to-chip.md)) |
| Many switches in one network | NIC-400 supports "Complex topologies, including Network on Chip (NoC) loop-back connections between switches" and "Up to five cascaded switch networks between any master and slave interface pair" | NIC400-J §1.2 |

## What an AXI network interface must preserve

A NoC with AXI at its edges is only correct if the network interfaces keep every AXI rule end to end. The packets in between can look like anything, but these rules must survive:

| AXI rule | Why the NI cares | Source |
|---|---|---|
| Responses with the same ID come back in order; different IDs may reorder | Packets can take different paths, so the NI must reorder or restrict same-ID traffic | AXI-L §A5.3 (see [Ordering](transaction-ids-and-ordering.md)) |
| BID and RID must echo AWID and ARID | The NI must remember each request's ID, or carry it in the packet | AXI-L §A5.1.1 |
| A transaction must not cross 4 KB | Splitting at router or memory-interleave boundaries must respect it | AXI-L §A3.1 |
| Non-modifiable transactions must not be resized, split or merged (except bursts over 16 beats) | A NoC that splits or packs data must check AxCACHE[1] | AXI-L §A4.2.2 |
| Exclusive and atomic accesses | The NI must keep them intact, and must not split them | AXI-L §A6 (see [Exclusives and atomics](exclusive-locked-and-atomic-access.md)) |

For CHI, the network itself is defined by the spec. It must honour the channel-dependency rules (CHI-H §B13.4.1) and the link-layer credit rules (CHI-H §B14.2).

## Open-source NoC designs and generators

These are web references (see [Web references](#web-references-not-specifications-read-2026-11-23)). They are not part of the audited source set. Check each project's own licence before use.

| Project | What it is | Language | AMBA support |
|---|---|---|---|
| **FlooNoC** (PULP Platform) | NoC with network interfaces ("chimneys") and routers, generated by **floogen** from a configuration file. The README says no open-source simulation setup is provided (W-FLOO) | SystemVerilog | "Mainly supports AXI4+ATOPs"; the protocol is handled in the NIs so routers stay simple |
| **Constellation** (UC Berkeley) | NoC RTL generator for arbitrary and irregular topologies, with a routing-table compiler that verifies deadlock freedom. Part of Chipyard (W-CONST) | Chisel | AXI4 and TileLink transport |
| **ESP** (Columbia University) | Tile-based SoC platform with a multi-plane NoC. Proxies translate bus Manager requests into NoC transactions, and three planes carry MESI directory coherence (W-ESP) | SystemVerilog/VHDL | Bus proxies at each tile |
| **OpenPiton** (Princeton) | Many-core framework with three 2D-mesh networks (P-Mesh). A chip bridge extends them off-chip to a "chipset" (W-PITON) | Verilog | AXI bridges described in the BYOC work |
| **ProNoC** | EDA tool that generates complete NoC-based many-core RTL. Mesh, torus, ring, fat-tree and custom topologies, with deterministic, turn-model and adaptive routing. Sources disagree on its licence (W-PRONOC) | SystemVerilog | Not stated |
| **OpenSoC Fabric** (Lawrence Berkeley Lab) | Chisel NoC generator producing both a C++ model and Verilog (W-OSF) | Chisel | Not stated |
| **CONNECT** (CMU) | Web-based NoC generator for FPGAs; output is Verilog. Generated networks are for "internal, non-commercial research use" only (W-CONNECT) | Bluespec | Not stated |
| **OpenTitan tlgen** | Generates TileLink-UL crossbars from an Hjson description. A crossbar generator, not a NoC (W-TLGEN) | SystemVerilog | TileLink, not AMBA |

## Simulators (performance models, not RTL)

Use these to size a network (topology, buffer depths, virtual channels) before writing RTL.

| Simulator | What it is |
|---|---|
| **BookSim 2** (Stanford) | Cycle-accurate interconnection-network simulator in C++, written to accompany *Principles and Practices of Interconnection Networks* (W-BOOKSIM) |
| **Garnet** (in gem5) | The on-chip network model of gem5's Ruby memory system. Garnet 3.0 includes HeteroGarnet, with heterogeneous links and clock domains (W-GARNET) |
| **Noxim** (University of Catania) | Cycle-accurate NoC simulator built on SystemC (W-NOXIM) |

## Open specifications

There is no open NoC protocol standard in the AMBA family. CHI is free to download, but it is Arm's specification. The nearest open alternative is **TileLink**: OpenTitan's TL-UL bus is "compliant with TileLink-UL apart from user extensions", and refers to TileLink specification 1.7.1 (W-TLGEN).

## Where the sources agree

- Topology is left to the implementer. CHI is "primarily topology-independent" (CHI-H §B1.2), and NIC-400 offers multiple switches with "many topology options" (NIC400-J §1.1).
- Credit-based flow control is the common link mechanism for packetised AMBA links: CHI, CXS, C2C and AXI5 credited transport (see [Handshakes](handshakes-and-flow-control.md)).
- The open AXI NoCs keep the protocol out of the routers. FlooNoC handles AXI in its network interfaces (W-FLOO), and Constellation is a protocol-independent transport (W-CONST).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Where coherence lives | CHI-H: coherence is part of the protocol carried by the network, with Home Nodes and snoops | ESP: a MESI directory protocol on three dedicated NoC planes (W-ESP); OpenPiton: P-Mesh coherence (W-PITON) | Different designs, not a conflict. The open projects use their own coherence protocols instead of CHI |
| Licence terms | FlooNoC: Solderpad for some folders (W-FLOO) | ProNoC: Solderpad 2.1 on one page, LGPL on another (W-PRONOC); CONNECT: non-commercial only (W-CONNECT) | Each project sets its own terms. Read the LICENSE file in the repository |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Never send a flit without a credit, and never use a credit in the cycle it arrives (CHI-H §B14.2; AXI-L §A2.4.1).
- Give each message class that can block another its own buffers or Resource Plane. CHI's channel-dependency rules show which dependencies are allowed (CHI-H §B13.4.1).
- An AXI network interface needs a reorder buffer, or a rule that keeps same-ID traffic on one path, to preserve AXI ordering (AXI-L §A5.3).
- Model first: run your topology and traffic in BookSim 2 or Garnet, then build RTL.
- A good learning path: read FlooNoC's network interface code alongside the AXI articles in this wiki, then Constellation's routing compiler for deadlock-free routing.

## Related articles

- [Interconnect, topology and bridges](interconnect-topology-and-bridges.md)
- [CHI: Coherent Hub Interface](chi-architecture.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Transaction IDs and ordering](transaction-ids-and-ordering.md)
- [Bridges, adapters and converters](bridges-and-adapters.md)
- [Chiplets and chip-to-chip](chiplets-and-chip-to-chip.md)
- [QoS and traffic modelling](qos-and-traffic-modelling.md)

## Sources

AXI-L, CHI-H, G-CHI, C2C-B, NIC400-J. See [Source key](sources.md).

### Web references (not specifications; read 2026-11-23)

| Code | Reference |
|---|---|
| W-FLOO | FlooNoC, [github.com/pulp-platform/FlooNoC](https://github.com/pulp-platform/FlooNoC); paper: Fischer et al., [arXiv 2409.17606](https://arxiv.org/abs/2409.17606) |
| W-CONST | Constellation, [Chipyard documentation](https://chipyard.readthedocs.io/en/stable/Generators/Constellation.html); paper: Zhao et al., NoCArc 2022 ([PDF](https://par.nsf.gov/servlets/purl/10439921)) |
| W-ESP | ESP, [esp.cs.columbia.edu](https://www.esp.cs.columbia.edu/); paper: Mantovani et al., ICCAD 2020 ([PDF](https://sld.cs.columbia.edu/pubs/mantovani_iccad20.pdf)) |
| W-PITON | OpenPiton P-Mesh, Balkind et al. ([CACM research highlight](https://jbalkind.github.io/docs/balkind-op-cacmrh.pdf)); BYOC, [github.com/bring-your-own-core/byoc](https://github.com/bring-your-own-core/byoc) |
| W-PRONOC | ProNoC, [OpenCores page](https://opencores.org/projects/an-fpga-implementation-of-low-latency-noc-based-mpsoc) and [BSC page](https://bsc.es/research-and-development/software-and-apps/software-list/pronoc) |
| W-OSF | OpenSoC Fabric, [github.com/LBL-CoDEx/OpenSoCFabric](https://github.com/LBL-CoDEx/OpenSoCFabric) |
| W-CONNECT | CONNECT, [users.ece.cmu.edu/~mpapamic/connect](https://users.ece.cmu.edu/~mpapamic/connect/?id=gen) |
| W-TLGEN | OpenTitan [bus specification](https://opentitan.org/book/hw/ip/tlul/) and [tlgen](https://opensecura.googlesource.com/3p/lowrisc/opentitan/+/refs/heads/master/util/tlgen) |
| W-BOOKSIM | BookSim 2, [github.com/booksim/booksim2](https://github.com/booksim/booksim2) |
| W-GARNET | gem5 Garnet, [gem5 documentation](https://m5sim.org/documentation/general_docs/ruby/garnet-2) |
| W-NOXIM | Noxim, [github.com/davidepatti/noxim](https://github.com/davidepatti/noxim) |
