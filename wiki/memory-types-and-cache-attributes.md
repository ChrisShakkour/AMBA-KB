# Memory types and cache attributes

> The bits that tell the system *how* a transaction may be handled: whether it may be buffered, merged, split, cached or prefetched. In AHB these are `HPROT`, in AXI `AxCACHE`, in CHI `MemAttr`.

## In plain words

Writing to a UART's TX register is very different from writing to RAM. For the UART, each write must arrive exactly once, in order, unchanged. For RAM it's fine to combine two writes, read ahead, or keep a copy in a cache. **Memory attributes** carry that knowledge from the CPU's page tables onto the bus so that interconnects, buffers and caches can behave correctly.

Two big families:
- **Device** memory, for peripherals: no merging, no splitting, no speculation, and read data always from the real target.
- **Normal** memory, for RAM: may be modified, merged, prefetched and cached.

## The bits

### AXI `AxCACHE[3:0]` (AXI-L §A4.2)
| Bit | AWCACHE | ARCACHE | Meaning |
|---|---|---|---|
| [0] | Bufferable | Bufferable | The write response may come from an intermediate point |
| [1] | Modifiable | Modifiable | The transaction may be split, merged or widened. 0 = **Device** / Non-modifiable |
| [2] | **Other** Allocate | **Allocate** | Allocation hint: "this one" vs "the other direction" |
| [3] | **Allocate** | **Other** Allocate | |

Note that the Allocate and Other-Allocate bits **swap places** between reads and writes (AXI-L §A4.2).

### AXI memory types (AXI-L Table A4.4, simplified)
| ARCACHE | AWCACHE | Type |
|---|---|---|
| 0000 | 0000 | Device Non-bufferable |
| 0001 | 0001 | Device Bufferable |
| 0010 | 0010 | Normal Non-cacheable Non-bufferable |
| 0011 | 0011 | Normal Non-cacheable Bufferable |
| 1010 / 1110 | 0110 / 1110 | Write-Through (various allocate hints) |
| 1011 / 1111 | 0111 / 1111 | Write-Back (various allocate hints) |

### AHB `HPROT` (AHB-C §3.8–3.9)
| Bit | Name | Notes |
|---|---|---|
| [0] | Data/Instruction | 1 = data (a hint) |
| [1] | Privileged | |
| [2] | Bufferable | |
| [3] | Modifiable (formerly "Cacheable") | |
| [4] | Lookup | AHB5 extended memory types only |
| [5] | Allocate | AHB5 extended |
| [6] | Shareable | AHB5 extended. Must be 0 for Device |

`HPROT_WIDTH` is 0, 4 or 7, depending on the `Extended_Memory_Types` property (AHB-C Table 2-2). Device types are **Device-nE** (no early write response) and **Device-E** (early write response allowed) (AHB-C §3.9.3).

### Behaviour rules (AXI-L §A4.3.1; AHB-C §3.9.4–3.9.5 say essentially the same)
| Type | Response from final destination? | Merge writes? | Prefetch reads? | Split/modify? | Cache lookup? |
|---|---|---|---|---|---|
| Device Non-bufferable / Device-nE | Yes (read and write) | No | No | No | No |
| Device Bufferable / Device-E | Read yes, write may be early | No | No | No | No |
| Normal Non-cacheable | Depends on Bufferable | Yes | (reads may fetch more) | Yes | No |
| Write-Through | Early allowed | Yes | Yes | Yes | **Yes** |
| Write-Back | Early allowed, and the write need not reach memory | Yes | Yes | Yes | **Yes** |

**Non-modifiable means frozen**: address, size, length, burst type and protection must not be changed. The only allowed change is Bufferable→Non-bufferable. Non-modifiable bursts longer than 16 may be split (AXI-L §A4.2.2).

### Mismatched attributes (AXI-L §A4.3.2)
All Managers must agree on whether a region is cacheable. They may use different allocation hints, may access Normal Non-cacheable memory with Device transactions, and may access Bufferable memory with transactions that do not permit buffering. Breaking these rules is a **software protocol error**: coherency may be lost, but the system must not deadlock and the damage must stay inside that 4 KB region (AXI-L §A4.4).

### CHI (CHI-H §B2.8.3, §B13.10.22)
CHI carries equivalent information in the 4-bit `MemAttr` field, plus `SnpAttr` (snoopable or not) and `LikelyShared` (a hint that another RN will probably want the line):

| MemAttr bit | Name | 1 means |
|---|---|---|
| [3] | Allocate | Allocation recommended |
| [2] | Cacheable | A cache *must* be looked up |
| [1] | Device | Device memory |
| [0] | EWA | Early Write Acknowledge allowed (the CHI equivalent of Bufferable) |

CHI memory types:
- **Device nRnE**, **Device nRE**, **Device RE** (R = reordering allowed, E = early write acknowledgement allowed). Device RE relaxes ordering to the same endpoint, keeping only overlapping-address order. CHI-H does not use the Arm "G" (gathering) attribute at all.
- **Normal Non-cacheable**, Non-bufferable or Bufferable. CHI-H notes that Non-cacheable Non-bufferable is "an AXI memory type, not an ARM memory type".
- **Normal Write-Back**, Non-snoopable or Snoopable, Allocate or No-Allocate.
- There is **no Write-Through** type in CHI.

Rules worth knowing:
- Device accesses must use ReadNoSnp / WriteNoSnp*. CMOs and PrefetchTgt are not allowed to Device memory. Full-line writes to Device memory must be 64-byte aligned (CHI-H Table C5.10).
- Device accesses may be unaligned: the data covers the start address up to the next Size boundary, and the BEs mark only those bytes (CHI-H §B2.9).
- Mismatched attributes: if a line believed Non-snoopable is snooped, answer SnpResp_I without data. The interconnect must never expose a stale clean copy (CHI-H §B2.8.7).
- **Non-shareable but Cacheable** memory: with `Nonshareable_Cache_Maint = True` an RN-F must upgrade such accesses to snoopable ones, so that other agents can invalidate them remotely. RME requires this (CHI-H §B10.3.2, §B16.1.17). `Outer_Cacheable_Support` (Issue H) separately controls whether Non-snoopable Cacheable ReadNoSnp/WriteNoSnp may allocate in the system cache (CHI-H §B16.1.18).

### Other AXI5 hints and attributes (AXI-L ch. A8, A10–A11)
- **Prefetch** (`AWSNOOP` 0b01111): a data-less "please fetch this line" sent on AW with a B response. A later read that hits the prefetched data may get the **PREFETCHED** response (RRESP 0b100). It is the AXI equivalent of CHI PrefetchTgt (AXI-L §A8.6).
- **ReadOnceCleanInvalid / ReadOnceMakeInvalid**: reads that also hint "I won't need this again". ROMI may throw away dirty data, so use it with care (AXI-L §A8.8).
- **InvalidateHint**: a data-less hint that may expose old values. Watch the security implications (AXI-L §A8.9).
- **WriteZero**: writes a whole line of zeros without sending data (AXI-L §A11.1). CHI has WriteNoSnpZero / WriteUniqueZero.
- **WriteDeferrable**: a 64-byte atomic store that may be answered **DEFER** ("try later, nothing written"). It maps to PCIe DMWr. CHI has WriteNoSnpDef (AXI-L §A11.2; CHI-H §B4.5.1.3.1).
- **PBHA** (4 bits from the page tables) and **SUBSYSID** (0–8 bits) carry system-defined attributes (AXI-L §A10.2–A10.3).

## Where the sources agree

- Device memory must **never be merged, split, prefetched or speculated**, and Device reads always come from the endpoint (AXI-L §A4.3.1; AHB-C §3.9.4).
- Allocate bits are **hints**, so a cache may ignore them (AXI-L §A4.3.1; AHB-C §3.9.6).
- If a Manager cannot produce accurate attributes, use a safe default. AHB recommends `HPROT = 0b0011` (Non-cacheable, Non-bufferable, privileged, data) (AHB-C §3.8). The AXI defaults are listed in AXI-Hc §A9.3.

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Name of AxCACHE[1] / HPROT[3] | AXI3 (AXI-Hc §A4.2) and AMBA2/AHB-A: **Cacheable** | AXI4+ (AXI-Hc §A4.3) and AHB5: **Modifiable** | Arm says the rename was "to better describe the required functionality. The actual functionality is unchanged" (AXI-Hc §A4.3; AHB-C §3.8) |
| …but did meaning change? | Arm: "functionality is unchanged" | AXI-Hc §A4.3 in the same section: AXI4 **also** lists "Ordering requirements are defined for Non-modifiable transactions" and "The meanings of Read-Allocate and Write-Allocate are updated" | The bit means the same thing, but the surrounding rules got stricter. AXI-Hc §A4.8 gives an example: AXI4 requires Device transactions with the same ID to the same Subordinate to stay ordered, which "is not an explicit requirement of AXI3", so an AXI4 component relying on it "cannot be connected to an AXI3 interconnect that does not exhibit this behavior" |
| RA/WA bit positions | AXI3: [2]=Read-Allocate, [3]=Write-Allocate for **both** AR and AW | AXI4+: [2]/[3] = Allocate / Other Allocate, which **swap** between AR and AW | The encodings are equivalent (on writes, bit 3 is the "this direction" allocate). The new names express "allocate for me" vs "for the other direction" |
| Who should use HPROT | AMBA2 §3.7.3: "Not all bus masters will be capable of generating accurate protection information, therefore it is recommended that slaves do not use the HPROT signals unless strictly necessary" | AHB-C §3.8 keeps the same advice ("Many Managers are not capable of generating accurate protection information"), and adds that such a Manager should drive HPROT = 0b0011. Only when the `Extended_Memory_Types` property is supported does AHB-C §3.9 add detailed required behaviours tied to HPROT[6:2] | Not a real conflict. The general advice is unchanged since 1999. The detailed rules apply only to interfaces that opt in to extended memory types |
| Names of Device memory types | AXI-L Table A4.4: Device **Non-bufferable** / **Bufferable**. AHB-C §3.9.3: **Device-nE / Device-E** | CHI-H §B2.8.3: **Device nRnE / nRE / RE**. G-CHI §4 uses the Arm "GRE / nGRE" names | *Editor's note (not from the sources):* Each spec picked the subset of the Arm Device attributes (G, R, E) that its ordering rules need. AXI and AHB only care about E (early response). CHI also models R (reordering). Map by attribute, not by name |
| Write-Through memory | AXI-L and AHB-C: Write-Through types exist | CHI-H §B2.8.3: no Write-Through type | CHI-H does not mention Write-Through anywhere, so it gives no rule. An AXI→CHI bridge must choose its own mapping for WT traffic and document it |
| Prefetch hint response | AXI-L §A8.6: Prefetch has a **B response** (always OKAY) and needs a unique ID | CHI-H §B4.2.6.2: PrefetchTgt has **no response**, and the Requester frees it as soon as it is sent | *Editor's note (not from the sources):* AXI channels always complete with a handshake. CHI can drop a hint message cheaply |
| Deferrable-write responses | AXI-L §A11.2.3: a 3-bit **BRESP**, DEFER or UNSUPPORTED | CHI-H Table B4.29: **RespErr = OK** with `Resp` = 001 (Unsupported) or 010 (Defer) | The same PCIe DMWr semantics, but AXI adds response codes while CHI reuses its existing fields. A bridge must translate |
| Default AxCACHE handling on AXI4-Lite | AXI-Hc §B1.1: AXI4-Lite accesses are Non-modifiable **Non-bufferable** (0b0000) | AXI-L §B2.1.5: AXI5-Lite accesses are **Device Non-bufferable** | The same meaning in AXI5 naming (AxCACHE 0b0000 = Device Non-bufferable). Not a conflict, just the newer vocabulary |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- A simple AXI peripheral can ignore AxCACHE completely: it just services each access as it arrives.
- An **interconnect or bridge** must honour Non-modifiable. Never upsize, downsize, split or merge AxCACHE[1]=0 traffic, except splitting bursts longer than 16 (AXI-L §A4.2.2). A downsizer that must break this rule may flag it through an implementation-defined mechanism.
- When bridging AHB (HPROT[3:0]) to AHB5 extended types, use the mapping table in AHB-C §3.9.7.

## Related articles

- [Protection and security attributes](protection-and-security.md)
- [Transaction IDs and ordering](transaction-ids-and-ordering.md)
- [Cache coherency fundamentals](cache-coherency-fundamentals.md)
- [Bursts, sizes and alignment](bursts-sizes-and-alignment.md)

## Sources

AMBA2, AHB-A, AHB-C, AXI-Hc, AXI-L (read in full), CHI-H (read in full), G-CHI. See [Source key](sources.md).
