# Interconnect, topology and bridges

> How AMBA components are physically connected: a shared bus with an arbiter, a multiplexed bus, point-to-point links joined by an interconnect, or a network of routers. Also covers bridges that translate between protocols.

## In plain words

Imagine a road system. An **early AMBA bus** (ASB, AMBA 2 AHB) is a single road with a traffic light (the *arbiter*). Only one car (Manager) drives on it at a time, and a signpost (the *decoder*) tells the car which house (Subordinate) to stop at. **AHB-Lite** removes the traffic light by saying "one car per road". To have several cars you build a *multi-layer* junction. **AXI** gives every car its own private lane (a point-to-point link). An *interconnect* then acts as a big junction that routes many lanes. **CHI** is a city road network (ring, mesh or crossbar) with routers and addresses for every node.

A **bridge** is a translator at the border between two road systems, for example AXI→APB.

## Key ideas, protocol by protocol

### Shared bus with arbiter and decoder: ASB and AMBA 2 AHB
- ASB: centralised decoder and arbiter, multiple bus masters, **tri-state** bus, timing on the **falling** clock edge (INTRO96 §1.2.1; AMBA2 §1.4, ch. 4).
- AMBA 2 AHB keeps the arbiter and decoder but uses a **central multiplexor** instead of tri-states, and a single rising clock edge (AMBA2 §3.1–3.2).
  - Arbitration signals: `HBUSREQx`, `HGRANTx`, `HMASTER[3:0]`, `HLOCKx`, `HMASTLOCK`, `HSPLIT[15:0]`. Up to **16 masters** (AMBA2 §3.11.1).
  - A **default master** is granted when nobody else wants the bus, and it must issue only IDLE transfers (AMBA2 §3.11.6).
  - A **default slave** answers unmapped addresses with ERROR (AMBA2 §3.8).

### Single manager + multi-layer: AHB-Lite and AHB5
- AHB-Lite is a **single-master** bus. For several Managers you build a **multi-layer interconnect**, where each Manager gets its own layer and arbitration happens *per Subordinate* (AHB-A §1.3).
- The minimal fabric is a **decoder** (makes `HSELx`) plus a **read-data/response multiplexor** (AHB-C §1.1.3, ch. 4).
- Each Subordinate drives `HREADYOUT`. The interconnect combines these into the single `HREADY` that every component sees (AHB-C §3.1).
- AHB5 lets one Subordinate have **several HSELx inputs**, giving several logical interfaces in the address map (AHB-C §4.2.2).

### Point-to-point links + interconnect: AXI
- AXI defines **one interface definition** that is used Manager↔interconnect, interconnect↔Subordinate and Manager↔Subordinate (AXI-L §A1.2.1).
- Common topologies are shared request and data channels, a shared request channel with multiple data channels, or a fully multilayer fabric. Request bandwidth is usually much smaller than data bandwidth (AXI-L §A1.2.1.1).
- **IDs grow through the interconnect.** The interconnect appends Manager-port bits to AWID/ARID and strips them from BID/RID on the way back, so the IDs at a Subordinate are wider than at a Manager (AXI-L §A5.4).
- **Register slices** can be inserted on any channel because channels have no fixed timing relation (AXI-L §A2.5).
- **Region signalling** (`AxREGION`, 4 bits) lets the interconnect tell one physical Subordinate interface which of up to 16 logical regions is addressed (AXI-L §A4.7). This is the AXI counterpart of AHB5's multiple HSEL.

### Network of nodes: CHI
- CHI is "primarily topology-independent". It is typically built as a **crossbar** (small, low latency), a **ring** (medium) or a **mesh** (large, more wires, scales by adding rows and columns) (CHI-H §B1.2; G-CHI §2).
- Every node has a **Node ID**. A **System Address Map (SAM)** in each Request Node maps a physical address to a Home Node ID, and the Home Node's SAM maps it on to a Subordinate Node ID (G-CHI §3; CHI-H §B3.1).
- All RNs must have a **consistent SAM**, and addresses with no target must map to a node that returns an error (G-CHI §3).
- The interconnect may **remap TgtID** on the way, which is why write data is sent to the SrcID of the DBIDResp rather than to the original TgtID. **PrefetchTgt** uses a separate address map that points straight at the Subordinate Node (CHI-H §B2.4, §B3).
- A node may have **several interfaces**, or **replicated channels** on one interface, for bandwidth. Requests can be spread over interfaces with an address-striping hash such as XOR-ing masked address bits. Advertising that hash lets snoop filters target the right interface (CHI-H §B13.7).

### Bridges

For the full list of bridge and converter types, with real component examples, see [Bridges, adapters and converters](bridges-and-adapters.md).

- **AHB/ASB→APB bridge**: appears as *one* Subordinate on the system bus, latches address, data and control, and does a second-level decode to create the `PSELx` signals (AMBA2 §1.7, §5.4).
- **Error mapping** across bridges (APB-E §3.4.3; APB-B §2.3.3):
  - AXI→APB: `PSLVERR` → `RRESP`/`BRESP` = SLVERR.
  - AHB→APB: `PSLVERR` → `HRESP` = ERROR.
- **AHB→APB cost**: a read that immediately follows a write needs 3 wait states in the AMBA 2 example bridge (AMBA2 §5.6.3).
- **Narrow/wide adapters**: a 32-bit AHB Subordinate can sit on a 64-bit bus using `HADDR[2]` to pick a half. A Manager may only be put on a *narrower* bus if it never issues HSIZE larger than that bus (AMBA2 §3.15–3.16; AHB-C §6.3).
- **Address-width adaptation (AXI)**: a component with a smaller address space sits in an aligned window, and the interconnect adds or removes the high address bits (AXI-L §A3.1.5).

## Decode granules: why 1 KB and 4 KB matter

| Protocol | Rule | Reason |
|---|---|---|
| AHB (all) | The minimum region per Subordinate is **1 KB**. Incrementing bursts must not cross 1 KB | Guarantees a burst never crosses an address-decode boundary (AMBA2 §3.8; AHB-C §4.2) |
| AXI (all) | A transaction must not cross **4 KB** | Prevents crossing from one Subordinate to another and limits address increments (AXI-L §A3.1; AXI-Hc §A3.4) |
| AXI5 option | `Max_Transaction_Bytes` can be set below 4 KB (64…4096) | Lets a striped interconnect avoid splitting bursts (AXI-L §A3.1.3) |

## Where the sources agree

- A **default responder** must exist for unmapped addresses. It returns an error for real transfers and OKAY for IDLE/BUSY (AMBA2 §3.8; AHB-C §4.2.1). CHI likewise requires unmapped addresses to map to a node that gives an error (G-CHI §3).
- Interconnect design itself is **outside the scope** of the protocol specs (AHB-A §1.3; AHB-C §1.1.3; CHI-H §B1.2).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Who arbitrates | AMBA2: a single bus **arbiter** with request/grant wires per master is part of the protocol (§3.11) | AHB-A/AHB-C: no arbitration signals. Arbitration is hidden inside a multi-layer interconnect "outside the scope of this specification" | AHB-A §1.1 defines AHB-Lite as "a bus interface that supports a single bus master". For multiple masters, "slave arbitration must be performed by the multi-layer interconnect component" (AHB-A §1.3). The AHB-A glossary adds that "in most cases, the extra facilities provided by a full AMBA AHB interface are implemented more efficiently by using an AMBA AXI protocol interface" |
| How long a Subordinate may stall | AMBA2 §3.9.1: recommended no more than **16 wait states**, plus SPLIT/RETRY to free the bus | AHB-C §5.1.2: only "a predetermined maximum number of wait states" with no figure. SPLIT/RETRY no longer exist | AMBA2's stated reason for the 16-cycle figure is "to prevent any single access locking the bus for a large number of clock cycles" on a shared multi-master bus. *Editor's note (not from the sources): AHB-C gives no reason for dropping the figure. A likely one is that with one Manager per layer, a long stall no longer blocks other Managers* |
| Topology names | G-CHI §2 and CHI-H §B1.2 describe ring, mesh and crossbar | G-AXI §2 attributes "flexible topologies such as cross-bar, ring, mesh" to AXI5/ACE5 features "to align with … CHI" | The same bullet list (high-frequency non-blocking coherent transfer, layered model for cross-bar/ring/mesh topologies, stashing, far atomics, data protection) appears in G-SYS §4.4.1 as CHI features. The AXI specs (AXI-L) describe point-to-point interfaces and do not define ring or mesh topologies. The topology claim fits CHI |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- An AHB Subordinate must sample `HSELx`, `HADDR` and control **only when `HREADY` is HIGH** (AHB-C §4.2). Using `HREADYOUT` here is a classic bug.
- When you write an AXI interconnect, keep **ID width growth** in mind: Subordinates need `ID_W_WIDTH` = Manager ID width + log2(number of Managers) (AXI-L §A5.4).

## Related articles

- [Bridges, adapters and converters](bridges-and-adapters.md)
- [Networks-on-chip (NoC)](networks-on-chip.md)
- [Terminology and roles](terminology-and-roles.md)
- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Bursts, sizes and alignment](bursts-sizes-and-alignment.md)
- [Responses and errors](responses-and-errors.md)
- [CHI architecture](chi-architecture.md)

## Sources

INTRO96, AMBA2, APB-B, APB-E, AHB-A, AHB-C, AXI-Hc, AXI-L, CHI-H, G-AXI, G-CHI. See [Source key](sources.md).
