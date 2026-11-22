# ACE: AXI Coherency Extensions (and ACE-Lite, ACE5 variants)

> ACE adds hardware cache coherency to AXI4 by adding snoop channels and extra fields. It was the AMBA 4 answer to coherent multi-core systems and is now **superseded by CHI**, but much existing IP still uses it.

## In plain words

Take an AXI4 interface, then add:
- extra fields on AR/AW that say *what kind of coherent access* this is (`AxSNOOP`, `AxDOMAIN`, `AxBAR`),
- three new channels the interconnect uses to **ask your cache questions** ("do you have address X? Give it to me / invalidate it"): **AC** (snoop address), **CR** (snoop response), **CD** (snoop data),
- two acknowledge wires, **RACK** and **WACK**, to say "I have seen my read or write complete".

That is ACE. **ACE-Lite** is the lightweight version for agents *without* a coherent cache (for example a DMA engine). It keeps the extra AR/AW fields but has no snoop channels (AXI-Hc §D11.1).

## Key ideas

### What ACE adds (AXI-Hc §D1.3)
| Where | Signals | Purpose |
|---|---|---|
| AR | `ARSNOOP[3:0]`, `ARDOMAIN[1:0]`, `ARBAR[1:0]` | Coherent read type, domain, barrier |
| AW | `AWSNOOP[2:0]`, `AWDOMAIN[1:0]`, `AWBAR[1:0]`, `AWUNIQUE` | Coherent write type, and so on |
| R | `RRESP[3:2]` | `RRESP[2]` = PassDirty, `RRESP[3]` = IsShared |
| AC | `ACVALID/READY`, `ACADDR`, `ACSNOOP[3:0]`, `ACPROT` | Snoop request from interconnect to cache |
| CR | `CRVALID/READY`, `CRRESP[4:0]` | One snoop response per snoop |
| CD | `CDVALID/READY`, `CDDATA`, `CDLAST` | Optional snoop data |
| — | `RACK`, `WACK` | Manager acknowledges read/write completion |

### A coherent load, step by step (AXI-Hc §D1.3.4)
1. The Manager issues a read on AR.
2. The interconnect snoops the other caching Managers on AC.
3. They answer on CR, and on CD if they have the data.
4. If someone supplied data, the interconnect returns it on R. Otherwise it reads main memory.
5. The Manager asserts **RACK**.

For a store to a Shareable line, the Manager first removes all other copies so that it holds the line Unique (AXI-Hc §D1.3.4):
- **Partial-line store, no copy held**: ReadUnique (fetches the data).
- **Full-line store**: MakeUnique (no data is returned, only the response).
- **Partial-line store, a Shared copy already held**: CleanUnique. Other copies are removed and any Dirty copy is written to memory, but no data comes back.

### Transactions and encodings (AXI-Hc §D1.4, §D3.1)
| ARSNOOP | Transaction | AWSNOOP | Transaction |
|---|---|---|---|
| 0000 | ReadNoSnoop (Non-shareable/System) or ReadOnce (Inner/Outer) | 000 | WriteNoSnoop or WriteUnique (by domain) |
| 0001 | ReadShared | 001 | WriteLineUnique |
| 0010 | ReadClean | 010 | WriteClean |
| 0011 | ReadNotSharedDirty | 011 | WriteBack |
| 0111 | ReadUnique | 100 | Evict |
| 1011 / 1100 | CleanUnique / MakeUnique | 101 | WriteEvict (needs `AWUNIQUE`) |
| 1000 / 1001 / 1101 | CleanShared / CleanInvalid / MakeInvalid | | |
| 1110 / 1111 | DVM Complete / DVM Message | | |

A component without a cache can tie AxSNOOP to zero and use only AxDOMAIN. Its transactions then become ReadNoSnoop/WriteNoSnoop or ReadOnce/WriteUnique (AXI-Hc §D3.1.3).

Rules a junior engineer must not miss:
- **Domain vs memory type**: Device transactions must use the System domain, and Cacheable transactions must not (AXI-Hc §D3.1.1).
- **Cache-line-size transactions** (ReadClean, ReadShared, ReadUnique, CleanUnique, MakeUnique, CMOs, WriteLineUnique, WriteEvict, Evict) must be full lines and Regular. ReadOnce and WriteUnique may be smaller, but FIXED bursts are not allowed, so an AXI→ACE-Lite converter must translate FIXED (AXI-Hc §D3.1.5).
- ACE cache lines are **16 bytes minimum**, and at most the smaller of 2048 bytes or 16 × data-bus width (AXI-Hc §D3.1.5). Arm recommends a single 64-byte line for new Managers (AXI-Hc §D14.1).
- **RACK/WACK** last one cycle, must not wait on any other transaction, and are sent for *every* transaction. The interconnect uses them to hold back a snoop to a line until the Manager has finished its own transaction to that line. The spec explains they are needed because there can be a delay, for example a register slice or clock-domain crossing, between the interconnect and the Manager (AXI-Hc §D3.3, §D6.2.1).
- **Snoop responses are ordered**: one CR response per AC request, in order. CD data is in the same order, has no byte strobes, and may be narrower than the R/W buses (AXI-Hc §D3.7–§D3.8).
- `CRRESP[4:0]` = {WasUnique, IsShared, PassDirty, Error, DataTransfer}. PassDirty without DataTransfer is illegal (AXI-Hc §D3.7).
- **Deadlock rules**: AR (and WriteUnique/WriteLineUnique) may wait for AC, and AC may wait for WriteBack/WriteClean/WriteEvict/Evict/WriteNoSnoop, but never for WriteUnique/WriteLineUnique (AXI-Hc §D5.2.5, §D6.6.1).
- A snooped Manager may always answer any snoop as if it were ReadUnique, which simplifies the snoop port (AXI-Hc §D5.1.3).

### Other ACE features
- **Barriers** (memory and synchronisation), using AxBAR, with shareability domains defining how far they reach (AXI-Hc §D8).
- **DVM** messages for TLB and branch-predictor maintenance (AXI-Hc §D13). See [DVM and address translation](dvm-and-address-translation.md).
- **Cache maintenance** transactions (CleanShared, CleanInvalid, MakeInvalid, persistence CMOs) (AXI-Hc ch. D7).

### ACE5 variants (AMBA 5, AXI-Hc Part F; AXI-L §B2.1)
| Variant | For | Notes |
|---|---|---|
| ACE5 | Fully coherent caching agents | ACE plus AXI5 features |
| ACE5-Lite | I/O-coherent agents without caches | Adds AXI5 features |
| ACE5-LiteDVM | I/O-coherent agents that must receive DVM (for example an SMMU) | |
| ACE5-LiteACP | Accelerators tightly coupled to a CPU cluster. It supersedes the AMBA 4 ACP of Issue E | 128-bit data, length 1 or 4, INCR only, Write-Back only, Non-shareable or Outer Shareable, no exclusives, QoS or REGION (AXI-Hc §F4.1) |

Which AMBA 5 features each variant may use (AXI-Hc Part E, Table G3-1):
- **ACE5** (fully coherent) may *not* use Atomics, stashing, deallocating reads, MTE, Prefetch or WriteZero. An ACE5 Manager does atomics locally in its own cache (AXI-Hc §E1.1.10).
- **ACE5-Lite / ACE5-LiteDVM** may use all of them. ACE5-LiteDVM is ACE5-Lite plus AC and CR channels to *receive* DVM messages, "for IO coherent components that include SMMU functionality". It may not use untranslated transactions, "since this interface is intended to be used after translation has occurred" (AXI-Hc §F3.1).
- **Coherency Connection** (`SYSCOREQ/SYSCOACK`) applies to ACE5 and ACE5-LiteDVM. It connects the Manager to snoops *and* DVM messages on AC (AXI-Hc §E1.8).

## Where the sources agree

- ACE is coherent AXI4 based on a **5-state** model with snoop channels AC/CR/CD (AXI-Hc §D1.2; G-AXI §2; G-CHI §3).
- ACE-Lite gives **one-way** (I/O) coherency (AXI-Hc §D11.1; G-AXI §2).
- CHI is ACE's successor. CHI's CompAck "has similar functionality to RACK/WACK in ACE" (G-CHI §4).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Is ACE part of the current AXI spec? | AXI-Hc (2021): yes, Part D (ACE) and Part F (ACE5 variants) | AXI-J/AXI-L §B4.1: "ACE and ACE5 content is removed … AMBA CHI is recommended for fully coherent agents" | Issue J removed the ACE content from the AXI spec (AXI-L §B4.1). To design or verify ACE IP you must use **Issue H.c**, the last issue that contains it |
| Do you still need ACE5-Lite / ACE5-LiteDVM? | AXI-Hc: these are separate interface classes with their own signal lists | AXI-L §B2.1.2–B2.1.3: "an AXI5 interface is recommended for new designs as it now supports all functionality" | From Issue J, AXI5 can enable every ACE5-Lite feature through properties (Shareable_Transactions, DVM_Message_Support…) |
| What ACE5-LiteDVM contains | AXI-Hc §F3.2: AC and CR channels (no CD) with `ACSNOOP`, `ACPROT` and `CRRESP`. `DVM_Message_Support` defaults to **Bidirectional** when not declared (§D13.1) | AXI-L §B2.1.3: "snoop data transfer and bidirectional DVM messages are not supported", and ACSNOOP, ACPROT and CRRESP are "no longer required" | AXI-L §B2.1.3 gives the reason: "the most common use-case … is for a system MMU to receive invalidation messages", while issuing DVMs "is mostly done by fully coherent CPUs, so is beyond the scope of this specification" |
| Barriers | ACE (AXI-Hc ch. D8): supported | AXI-Hc §F5.2: "From Issue F onward, barrier transactions are not supported in ACE5 and ACE5-Lite variant interfaces". CHI-B also deprecated barriers (G-CHI §16) | AXI-Hc says only that Managers needing ordering "must delay the issue of dependent requests until earlier transactions are complete". For CHI, G-CHI §16 adds that barriers generated by DMB/DSB "must terminate within the cores". A `Barrier_Transactions` property (default True, for legacy parts) tells you whether an interface still has AxBAR |
| Inner Shareable domain | ACE (AXI-Hc §D1.6): Inner and Outer Shareable are separate | AXI-Hc §F5.1: Inner Shareable is **deprecated** for ACE5 variants. Use Outer Shareable instead | The spec's stated reason: "to simplify the specification and clarify the expected use of domains" |
| How ACE is taught | G-AXI (2025) presents ACE as the AMBA 4 coherency solution and links it to big.LITTLE | G-SYS (2025): ACE "has been superseded by CHI" | G-AXI explains AMBA's history, while G-SYS states the current recommendation. Both match the specs of their era |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- If you integrate an existing ACE CPU, make sure your interconnect and VIP use **AXI H.c** rules. AXI-L checkers will not know about AC/CR/CD.
- A DMA that must see CPU-cached data needs only ACE-Lite (or, today, AXI5 with `Shareable_Transactions=True`), not full ACE.

## Related articles

- [Cache coherency fundamentals](cache-coherency-fundamentals.md)
- [CHI architecture](chi-architecture.md)
- [DVM and address translation](dvm-and-address-translation.md)
- [Protocol evolution and version differences](protocol-evolution-and-versions.md)

## Sources

AXI-Hc (read in full), AXI-J, AXI-L (read in full), G-AXI, G-CHI, G-SYS. See [Source key](sources.md).
