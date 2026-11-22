# Interface properties, optional signals and user signals

> Modern AMBA specs describe an interface as a base protocol plus named **properties** that switch optional features (and their signals) on or off. They also allow **user signals** for custom sideband information, which Arm generally recommends you avoid.

## In plain words

Instead of publishing a new protocol for every small feature, Arm adds **properties**: named configuration settings such as `Wakeup_Signal = True`, `Check_Type = Odd_Parity_Byte_All` or `DATA_WIDTH = 64`. A property decides whether a signal exists and how wide it is. Each spec then gives **compatibility tables** saying what happens when a Manager with a feature meets a Subordinate without it: "compatible, tie input X LOW", "compatible but feature unused" or "not compatible".

**User signals** (`xUSER`) are spare, undefined wires that a system can use for its own purposes.

## How properties work

- A width property equal to 0 means the signal is **not present** (APB-E §2.1; AHB-C ch. 2; AXIS-B §2.1).
- An undeclared Boolean property defaults to **False** (for example "If the Wakeup_Signal property is not declared, it is considered False": APB-E §3.7).
- Spec appendices list each signal as **Y** (mandatory), **N** (must not be present), **O** (optional), **C** (conditional: present when the property is True) or **OC** (optional-conditional) (APB-E Appendix B; AHB-C Appendix A; AXI-L ch. B2).
- AXI5 goes furthest. Even `AxSIZE`, `AxLEN`, `AxBURST`, `WSTRB`, `WLAST` and the IDs can be omitted, with the Subordinate tying the input to a defined value (`SIZE_Present`, `LEN_Present`, `BURST_Present`, `WSTRB_Present`…) (AXI-L §A3.1–A3.2).

### Examples of properties

| Property | Protocols | Effect |
|---|---|---|
| `Check_Type` | APB5, AHB5, AXI5, AXI5-Stream | Adds parity check signals |
| `Wakeup_Signal(s)` | APB5, AXI5, AXI5-Stream | Adds xWAKEUP |
| `RME_Support` | APB5, AXI5, CHI | Adds PNSE / AxNSE / PAS fields |
| `Write_Strobes` | AHB5 | Adds HWSTRB |
| `Extended_Memory_Types`, `Secure_Transfers`, `Exclusive_Transfers`, `Endian`, `Stable_Between_Clock`, `Multi_Copy_Atomicity` | AHB5 | See the AHB-C chapters |
| `AXI_Transport`, `Num_RP_*`, `Shared_Credits_*` | AXI5 | Valid-Ready vs credited transport, resource planes |
| `Regular_Transactions_Only`, `Max_Transaction_Bytes`, `Fixed_Burst_Disable`, `Wrap_CLS_Modifiable` | AXI5 | Simplify Subordinate decode |
| `Read_Interleaving_Disabled`, `Ordered_Write_Observation`, `Device_Normal_Independence` | AXI5 | Ordering behaviour |
| `CXS_MAX_CREDIT`, `CXSMAXPKTPERFLIT`, `CXS_LAST`… | CXS | Credits and packing |
| `Cache_Line_Size`, `Untranslated_Transactions` (v1–v4), `MTE_Support`, `MPAM_Support`, `DVM_Message_Support`, `Credit_Control` | AXI5 | Cache granule, SMMU signals, tagging, partitioning, DVM, credited gating (AXI-L Appendix B2) |
| `NodeID_Width` (7–16), `Req_Addr_Width` (44–52), `Data_Width` (128/256/512), `Req_RSVDC_Width`, `Dat_RSVDC_Width` | CHI | Flit field widths (CHI-H §B16.1) |
| `Direct_Memory_Transfer`, `Direct_Cache_Transfer`, `Cache_Stash_Transactions`, `Atomic_Transactions`, `Enhanced_Features`, `Deferrable_Write`, `CleanSharedPersistSep_Request`, `CleanInvalidStorage_Request` | CHI | Which optional transaction flows a node supports |
| `Cache_State_UDP`, `Cache_State_SD`, `Nonshareable_Cache_Maint`, `Outer_Cacheable_Support` | CHI | Cache-state subset and handling of Non-shareable Cacheable memory |
| `RME_Support`, `MEC_Support`, `MECID_Width`, `GDI_Support`, `GDI_Non_PE_RNF`, `DevAssign_Support`, `MECID_Mismatch_Resolution_Realm` | CHI | Security extensions. They depend on each other: MEC, GDI and Device Assignment all need `RME_Support = True`, and RME needs `Nonshareable_Cache_Maint = True` and `DVM_Support = DVM_v9.2` |
| `Num_RP_REQ/SNP`, `Shared_Credits_REQ/SNP`, `Retry_Support`, `MultiReq_Support`, `MultiReq_*_Retry_Support`, `Limited_Data_Elision` | CHI (Issue G/H) | Flow control and packet efficiency. Several must be **equal at both ends** of a link |

### Broadcast pins (tie-offs that switch features off)

Both AXI5 and CHI have optional `BROADCAST*` inputs that a system ties at integration to stop a component issuing things the rest of the system cannot handle. They must be stable when reset is released (CHI-H §B16.2).

| Pin | When LOW |
|---|---|
| `BROADCASTINNER` / `BROADCASTOUTER` (CHI), `BROADCASTSHAREABLE` (AXI) | Snoopable/Shareable requests are converted to non-snoopable ones. Some are dropped (Evict, WriteEvictFull, CleanUnique…) |
| `BROADCASTCACHEMAINT` | CleanShared, CleanInvalid and MakeInvalid are not issued. Write+CMO becomes a plain write |
| `BROADCASTPERSIST`, `BROADCASTCMOPOPA`, `BROADCASTSTORAGE` | Persist CMOs become CleanShared; PoPA and PoPS CMOs become CleanInvalid |
| `BROADCASTATOMIC` | No Atomic transactions are issued |
| `BROADCASTMTE` (CHI) | MTE fields stay Invalid, except tags already held in cache |
| `BROADCASTICINVAL` (CHI) | I-cache invalidations need not be broadcast as DVMs |
| `BROADCASTTLBIINNER/OUTER` (CHI) | Controls which TLBI domains are broadcast (01 allowed, 10 reserved) |
| `BROADCASTLIMELISION`, `BROADCASTMULTIREQ` (CHI) | Disable data elision. Limit multi-requests (3 bits: up to 2…64 lines, 128 B…4 KB boundary) |

### Reading a compatibility table

From APB-E Table 3-1 (PSTRB):

| | Completer without PSTRB | Completer with PSTRB |
|---|---|---|
| Requester without PSTRB | Compatible. Sparse writes not supported | Compatible. **Tie the PSTRB inputs to PWRITE** (all lanes valid on writes) |
| Requester with PSTRB | Compatible. Sparse writes not supported | Compatible |

The same pattern appears for PPROT, RME, MEC, Busy, QoS-Accept, Shared credits and so on. The typical outcomes are **compatible with a tie-off**, **functional but feature unused**, **not compatible** and occasionally **compatible but might break** (for example AXI `Regular_Transactions_Only`: if the Manager isn't regular but the Subordinate requires it, "data corruption or deadlock might occur", AXI-L Table A3.18).

## User signals

| Protocol | Signals | Width recommendations |
|---|---|---|
| APB5 | `PAUSER`, `PWUSER`, `PRUSER`, `PBUSER` | Request ≤ 128, data ≤ DATA_WIDTH/2, response ≤ 16 (APB-E §3.8) |
| AHB5 | `HAUSER`, `HWUSER`, `HRUSER`, `HBUSER` | Same as APB5 (AHB-C §11.1) |
| AXI | `AxUSER`, `WUSER`, `RUSER`, `BUSER` (AXI4+), plus `User Loopback` (AXI5) | Configurable (AXI-L §A12.4–A12.5) |
| AXI-Stream | `TUSER` | A multiple of the byte count. Bits packed per byte (AXIS-B §2.9) |
| CXS | `CXSUSER` | 0–128 bits per flit (CXS-D §2.6) |

Rules that apply everywhere:
- **Data-channel user bits are defined per byte**, `xUSER[y*m + m-1 : y*m]` for byte *y*, so they survive width conversion (AHB-C §11.1; AXIS-B §2.9).
- When an interconnect **splits** a transfer, request-user bits are copied into each piece. When it **merges**, the first transfer's request-user bits win (AHB-C §11.2).
- Include user signals on **interconnects and bridges**. Managers and Subordinates are not required to have them (APB-E §3.8.3; AHB-C §11.1).

## Where the sources agree

- **"Generally, it is recommended that User signals are not used."** The protocols don't define their meaning, so two components can use the same bits incompatibly (APB-E §3.8.2; AHB-C ch. 11 note).
- Properties are declared **per interface**. Connected interfaces must have compatible values, and if a property is not declared, its default applies.

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Fixed vs configurable address width (AHB) | AHB Issues A and B: HADDR "was fixed at 32" | AHB-C Table 2-2: `ADDR_WIDTH` property, recommended 10–64 | *Editor's note (not from the sources):* Issue C (2021) added signal-width properties so AHB5 can address more than 4 GB |
| Default of optional AXI properties | Older AXI issues list default signal values per signal (AXI-Hc §A9.3) | AXI-L declares a "Default" column per property in each table | The same idea with a different presentation. When migrating IP, re-check each default against the issue you target |
| Retry interoperability | Most property tables: a mismatch means "feature unused" | CHI-H Table B16.41: a Completer with `Retry_Support = True` and a Requester with False "could deadlock" | Retry is not a feature you can ignore. If the Completer sends RetryAck to a Requester that cannot resend, that request never completes. Some CHI property mismatches are **hard incompatibilities** |
| Property vs signal naming | APB-E and AXIS-B use `Wakeup_Signal` (singular) | AXI-L uses `Wakeup_Signals` (plural, because there are AWAKEUP and ACWAKEUP) | Not a functional difference, but tool scripts that search for property names must handle both |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Put every property your IP supports into its **datasheet and IP-XACT**. Integrators then use the compatibility tables to decide tie-offs.
- If you must use user signals, document the meaning per bit *and* how they behave under split and merge.

## Related articles

- [Interface protection, parity and RAS](interface-protection-parity-and-ras.md)
- [Low power and wake-up](low-power-and-wakeup.md)
- [Bursts, sizes and alignment](bursts-sizes-and-alignment.md) (Regular transactions)
- [Protocol evolution and version differences](protocol-evolution-and-versions.md)

## Sources

APB-E, AHB-C, AXI-Hc, AXI-L (read in full), AXIS-B, CHI-H (read in full), CXS-D. See [Source key](sources.md).
