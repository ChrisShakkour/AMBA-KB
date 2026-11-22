# Responses and error signalling

> How the answering side reports "done", "failed" or "try again", and what each protocol lets you assume about the data when something goes wrong.

## In plain words

Every transaction ends with a **response**. "OKAY" means it worked. An error response means it did not, but **an error does not always mean nothing happened**. A write that gets an error may still have changed the register, and a read that gets an error may still put data on the bus. Each protocol has its own error codes and its own timing for giving them.

## Response vocabularies

| Protocol | Signal(s) | Codes |
|---|---|---|
| ASB (AMBA2 §4.5) | `BWAIT`, `BERROR`, `BLAST` | WAIT, DONE, ERROR, LAST (done, but the decoder must re-decode), RETRACT (two-stage retry) |
| AMBA 2 AHB (AMBA2 §3.9) | `HRESP[1:0]` | OKAY, ERROR, **RETRY**, **SPLIT** |
| AHB-Lite / AHB5 (AHB-C §5.1) | `HRESP` (1 bit) + `HREADYOUT`; `HEXOKAY` for exclusives | OKAY, ERROR |
| APB3+ (APB-E §3.4) | `PSLVERR` (optional) | error / no error |
| AXI write (AXI-L §A3.3.1) | `BRESP` (0, 2 or 3 bits) | OKAY, EXOKAY, SLVERR, DECERR. AXI5 3-bit codes add DEFER, TRANSFAULT, UNSUPPORTED |
| AXI read (AXI-L §A3.3.2) | `RRESP` (0, 2 or 3 bits), per beat | OKAY, EXOKAY, SLVERR, DECERR. AXI5 3-bit adds PREFETCHED, TRANSFAULT, OKAYDIRTY |
| CHI | `RespErr` field, Poison, DataCheck | OK (00), EXOK (01), Data error DERR (10), Non-data error NDERR (11) (CHI-H §B9.1.2; G-CHI §10, §13). For WriteNoSnpDef, OK is combined with `Resp` to signal Unsupported or Defer |
| GFB (GFB-Ab §3.3) | `FRESP` + `FREADY` | error (two-cycle) |

### SLVERR vs DECERR (AXI)
- **SLVERR**: the request reached a Subordinate but failed, for example a read-only register, a powered-down function, a FIFO overrun or an unsupported size. For reads it is a "contained error" (AXI-L Tables A3.28/A3.31).
- **DECERR**: the request never reached a valid target, typically an unmapped address. It is usually signalled on every read beat, and the `Consistent_DECERR` property guarantees that (AXI-L §A3.3.2).

## Timing: why AHB errors take two cycles

Because AHB is pipelined, the *next* address is already on the bus when a Subordinate decides to error. The ERROR response therefore lasts two cycles: first `HRESP=ERROR, HREADYOUT=LOW`, then `HRESP=ERROR, HREADYOUT=HIGH`. This gives the Manager time to turn the next transfer into IDLE (AHB-C §5.1.3; AMBA2 §3.9.3). GFB copies this idea: "An error response always takes two cycles" (GFB-Ab §3.3.4).

APB needs no such trick. `PSLVERR` is only looked at in the last ACCESS cycle, when `PSEL`, `PENABLE` and `PREADY` are all HIGH (APB-E §3.4.1).

## SPLIT and RETRY (AMBA 2 AHB only)

- Both let a slow slave release the bus. With **RETRY**, the arbiter keeps normal priority. With **SPLIT**, the arbiter masks the split master until the slave signals `HSPLIT[x]`, so lower-priority masters can use the bus meanwhile (AMBA2 §3.9.5, §3.12).
- A master must treat both the same way: keep re-requesting until the transfer completes or gets an ERROR.
- These responses do **not exist** in AHB-Lite or AHB5 (`HRESP` is 1 bit).

## What happens to state and data on error

| Protocol | Write with error | Read with error |
|---|---|---|
| APB | "Does not mean that the register within the peripheral has not been updated" (APB-E §3.4.1) | Data may be invalid. "No requirement for the peripheral to drive the data bus to all 0s". The Requester might still use it |
| AHB5 | — | "A Manager … might still use the data … It is **recommended that HRDATA is driven to zero**" (AHB-C §5.1.3) |
| AXI | SLVERR/DECERR: "the location might not be fully updated" | "The Manager might still sample the RDATA value, so the Subordinate should not rely on the response to hide sensitive data" (AXI-L §A3.3.2) |
| GFB | Programming failed. Content is UNDEFINED (GFB-Ab §3.3.4) | Read data invalid |

AXI also requires **all beats** to be returned even if the first one errors (AXI-L §A3.3.2): no early termination. CHI has the same rule: every transaction, even one with an error, must complete in a protocol-compliant way with the right number of data packets, though the data need not be valid (CHI-H §B9.1.3).

### AXI5 extended responses (AXI-L §A3.3, §A8.6, §A11.2, §A13.6)
With 3-bit `BRESP`/`RRESP`:
- **DEFER**: a WriteDeferrable was not performed and should be retried later, typically by software. **UNSUPPORTED**: the Subordinate does not support WriteDeferrable. EXOKAY is not allowed for WriteDeferrable.
- **TRANSFAULT**: an untranslated transaction hit a translation fault, used in the PRI flow and signalled on all beats.
- **PREFETCHED**: a read hit data brought in by an earlier Prefetch.
- **OKAYDIRTY**: a read of a Shareable line returns it Dirty, used when caching Shareable lines below the coherent interconnect (AXI-L §A8.5).

### CHI error rules in brief (CHI-H §B9.1)
- No mixing of OK with EXOK, or of EXOK with NDERR, in one transaction. NDERR is on none or all of the data packets.
- In a response with NDERR, the cache-state field may hold any value, so ignore it.
- A snoop response with data may carry DERR but **never NDERR**.
- For a DVMOp, the MN may merge all the snoop errors into one NDERR on the final Comp.
- An unsupported **PrefetchTgt** is silently discarded. An unsupported **stash target** is ignored and is not an error.

## Error propagation across bridges

- AXI→APB: PSLVERR → RRESP/BRESP = SLVERR. AHB→APB: PSLVERR → HRESP = ERROR (APB-E §3.4.3).
- AXI↔CHI: setting `Consistent_DECERR=True` helps, "where DECERR translates to a Non-data Error" (AXI-L §A3.3.2).

## Data errors (poison) vs transaction errors

Poison and parity are a **separate** mechanism from responses: they mark *data* as corrupt. See [Interface protection, parity and RAS](interface-protection-parity-and-ras.md).

## Where the sources agree

- **An error response is not a security barrier.** APB, AHB5 and AXI all say a Manager might still read the data lines (APB-E §3.4.1; AHB-C §5.1.3; AXI-L §A3.3.2).
- **A write error does not prove the write didn't happen** (APB-E §3.4.1; AXI-L SLVERR/DECERR definitions).
- Supporting the error signal is **optional for simple Completers**. APB says to tie PSLVERR LOW if unused (APB-E §3.4.1). AXI says if BRESP or RRESP is absent, assume OKAY (AXI-L §A3.3).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Response codes on AHB | AMBA2: 2-bit HRESP with RETRY and SPLIT | AHB-A/AHB-C: 1-bit HRESP (OKAY/ERROR) | AMBA2 §3.9.2 gives RETRY/SPLIT's purpose: to "free up the bus for use by other masters", and notes that SPLIT "requires extra complexity in both the slave and the arbiter" (§3.9.5). AHB-Lite is single-master per layer (AHB-A §1.1, §1.3). *Editor's note (not from the sources): with one master per layer there is no shared bus to free, which likely explains the removal. AHB-A does not state a reason* |
| Must read data be zero on error? | APB-E §3.4.1: **no** requirement | AHB-C §5.1.3: **recommended** zero | *Editor's note (not from the sources):* AHB Issue C added a security-minded recommendation. APB kept "no requirement". In practice, drive zero anyway |
| Must a Manager cancel the rest of a burst after an AHB error? | AMBA2 §3.9.3–3.9.4: optional. For ERROR "completion of the following transfer is optional", and the Manager "may choose to cancel the remaining transfers in the burst" | AHB-C §3.6.2: optional too, **but** if it cancels it *must* drive IDLE during the two-cycle error | Same rule. Issue C makes the IDLE requirement explicit |
| How to say "not done, try later" | AXI-L §A11.2.3: WriteDeferrable gets a 3-bit `BRESP` **DEFER** (or UNSUPPORTED) | CHI-H Table B4.29: WriteNoSnpDef gets **RespErr = OK** with `Resp` = 010 (Defer) or 001 (Unsupported) | The same PCIe Deferrable Memory Write semantics, encoded differently. CHI adds no new RespErr codes. A bridge must translate |
| How many cycles must an AHB slave be able to wait? | AMBA2 §3.9.1: recommended ≤ 16 wait states | AHB-C §5.1.2: only "a predetermined maximum" | See [Interconnect, topology and bridges](interconnect-topology-and-bridges.md) |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- In an AHB Subordinate, implement ERROR as a small 2-state FSM (ERR1 with HREADYOUT=0, ERR2 with HREADYOUT=1), both with HRESP=1.
- In AXI, keep returning `RVALID` beats until RLAST even after an error.
- Decide and document whether your peripheral **updates** the register on a write error. The protocols allow either (APB-E §3.4.1).

## Related articles

- [Interconnect, topology and bridges](interconnect-topology-and-bridges.md)
- [Exclusive access, locked transfers and atomics](exclusive-locked-and-atomic-access.md) (EXOKAY/HEXOKAY)
- [Interface protection, parity and RAS](interface-protection-parity-and-ras.md)

## Sources

AMBA2, APB-B, APB-E, AHB-A, AHB-C, AXI-L (read in full), CHI-H (read in full), GFB-Ab, G-CHI. See [Source key](sources.md).
