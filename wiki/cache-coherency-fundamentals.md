# Cache coherency fundamentals

> Why systems with caches need coherency, the three ways AMBA achieves it (don't cache, software maintenance, hardware snooping), the cache-line states, shareability domains, and the "Points of …" vocabulary.

## In plain words

Each CPU keeps copies of memory in its own cache. If CPU A changes its copy, CPU B's copy is now **stale**. *Coherency* means everyone agrees on the latest value of each address. Formally: "writes to the same address location by two Managers are observable in the same order by all participating Managers" (AXI-L §A8.3).

AMBA offers three approaches (AXI-L §A8.3):
1. **Don't cache it**: use Non-cacheable transactions (the System Domain). Always correct, but slow.
2. **Software coherency**: software issues **Cache Maintenance Operations (CMOs)**, *clean* (write dirty data back) and *invalidate* (throw a copy away), at the right times. Efficient when sharing is predictable, but "coherency bugs in software can be easy to introduce and difficult to debug".
3. **Hardware coherency**: the interconnect **snoops** other caches automatically (ACE, CHI).

There is also **I/O coherency**: a device without a cache (DMA, NIC) reads and writes through the coherent system so it sees CPU-cached data. This is "one-way coherency" (G-AXI §2; ACE-Lite, RN-I in CHI).

## Cache-line states

Each line has three characteristics (AXI-Hc §D1.2.3; G-CHI §3):
- **Valid / Invalid**: present or not.
- **Unique / Shared**: the only copy, or possibly one of several.
- **Clean / Dirty**: Dirty means this cache must eventually update memory (or pass that duty on).

| State | ACE (5 states) | CHI (7 states) | Can store without telling others? |
|---|---|---|---|
| Invalid | I | I | — |
| UniqueClean | UC | UC | Yes |
| UniqueDirty | UD | UD | Yes |
| SharedClean | SC | SC | No, must notify |
| SharedDirty | SD | SD | No, must notify |
| UniqueCleanEmpty | — | **UCE** (owned, no valid bytes) | Yes |
| UniqueDirtyPartial | — | **UDP** (some bytes valid) | Yes |

Rules (AXI-Hc §D1.2.3): a Unique line is in only one cache. A line in several caches is Shared in all of them. If a line is modified relative to memory, exactly **one** cache holds it Dirty. Discarding a Shared copy needs no notification, so a "Shared" line may in fact be the only copy.

CHI supports both **MESI** and **MOESI** style caches. CHI-B added ReadNotSharedDirty/SnpNotSharedDirty for caches without an SD ("Owned") state (CHI-H §B1.1.2; G-CHI §16). Since CHI-G, the `Cache_State_UDP` and `Cache_State_SD` properties let a component declare that it never uses those states, so the system can simplify (CHI-H §B16.1.20–21).

What each state may do when snooped (CHI-H §B4.1):
- **UCE** must never return or forward data (it has none).
- **UDP** must return its partial data to Home and must never forward it.
- **UD/SD** (Dirty) must always return data if the snoop removes the dirtiness.
- **SC** returns data only if asked (RetToSrc), and even then only "recommended".

### Cache line size
- CHI: always **64 bytes**, aligned. All coherency is done at that granule (CHI-H §B1.5).
- AXI5: a `Cache_Line_Size` property, 16 to 2048 bytes, default 64. It **must be 64** to be compatible with CHI (AXI-L §A8.2).

## Snooping vs directories

- **Broadcast snooping**: ask every caching agent. Simple, but it doesn't scale.
- **Snoop filter / directory**: track who might hold each line and snoop only them. CHI was designed "adding support for snoop filters and directory-based systems for snoop scaling" (G-CHI §3; CHI-H §B1.1.2). ACE also has optional external snoop filter support (AXI-Hc ch. D10).
- A CHI snoop filter may be **precise** (knows exactly which RN-F has the line and in what state) or **imprecise**. With an imprecise or absent filter, Home must assume the worst. For example, it must send data in response to MakeReadUnique in case the requester lost its copy (CHI-H §B4.7.1.1). Home may also send a **SnpQuery** to learn the exact state.
- A snoop filter may evict an entry by sending a "back-invalidation" snoop (SnpUnique or SnpCleanInvalid) that no request caused (CHI-H §B4.4).
- **Evict** is only a hint in CHI. Home may reply Comp without updating its filter (CHI-H §B5.2.4).
- With several interfaces on one RN, a snoop filter can target the right interface only if it knows the requester's **address-striping hash**. CHI recommends advertising it (CHI-H §B13.7.1.1).

## Shareability domains

A domain says which other Managers must be kept coherent with this access.

| Domain | ACE (AXI-Hc §D1.6) | AXI5 Issue L (AXI-L §A8.3) | CHI |
|---|---|---|---|
| Non-shareable | Single Manager | Not visible to others. Sharing needs CMOs | Non-snoopable |
| Inner Shareable | Some Managers | — (merged) | — |
| Outer Shareable | Inner + possibly more | — (merged) | — |
| Shareable | — | Visible to all Managers that mark it Shareable | Snoopable (`SnpAttr`=1) |
| System | All Managers. Must be Non-cacheable | All Managers. Device requests must use System | — |

In CHI the memory request says only *snoopable or not*. The old Inner/Outer split survives in one place: in a **DVMOp**, `SnpAttr` selects the **Inner (0) or Outer (1) DVM domain**, and the optional `BROADCASTTLBIINNER`/`BROADCASTTLBIOUTER` pins control TLBI broadcast (CHI-H §B8.4.1).

## The "Points of …" vocabulary (CHI-H §B1.3)

| Term | Meaning |
|---|---|
| **PoS**, Point of Serialisation | Where the order between requests from different agents is decided (usually the Home Node) |
| **PoC**, Point of Coherence | Where all agents are guaranteed to see the same copy (in CHI, typically the HN-F) |
| **PoP / PoDP**, Point of (Deep) Persistence | Where a write survives power loss (and, for deep persistence, battery failure) |
| **PoPA**, Point of Physical Aliasing | Beyond it, the same address in different PAS is the same location (RME) |
| **PoE**, Point of Encryption | Writes are encrypted from here on (MEC) |
| **PoPS**, Point of Physical Storage | The real memory, as far as a write can go |

## Cache maintenance operations (CMOs)

| CMO | Effect | AXI5 (AXI-L ch. A9) | CHI (CHI-H §B4.2.2) |
|---|---|---|---|
| CleanShared | Write any dirty copy back, keep clean copies | Yes | Yes |
| CleanSharedPersist (+Deep) | …and make it reach PoP (or PoDP) | Yes (CSP, CSDP) | Yes, with `Deep` bit. CleanSharedPersistSep gives a separate **Persist** response |
| CleanInvalid | Write back, then drop all copies | Yes | Yes |
| CleanInvalidPoPA | CleanInvalid across all PAS (RME) | Yes | Yes |
| CleanInvalidStorage | …to the Point of Physical Storage (for example to scrub poison) | Yes (Issue L) | Yes |
| MakeInvalid | Drop copies, **dirty data may be lost** | Read channel only | Yes |

Practical rules from the full specs:
- CMOs are **mandatory to act on**, unlike hints such as Evict or InvalidateHint (AXI-L §A9.2).
- AXI-L recommends issuing CMOs on the **write channel** (`AWCMO`). Read-channel CMOs are legacy, and MakeInvalid exists only on the read channel (AXI-L §A9.5, §A9.7).
- Both specs allow a **write combined with a CMO** (AXI WritePtlCMO/WriteFullCMO; CHI Combined Write). The receiver may split it into the write followed by the CMO. The CMO part is always treated as the most pervasive (AXI-L §A9.6; CHI-H §B4.2.4).
- A persistent CMO can have **two responses**, Completion and Persist, which may arrive in either order (AXI `BCOMP`/`BPERSIST`; CHI Comp + Persist or CompPersist) (AXI-L §A9.8.4; CHI-H §B2.3.5).
- Neither protocol allows CMOs to Device memory. From CHI Issue H, CMOs may target only Cacheable memory (CHI-H Table C5.11).
- With MEC, CMOs to the PoPA are enough to reach everything before the PoE, so no separate "PoE CMO" exists (CHI-H §B10.6.4).

## Where the sources agree

- The same **valid/unique/dirty** decomposition is used in ACE and CHI. CHI "uses the same terms as ACE … and adds partial and empty cache line states" (G-CHI §3).
- Main memory does **not** have to be up to date while cached copies exist; it only has to be updated before the last copy is discarded (AXI-Hc §D1.2.2).
- System-domain accesses must not be cached (AXI-Hc §D1.6; AXI-L §A8.3.1).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Number of cache states | ACE: **5** states (AXI-Hc §D1.2.3) | CHI: **7** states (G-CHI §3) | CHI-H §B4.1: the Empty and Partial states let a requester obtain permission to store *without first fetching the data*, which saves bandwidth when the whole line (or part of it) will be overwritten |
| Inner vs Outer Shareable | ACE (AXI-Hc §D1.6): separate Inner and Outer Shareable domains | AXI-L §A8.3.4: only one "Shareable" domain. Old 0b01/0b10 encodings both mean Shareable, and 0b10 is recommended. CHI-B deprecated Inner/Outer, so requests are only snoopable or not (G-CHI §16) | AXI-Hc §F5.1 gives the reason for the ACE5 deprecation: "to simplify the specification and clarify the expected use of domains". G-CHI §16 records the same step for CHI-B without giving a reason |
| Default domain without AxDOMAIN | AXI-L §A8.3.4 text: Cacheable → **Non-shareable** | AXI-L §A8.3.4 list below the table: Cacheable → **Shareable** | An internal contradiction in AXI Issue L. Document your choice |
| Is Inner/Outer gone everywhere? | G-CHI §16: CHI-B deprecated Inner/Outer Shareable | CHI-H §B8.4.1: DVM requests still use SnpAttr to choose an **Inner or Outer DVM domain** | Only *memory* shareability was merged. TLB maintenance can still target a smaller (Inner) domain |
| Cache line size | CHI-H §B1.5: fixed **64 B** | AXI-L §A8.2: `Cache_Line_Size` 16–2048 B (default 64) | *Editor's note (not from the sources):* AXI also serves non-Arm and accelerator systems. When AXI meets CHI the value must be 64 |
| Number of Arm coherency approaches | AXI-L §A8.3 lists **three** (Non-cacheable, software CMOs, hardware snooping) | G-SYS §4.4.1: AMBA "offers a range of interface options that support non-coherent, IO-coherent, and fully coherent traffic" | Different viewpoints: system *methods* vs interface *capabilities*. They are compatible |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- A non-caching DMA engine needs **I/O coherency** only if the CPUs cache the buffers. Otherwise mark the buffers Non-cacheable, or have software clean and invalidate around each DMA.
- Never write back a **Clean Non-shareable** line from an intermediate cache: it might overwrite a newer Dirty copy elsewhere (AXI-L §A8.3.2).

## Related articles

- [ACE coherency extensions](ace-coherency-extensions.md)
- [CHI architecture](chi-architecture.md)
- [Memory types and cache attributes](memory-types-and-cache-attributes.md)
- [DVM and address translation](dvm-and-address-translation.md)

## Sources

AXI-Hc, AXI-L (read in full), CHI-H (read in full), G-AXI, G-CHI, G-SYS. See [Source key](sources.md).
