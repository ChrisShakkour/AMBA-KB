# Quality of Service (QoS) and traffic modelling (ATP)

> How AMBA lets important traffic go first and lets busy targets slow down speculative traffic, plus ATP, a standard way to *describe* traffic for simulation and system sizing.

## In plain words

Not every transaction is equally urgent. A display controller that misses its deadline makes the screen flicker, whereas a background copy can wait. **QoS** signals let the system prefer some traffic. Other signals let a busy memory controller say "I'm nearly full, back off". **ATP** (Adaptive Traffic Profiles) is not a bus at all. It is a compact *language* for "this component issues 64-byte reads at 2 GB/s with up to 8 outstanding", used to model and test systems before the real RTL exists.

## QoS mechanisms by protocol

| Mechanism | Protocol | What it does |
|---|---|---|
| `AxQOS[3:0]` | AXI4+ | A per-request priority hint, where higher means more important. Exact use is system-defined. Interconnects often overwrite it from programmable registers (AXI-L §A4.8.1) |
| `VAWQOSACCEPT` / `VARQOSACCEPT` | AXI5 | The Subordinate says "right now I accept only QoS ≥ N without delay", so a Manager can avoid sending requests that would block (AXI-L §A4.8.2) |
| `BBUSY` / `RBUSY` | AXI5 | 2-bit "how busy am I" in responses. Managers can reduce speculative traffic (AXI-L §A3.3.3) |
| Resource Planes (credited) | AXI5, CHI, C2C | Independent credit pools, so one class of traffic cannot block another (AXI-L §A2.4.2) |
| QoS field, Retry and PCrdGrant | CHI | QoS value per request. A Completer can retry low-priority requests and grant credits by priority (CHI-H §B11.1; G-CHI §4) |
| Completer Busy, Data Source | CHI | Busy indication. DataSource reports where data came from (for example whether a PrefetchTgt helped) (CHI-H §B11.2, §B11.6; G-CHI §8) |
| MPAM | AXI5, CHI-D+ | Partition IDs for resource partitioning and monitoring between VMs and apps (AXI-L §A12.1; G-CHI §11) |

### The key AXI rule
"AXI ordering rules take precedence over ordering for QoS purposes" (AXI-L §A4.8.1). QoS only chooses between requests that the protocol allows to be reordered.

### CHI QoS and monitoring fields in detail (CHI-H ch. B11)
- **QoS** (4 bits, higher = more urgent) is set by the source and may change over time, for example as latency builds up. A requester may **send the same transaction again with a higher QoS**. The Completer must treat the copies as separate requests, and if one copy gets RetryAck the requester may cancel it and return the credit (CHI-H §B11.1).
- **DataSource** (8 bits since CHI-G, in CompData, DataSepResp and snoop data) has four subfields (CHI-H §B11.2):
  - `CompleterDistance` [1:0]: 1 = own cluster … 4 = remote socket. It is incremented as the response crosses cluster, die and socket boundaries.
  - `CompleterType` [4:2]: Default, three memory groups (recommended: DRAM, CXL, HBM), Cache Snoop Hit, and two system-cache groups.
  - `HitD` [5]: the line was Dirty where it was found.
  - `Functional` [7:6]: for memory, whether an earlier **PrefetchTgt was useful**; for caches, *unused prefetch* or *late prefetch*.
- **DataTarget** (7 bits, requester → HN-F) is the reverse direction: `UnusedPrefetch`, `Replacement` (how likely the line is to be reused), `CacheLevel` (place it here or 1–2 levels further down) and `Unique` (Issue H: also make it Unique there) (CHI-H §B11.3).
- **CBusy** (3 bits, in responses) tells the requester how busy the completer is. The encoding is implementation-defined. CHI-H's example uses bit [2] for "several cores active" and [1:0] for tracker occupancy (<50%, >50%, >75%, >90%), so a prefetcher can switch between aggressive and conservative modes (CHI-H §B11.6).
- **MPAM**: 0, 12 or 15 bits. `MPAM_9_1` = 9-bit PartID + 1-bit PerfMonGroup + 2-bit MPAMSP. `MPAM_12_1` = 12-bit PartID. On SNP it is used only in stash snoops. Values must be propagated onto any interface that supports MPAM, and requests to the Subordinate copy the values from the original request (CHI-H §B11.4). AXI5 has the same two options, plus a 1-bit `MPAM_NS` form without RME (AXI-L §A12.1).
- **TraceTag** (1 bit per flit) must be copied into every response and spawned packet, so one transaction can be traced through the system (CHI-H §B11.7). AXI5 has `xTRACE` signals with the same purpose (AXI-L §A12.3).

## ATP: Adaptive Traffic Profiles (ATP-A)

- **What it is**: ATP is "a specification of the dynamic characteristics of an interface". It focuses on AXI, and profiles are described from the master's point of view (ATP-A §1.1).
- **A traffic profile** = a fixed set of control-signal values + an address sequence + intra-transaction timing + inter-transaction timing + an optional start event + an optional output event (ATP-A §1.3).
- Address patterns: **sequential**, **two-dimensional** (base, X range, stride, Y range), **random** or **from a file**. An environment without random support falls back to sequential (ATP-A §2.2). IDs can be fixed, cycled, unique or from a file (ATP-A §2.2.3).
- **Timing model**: a simple FIFO. A read profile drains its FIFO at `Rate` bytes per cycle and issues a read whenever there is room for the returning data. A write profile fills its FIFO and issues a write when enough data is present. `TxnLimit` caps outstanding transactions (ATP-A §4.2). The spec describes three observable phases: Initial Peak Rate, Constrained Peak Rate (latency-bound) and Average Rate (ATP-A §4.5). Only *primary* timing parameters, such as time between transactions or initial read latency, adapt dynamically. Secondary ones are fixed per profile (ATP-A §3.1).
- Profiles can run **concurrently** (a *Traffic Profile Group*) or **in sequence** (a *Traffic Profile Sequence*), and can be **linked** so that one profile's progress drives another. A whole-system run is a *Scenario* (ATP-A §1.3).
- Uses (ATP-A §1.2):
  - Stand in for real components in simulation.
  - Define dynamic interface requirements when sizing interconnects.
  - Check bandwidth and latency in monitors.
  - Capture observed traffic (lossy).
  - Replay the same stimulus in TLM, RTL, emulation, FPGA or silicon.
- *(External pointer, not one of this wiki's raw sources:)* Arm publishes an open-source implementation, the ATP Engine, at github.com/ARM-software/ATP-Engine.

## Where the sources agree

- QoS values are **hints**. The protocol does not mandate an arbitration algorithm (AXI-L §A4.8.1; AMBA2 §1.5 already said "any arbitration algorithm … can be implemented").
- A Subordinate may delay low-priority requests but "it is recommended that such a transaction is not delayed indefinitely" (AXI-L §A4.8.2). Starvation avoidance is the system's job.

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Where QoS lives in the protocol | AMBA2 (AHB): arbitration priority inside the bus arbiter, with SPLIT letting lower-priority masters through (§3.9.5) | AXI4+: per-transaction `AxQOS` values that any component may use | *Editor's note (not from the sources):* Shared-bus arbitration was replaced by per-transaction priority in point-to-point fabrics |
| What DataSource tells you | CHI-F: a 5-bit DataSource field. G-CHI §8 describes it as reporting where data came from | CHI-H §B11.2 (since CHI-G): **8 bits** with defined subfields (distance, completer type, Hit-Dirty, prefetch usefulness) | CHI-G standardised the encoding for multi-die and heterogeneous-memory systems, so performance tools can read it across vendors (CHI-H Table C5.9) |
| MPAM field width in CHI | CHI-F: as first published | CHI-F.b: "MPAM field width has been corrected to 12 bits". CHI-G adds the 15-bit `MPAM_12_1` option (CHI-H Tables C5.8, C5.9) | A documentation defect fixed in F.b, then a real extension for larger PartID spaces |
| ATP's naming | ATP-A (2019) describes "master" and "slave" traffic profiles | Current AXI/CHI specs use Manager/Subordinate | ATP-A has not been re-issued since the terminology change. *ATP master* = Manager |
| ATP's scope | G-AXI §2: ATP is for "modeling high-level memory access behavior" | ATP-A §1.2 also lists using profiles as a **low-gate-count hardware traffic generator** inside an SoC for testing | The guide summarises only the main use. The spec is broader |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- If your Manager has several traffic types, give it a **programmable QoS register** per stream rather than hard-coded values (AXI-L §A4.8.1 recommendation).
- In a memory controller, implement `VAxQOSACCEPT` from queue occupancy so that high-priority Managers aren't blocked behind low-priority ones.
- Use DataSource as a *qualifier* for CBusy. For example, ignore CBusy on data that came from a forwarding snoop, so a busy peer cache does not throttle your memory prefetcher (CHI-H §B11.6).
- Drive DataSource[7:2] with a legal encoding even when you have nothing useful to say: use the Default encodings (CHI-H §B11.2.7).

## Related articles

- [Handshakes and flow control](handshakes-and-flow-control.md) (resource planes, retry)
- [CHI architecture](chi-architecture.md)
- [Interconnect, topology and bridges](interconnect-topology-and-bridges.md)

## Sources

AMBA2, AXI-L (read in full), CHI-H (read in full), ATP-A, G-AXI, G-CHI. See [Source key](sources.md).
