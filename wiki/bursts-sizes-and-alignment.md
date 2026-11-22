# Bursts, sizes, alignment and write strobes

> How one request can move many beats of data (a *burst*), how big each beat is (*size*), how addresses step and wrap, and how *strobes* mark which bytes are real.

## In plain words

A **burst** is a group of same-width transfers to an incrementing (or wrapping) region of addresses (AMBA2 §1.4). How much address information travels with it depends on the protocol. In AHB the Manager still drives every beat's address, and a SEQ beat's address is "the address of the previous transfer plus the size" (AMBA2 §3.5; AHB-C §3.2). In AXI the Manager sends only the first address, and the Subordinate calculates the rest (AXI-L §A3.1).
- **Size** = bytes per beat. **Length** = number of beats.
- **INCR** bursts step upwards. **WRAP** bursts wrap around inside an aligned block, which is ideal for cache lines because the critical word comes first. **FIXED** bursts hit the same address repeatedly, as when reading a FIFO.
- **Write strobes** say which byte lanes of the data bus carry valid bytes, so you can write 1 byte on a 64-bit bus.

## Burst encodings side by side

| | AHB (`HBURST[2:0]`) | AXI (`AxBURST`, `AxLEN`) | APB |
|---|---|---|---|
| Single | SINGLE (000) | INCR with LEN=0 | Always single |
| Incrementing | INCR (undefined length), INCR4/8/16 | INCR, length 1–16 (AXI3) or **1–256** (AXI4+) | — |
| Wrapping | WRAP4/8/16 | WRAP, length **2, 4, 8 or 16** | — |
| Fixed address | — | FIXED, length ≤ 16 | — |
| Boundary rule | Must not cross **1 KB** | Must not cross **4 KB** | — |
| Early termination | Allowed (ERROR, multi-layer) | **Not allowed**. Use strobes = 0 to "skip" writes, discard unwanted reads | — |

Sources: AHB-C §3.6; AMBA2 §3.6; AXI-L §A3.1.2–A3.1.4; AXI-Hc §A3.4.

### The wrap calculation (AXI-L §A3.1.6, AHB-C §3.6)

```
Container_Size = Size × Length
Wrap_Boundary  = INT(Start_Addr / Container_Size) × Container_Size
Next address   = Addr + Size; if it reaches Wrap_Boundary + Container_Size → jump to Wrap_Boundary
```
Example (AHB-C §3.6): WRAP4 of words starting at 0x34 → 0x34, 0x38, 0x3C, **0x30**.

The exact AXI equations are in AXI-L §A3.1.6. After the wrap, Address_N = Aligned_Addr + (N−1)×Size − Size×Length. Issue L corrected this from `Start_Addr + …` in earlier issues (AXI-L Table B4.3). Because a WRAP start address must already be Size-aligned, both versions give the same addresses. The fix only matters if you copy the equation into a model of other burst types.

**New in AXI Issue L: `Wrap_CLS_Modifiable`.** With this property True, **which is the default**, a WRAP transaction must be **exactly one cache line** and **Modifiable** (AxCACHE[1]=1). With it False, the older rules apply: any wrap length 2/4/8/16 and Device memory allowed. The aim is simpler decoders and protocol/width bridges (AXI-L §A3.1.4, Tables A3.11–A3.12).

## Size

| AHB `HSIZE` / AXI `AxSIZE` | 000 | 001 | 010 | 011 | 100 | 101 | 110 | 111 |
|---|---|---|---|---|---|---|---|---|
| Bytes per beat | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 |

- Size must be ≤ the data-bus width (AHB-C §3.4; AXI-L §A3.1.1).
- Data-bus widths: APB 8/16/32 (APB-E §2.1.2); AHB 8–1024, with 32–256 recommended (AHB-C §6.3); AXI 8–1024 (AXI-L §A3.2); AXI4-Lite **32 or 64 only** (AXI-Hc §B1.1); CHI **128, 256 or 512 only** (CHI-H §B16.1.13).

## CHI: no bursts, but packets (CHI-H §B2.9)

CHI has no burst type or length. A request names a **Size** of 1 to 64 bytes (`Size` 0b000–0b110), and the data moves as one or more DAT packets:
- A 64-byte line takes 4 packets on a 128-bit bus, 2 on 256-bit, 1 on 512-bit. **DataID** says which 128-bit chunk(s) a packet carries.
- **CCID** names the critical chunk. With `CCF_Wrap_Order` the completer returns data critical-chunk-first in wrap order. Otherwise packets may arrive in any order, and the interconnect may reorder them.
- Snoop data is always the full 64 bytes.
- **Normal** memory: the bytes are those of the Size-aligned block containing the address. **Device** memory: from the start address up to the next Size boundary, so unaligned Device accesses are allowed and BE marks only those bytes.
- Write data and snoop data bytes whose BE is 0 must be driven as **zero**.
- **Limited Data Elision** (CHI-G) lets one packet stand for up to 3 more all-zero or replicated packets (NumDat, Replicate). It may be used only when the BEs are all-0 or all-1.
- **Multi-request** (CHI-H) covers 2–64 whole cache lines (128 B–4 KB) with one request, never crossing 4 KB. Each line's data still travels as its own 64-byte message.

AXI equivalent: transactions that must be a whole cache line, such as CMOs, WriteZero and Prefetch, must be **Regular**, use at most 16 beats, and assert all strobes (AXI-L §A8.2).

## Narrow and unaligned transfers

- **Narrow** = Size smaller than the bus. INCR/WRAP use a different byte lane each beat, FIXED uses the same lanes every beat (AXI-L §A3.2.3).
- **AXI supports unaligned starts.** A Manager can show the unaligned address on the low address bits *or* give an aligned address with strobes, but the two must agree (AXI-L §A3.2.5).
- **AHB requires alignment**: "All transfers in a burst must be aligned to the address boundary equal to the size of the transfer" (AHB-C §3.6).
- **APB**: unaligned PADDR is permitted, but the result is **UNPREDICTABLE** (APB-E §2.1.1).

## Write strobes

| Protocol | Signal | Introduced | Rules |
|---|---|---|---|
| APB | `PSTRB` | APB4 (Issue C) | One bit per byte. Must be all LOW on reads. If the Requester has strobes but the Completer doesn't, sparse writes are simply unsupported (APB-E §3.2) |
| AHB | `HWSTRB` | AHB Issue C (2021) | Data-phase signal. Strobes for *inactive* lanes may be anything. A transfer with all strobes deasserted is permitted, and then "no bytes are written in that transfer". May change between beats. Recommended deasserted on reads (AHB-C §3.5) |
| AXI | `WSTRB` | AXI3 | Outside the transaction container all strobes must be LOW. Inside, any pattern is allowed, including all LOW (AXI-L §A3.2.1.1) |
| AXI-Stream | `TSTRB` (+ `TKEEP`) | AXI4-Stream | Marks data byte vs position byte (see [Streaming interfaces](streaming-interfaces.md)) |

## "Lite" and "regular" subsets

- **AXI4-Lite**: burst length 1, full-width accesses, Non-modifiable Non-bufferable, no exclusives, no EXOKAY (AXI-Hc §B1.1).
- **AXI5-Lite**: burst length 1, WriteNoSnoop/ReadNoSnoop only, Device Non-bufferable, no exclusives, **but responses may be reordered for different IDs** (AXI-L §B2.1.5).
- **Regular transactions** (AXI5 property `Regular_Transactions_Only`): length 1/2/4/8/16, full-width size when length > 1, no FIXED, aligned. This lets Subordinates use simpler decode (AXI-L §A3.1.8).

## Where the sources agree

- A burst is a sequence of same-size beats to related addresses, described by a burst type and length (AMBA2 §1.4, §3.6; AXI-L §A3.1). AHB repeats the address on every beat (AMBA2 §3.5), while AXI sends only the start address (AXI-L §A3.1).
- The wrap boundary is **Size × Length**, and wrap lengths are **powers of two up to 16** in both AHB and AXI.
- Strobe bit *n* always covers bits [8n+7 : 8n] of the data bus, independent of endianness (APB-E §3.2; AHB-C §3.5; AXI-L §A3.2.1.1).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Max AXI burst length | AXI-B/AXI-C: AXI3 supports **1–16** beats for all burst types (`AxLEN[3:0]`) | AXI-Hc §A3.4 / AXI-L: AXI4+ INCR supports **1–256** (`AxLEN[7:0]`) | AXI-C §13.1 describes the change ("The AXI4 protocol supports longer bursts through the extension of AWLEN and ARLEN") but gives no reason. Its limits: >16 beats only for INCR, exclusives ≤ 16, and long bursts may be split even if Non-modifiable. A Note says splitting "might also be needed to reduce the impact of longer bursts on the QoS guarantees". *Editor's note (not from the sources): fewer address transfers per byte is the usual motivation* |
| Must a Manager rebuild a broken AHB burst? | AMBA2 §3.6.1: if a master loses the bus mid-burst it **must rebuild** the remaining beats (for example with an INCR) | AHB-C §3.6.2: after an ERROR the Manager need not complete the burst, and "there is no requirement for it to rebuild the burst" | Different situations. AMBA2 covers *losing arbitration*, which doesn't exist in AHB-Lite. AHB-C covers *errors* and multi-layer termination |
| Alignment of IDLE transfers | AHB Issues A and B: IDLE addresses must be aligned (a rule) | AHB-C §3.6: now only **recommended** | Relaxed in Issue C because the rule only caused "spurious warnings in simulation" |
| AHB data width minimum | AMBA2 §3.10: "the **minimum** data bus width is specified as **32 bits**" | AMBA2 §3.14 (same spec) and AHB-C §6.3: 8 and 16 bits are allowed, and 32 is only **recommended** | An internal inconsistency in the AMBA 2 text. The later section and every later issue treat 32 as a recommendation |
| AXI4-Lite vs AXI5-Lite IDs | AXI-Hc §B1.1: AXI4-Lite has **no** ID signals (in-order only) | AXI-L §B2.1.5: AXI5-Lite permits **reordering** of responses for different IDs | AXI5-Lite is defined as a constrained AXI5 interface, so it inherits ID support |
| What WRAP bursts may be | AXI3/AXI4 and AXI-J/K: any WRAP of length 2/4/8/16, any memory type | AXI-L §A3.1.4: `Wrap_CLS_Modifiable` (default **True**) restricts WRAP to one cache line, Modifiable | WRAP is really used only for cache-line fills. Restricting it by default simplifies bridges. A Manager that issues other WRAPs must declare the property False, and the compatibility table then says which Subordinates it can connect to (AXI-L Table A3.12) |
| Wrap address equation | AXI-J (and earlier): after wrapping, Address_N = **Start_Addr** + (N−1)×Size − Size×Length | AXI-L §A3.1.6: **Aligned_Addr** + (N−1)×Size − Size×Length, listed as a correction | A documentation fix. WRAP starts are Size-aligned, so the results are identical in practice |
| Widest data bus | AXI-L §A3.2 and AHB-C §6.3: up to **1024 bits** | CHI-H §B16.1.13: **512 bits** maximum (128/256/512 only) | A design difference; CHI-H gives no reason. *Editor's note (not from the sources): at 512 bits one DAT flit already carries a whole 64-byte cache line* |
| Strobes on AHB | AMBA2, AHB-A, AHB-Bb: **no** HWSTRB, so sub-word writes use HSIZE only | AHB-C §3.5: optional `HWSTRB` (Write_Strobes property) | Added in AHB-C (Sep 2021). Write strobes enable "a Manager to issue a write that updates only a subset of active write data bytes" (a *sparse write*) (AHB-C §3.5). *Editor's note (not from the sources): it also eases AXI↔AHB bridging, since AXI always has WSTRB* |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Check the **4 KB rule** in AXI Managers: `(start_addr[11:0] + total_bytes) <= 4096` for INCR.
- For an AXI Subordinate that cannot handle FIXED bursts, declare `Fixed_Burst_Disable = True` (AXI-L §A3.1.4) instead of silently mishandling them.
- When reading a FIFO-like peripheral over AXI, use an exact length, because "discarding read data … can result in lost data when accessing a read-sensitive device" (AXI-Hc §A3.4).

## Related articles

- [Endianness and byte lanes](endianness-and-byte-lanes.md)
- [Transfer phases and pipelining](transfer-phases-and-pipelining.md)
- [Memory types and cache attributes](memory-types-and-cache-attributes.md) (when a burst may be split or merged)
- [Streaming interfaces](streaming-interfaces.md)

## Sources

AMBA2, APB-E, AHB-C, AXI-B, AXI-C, AXI-Hc, AXI-J, AXI-L (read in full), CHI-H (read in full). See [Source key](sources.md).
