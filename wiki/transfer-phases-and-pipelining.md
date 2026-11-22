# Transfer phases and pipelining

> What happens cycle by cycle during one access, and how much overlap each protocol allows: none (APB), one stage of overlap (AHB), fully independent channels (AXI) or layered packets (CHI).

## In plain words

A memory access has two halves: *"where and what"* (address and control) and *"the data"*.
- **APB** does them one after another with no overlap, which makes it simple and slow (at least 2 cycles per access).
- **AHB** overlaps them like an assembly line: while transfer *N* is in its data phase, transfer *N+1* is already presenting its address.
- **AXI** splits them onto separate one-way channels that do not have to line up in time at all, so many transactions can be in flight.
- **CHI** goes one step further: messages are packets (flits) that travel through a network.

## APB: SETUP then ACCESS

State machine (APB-E §4.1; AMBA2 §5.2.1):

```
 IDLE --(transfer)--> SETUP (PSEL=1, PENABLE=0) --(always, 1 cycle)--> ACCESS (PSEL=1, PENABLE=1)
 ACCESS --(PREADY=0)--> ACCESS                 (wait states, APB3+)
 ACCESS --(PREADY=1, no more)--> IDLE
 ACCESS --(PREADY=1, another transfer)--> SETUP
```

- SETUP lasts exactly **one** cycle. Address, direction, write data, strobes, protection and user bits must be valid in SETUP and **must not change** going into ACCESS or during ACCESS (APB-E §4.1).
- "The APB interface is not pipelined … Every transfer takes at least two cycles" (APB-E §1.1).
- Read and write data buses are separate, but "data transfers cannot occur concurrently because the read data and write data buses do not have their own individual handshake signals" (APB-E §2.1.2).

## AHB: address phase overlaps the previous data phase

- Every transfer = **one address/control cycle + one or more data cycles** (AHB-C §1.3).
- "The address phase of any transfer occurs during the data phase of the previous transfer. This overlapping … is fundamental to the pipelined nature of the bus" (AHB-C §3.1; AMBA2 §3.4).
- Transfer type on `HTRANS` (AHB-C §3.2):

| HTRANS | Name | Meaning |
|---|---|---|
| 00 | IDLE | No transfer. The Subordinate must give a zero-wait OKAY |
| 01 | BUSY | "I'm in a burst but not ready for the next beat". Address/control already show the next beat |
| 10 | NONSEQ | Single transfer or first beat of a burst |
| 11 | SEQ | Later beats. Address = previous + size (with wrapping if WRAPx) |

- **Waited transfers** limit what the Manager may change (AHB-C §3.7). While waited, it may change IDLE→NONSEQ (then hold), BUSY→SEQ in fixed bursts, or BUSY→anything in INCR bursts. The address may change only once, except during IDLE or after an ERROR.

## AXI: five independent channels

- Channels: **AW** (write request), **W** (write data), **B** (write response), **AR** (read request), **R** (read data + response) (AXI-L §A1.2).
- "The architecture does not require any fixed relationship between the channels". Write data may even arrive **before** its AW request (AXI-L §A2.5–A2.6).
- Required relations (AXI-L §A2.6):
  - B always follows the last W beat. R follows the AR request.
  - A Manager that issued AW must be able to send all the W data **without depending on other transactions**.
  - A Subordinate must not block **data-less** write requests because of other transactions' early write data (added in Issue K, AXI-L §B4.2).
- **Register slices**: any number of stages on any channel, as long as VALID and payload are delayed together (AXI-L §A2.5).
- **Outstanding transactions**: a Manager may issue new requests without waiting for earlier ones (AXI-L §A1.1). Contrast this with AMBA 2 AHB, where "the bus protocol only allows a single outstanding transaction per bus master" (AMBA2 §3.12.2).

## CHI: layers, messages and flits

| Layer | Unit | Job (CHI-H §B1.1.3) |
|---|---|---|
| Protocol | Transaction | Requests and responses at nodes, cache-state transitions, transaction flows, protocol-level flow control (retry) |
| Network | Packet | Packetise messages, add source and target Node IDs for routing |
| Link | Flit | Flow control between network devices (credits), deadlock-free channels |

- Four channels per direction: **REQ**, **RSP**, **SNP**, **DAT** (G-CHI §3). They appear as TX* or RX* on each node.
- Flit fields go **in parallel**, not serialised over several beats like PCIe (G-CHI §3).

## Other phase models

- **GFB**: separate pipelined address and data phases, like AHB, with commands on `FCMD` (GFB-Ab §1.1, §3.3).
- **ASB**: a transfer runs from falling edge to falling edge, with the response (WAIT/DONE/ERROR/LAST/RETRACT) driven in the clock-LOW phase (AMBA2 §4.3, §4.5).

## Where the sources agree

- Every bus-style AMBA protocol separates **address/control** from **data**. AMBA2 §3.3: "Every transfer consists of an address and control cycle [and] one or more cycles for the data". AHB-C, AXI and GFB describe it the same way (AHB-C §1.3; AXI-L §A1.1; GFB-Ab §1.1).
- **One clock edge.** AMBA 2 AHB and APB time everything on the rising edge. AMBA2 §5.1 lists the advantages: easier high-frequency operation, independence from clock mark-space ratio, simpler static timing analysis, easy test insertion, better rising-edge register libraries, and cycle-based simulation. AMBA 2 ASB is still timed from falling edge to falling edge (AMBA2 §1.4, §4.3). AMBA2 §1.8.1 recommends AHB "for all new designs" partly because of its single-clock-edge protocol. Later protocols keep the single rising edge (AHB-C §7.1; AXI-L §A2.1).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Is APB clocked? | INTRO96 §1.2.2: APB data access is "controlled by select and strobe only (i.e. **no clock**)", and "a single read or write cycle takes **5 clocks**" | AMBA2 §1.7 / ch. 5: "all signal transitions are only related to the **rising edge of the clock**", 2-cycle SETUP/ENABLE. APB-E: "every transfer takes at least two cycles" | AMBA 2 (1999) **redesigned APB** around PCLK and PENABLE. Rev D peripherals use a `PSTB` strobe and sample read data differently. AMBA2 §5.8 shows how to adapt them |
| Can APB signals glitch? | AMBA2 §5.2: address, write and select "may glitch during a transition from the ENABLE to SETUP states" | APB-E §4.1: the listed signals "must not change" between SETUP→ACCESS and within ACCESS (no statement on ACCESS→SETUP) | Both allow changes *between* transfers. AMBA2 says so explicitly, APB-E is just silent. Inside a transfer both require stability |
| APB clock edges | INTRO96 implies strobe-based (level) timing | AHB-C §7.1 adds `Stable_Between_Clock`: glitches between edges are allowed unless that property is True | *Editor's note (not from the sources):* Later specs make glitch-freedom an **explicit, optional property** instead of an assumption |
| Outstanding transactions on AHB | AMBA2 §3.12.2: one outstanding transaction per master. A master needing more must appear as several masters | AXI-L §A1.1: multiple outstanding addresses are a core feature | A design difference between protocols, not an error. Listed because juniors often assume AHB can pipeline more than one transaction ahead |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- An APB Completer can be a pure combinational read mux plus registered writes, with `PREADY` tied HIGH (APB-E §3.1.2).
- In AHB, register the address/control at `HREADY & HSEL & HTRANS[1]`, then use the registered copy during the data phase. *Editor's note (not from the sources): this is a common implementation pattern. AHB-C §4.2 only requires that "A Subordinate must only sample the HSELx, address, and control signals when HREADY is HIGH".*
- In AXI, never assume AW arrives before W. Buffer W data until its AW is seen, or use a skid buffer (AXI-L §A2.6).

## Related articles

- [Handshakes and flow control](handshakes-and-flow-control.md)
- [Bursts, sizes and alignment](bursts-sizes-and-alignment.md)
- [Transaction IDs and ordering](transaction-ids-and-ordering.md)
- [CHI architecture](chi-architecture.md)

## Sources

INTRO96, AMBA2, APB-E, AHB-C, AXI-L, CHI-H, GFB-Ab, G-CHI. See [Source key](sources.md).
