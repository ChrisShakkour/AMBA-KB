# Debug trace: the Advanced Trace Bus (ATB)

> ATB carries trace data, a record of what processors and buses are doing, from trace sources to trace sinks in an Arm CoreSight system. It adds flush, trigger and synchronisation features on top of a simple valid/ready stream.

## In plain words

To debug a chip you often want a recording of what the CPU executed, a "flight recorder". **Trace macrocells** (ETM for instructions, HTM for AHB activity) produce that record as bytes. **ATB** moves those bytes through **funnels** (many sources → one bus) and **replicators** (one → two) to **sinks**: an on-chip buffer (ETB) or a trace port to an external analyser (TPIU) (ATB-C §1.2).

Because trace is buffered, the last few bytes can sit in a FIFO for a long time. ATB therefore has a **flush** mechanism ("push out everything you have"), plus **triggers** and **sync requests**.

## Signals (ATB-C ch. 2)

| Group | Signals | Notes |
|---|---|---|
| Global | `ATCLK`, `ATCLKEN` (optional from Issue B), `ATRESETn` | |
| Data | `ATVALID`, `ATREADY`, `ATDATA[n:0]`, `ATBYTES[m:0]`, `ATID[6:0]` | ATBYTES = number of valid bytes − 1, aligned to the LSB |
| Flush | `AFVALID` (sink→source request), `AFREADY` (source→sink done) | |
| Sync | `SYNCREQ` | Request synchronisation packets in the stream |
| Wake-up | `ATWAKEUP` | ATB-C (AMBA 5) |

## Key rules

- **Handshake**: data moves when ATVALID and ATREADY are both HIGH. If ATREADY is LOW, ATVALID, ATDATA, ATID and ATBYTES hold (ATB-C §3.2).
- **ATDATA width** is a power of two ≥ 8 bits. ATBYTES is log2(number of ATDATA bytes) bits wide and is not needed for 8-bit ATDATA. For example a 32-bit ATDATA has a 2-bit ATBYTES[1:0]. Valid bytes are always the low bytes, and zero bytes cannot be sent (ATB-C §3.2.1).
- **Absent or powered-down Receiver**: it must drive ATREADY **HIGH** and AFVALID LOW, so replicators never block. An absent Transmitter drives AFREADY HIGH and ATVALID LOW (ATB-C §3.2.2–3.2.3).
- **IDs** (ATB-C §4.1):
  - Usable trace IDs: **0x01–0x6F**.
  - **0x7D** = trace trigger (from ATBv1.1). ATDATA then holds the source IDs that triggered.
  - 0x00, 0x70–0x7C, 0x7E and 0x7F are reserved for CoreSight.
  - Reusable components must use **programmable** IDs.
- **Ordering**: trace bytes keep their order **even between different ATIDs**. The spec points out this "differs from … AXI" (ATB-C §4.1).
- **Flush** (ATB-C §4.2):
  - A sink raises AFVALID. The source must output everything buffered *at that moment*, then raise AFREADY one cycle after the last flushed byte.
  - Funnels give priority to sources that haven't acknowledged yet.
  - A flush cannot be cancelled. Trace generated after the request may come out after AFREADY.
  - Uses include before power-down, at capture stop or trigger, or periodically.

## Versions

| Version | Spec issue | AMBA generation | Adds |
|---|---|---|---|
| ATBv1.0 | IHI0032 Issue A (2006) | AMBA 3 | Base protocol |
| ATBv1.1 | Issue B (2012) | AMBA 4 | `SYNCREQ` synchronization request, trace trigger (ATID 0x7D), changed reserved ATID values, `ATCLKEN` optional, and removal of the recommendation that ATDATA be at least 32 bits (ATB-C Table B-1) |
| ATB-C | Issue C (2021) | AMBA 5 | Only two changes (ATB-C Table B-2): terminology update and `ATWAKEUP` wake-up signalling (ch. 6, `Wakeup_Signal` property) |

Source: ATB-C §1.1, Appendix B, and the change history (Issue A 19 June 2006, B 28 March 2012, C 1 December 2021).

## Where the sources agree

- ATB is "data-agnostic" and part of CoreSight (ATB-C §1.2; G-AXI §2; G-SYS §4.4.2).
- Flow control is the same VALID/READY two-way handshake as AXI (ATB-C §3.1).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Ordering model | ATB-C §4.1: total byte order, even across IDs | AXI-L §A5.3: order only within the same ID | An intentional design difference that ATB states itself ("This differs from the required ordering by ID signals in AXI interfaces"). ATB-C §4.1 explains that "although a CoreSight trace funnel can order trace from different sources in any order, when funneled onto a single bus the order cannot be changed" |
| Version naming | ATB-C §1.1 calls the newest version **ATB-C** | Earlier material calls versions **ATBv1.0/v1.1** | Not a conflict. ATB-C §1.1 lists the three versions itself: ATBv1.0 = Issue A (AMBA 3), ATBv1.1 = Issue B (AMBA 4), ATB-C = Issue C (AMBA 5) |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- A trace funnel must forward a flush **upstream to all sources** and acknowledge downstream only after **all** of them have acknowledged (ATB-C §1.2).
- Gate trace-source clocks only after a completed flush (AFVALID→AFREADY). ATB-C §4.2: "Any trace remaining within buffers or FIFOs in trace sources must be output before powering down or stopping the clock. Therefore, the AFVALID signal signals a flush."
- `ATWAKEUP` must be glitch-free and come directly from a register. A Receiver may wait for it before asserting ATREADY, so a present-but-never-asserted `ATWAKEUP` can deadlock the interface (ATB-C §6.2).

## Related articles

- [Streaming interfaces](streaming-interfaces.md)
- [Transaction IDs and ordering](transaction-ids-and-ordering.md)
- [Low power and wake-up](low-power-and-wakeup.md)

## Sources

ATB-B, ATB-C, AXI-L, G-AXI, G-SYS. See [Source key](sources.md).
