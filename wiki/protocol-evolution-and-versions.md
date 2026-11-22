# Protocol evolution and version differences

> A timeline of how each AMBA protocol changed, what was added or removed in each issue, and a single **register of every disagreement** found across the sources in this wiki.

## In plain words

AMBA's first spec was "stable from September 1995" (INTRO96). Later generations changed or removed earlier features, and the specs often give their own reasons:
- **Tri-state buses.** AMBA 2 AHB lists "non-tristate implementation" among its features, and it needs separate read and write data buses "to allow implementation of an AHB system without the use of tristate drivers" (AMBA2 §1.5, §3.10). The tri-state ASB remained in AMBA 2, but AHB was "recommended for all new designs" (AMBA2 §1.8.1).
- **Shared-bus arbitration.** AHB-Lite is "a bus interface that supports a single bus master". Multi-master systems use a multi-layer interconnect, and "slave arbitration must be performed by the multi-layer interconnect component" (AHB-A §1.1, §1.3). AXI is "a point-to-point specification, not a bus specification" (G-AXI §3).
- **Locked transfers.** These were removed in AXI4 because "the majority of components do not require locked transactions" and because they have "a significant effect on the complexity of the interconnect" and "on the ability to make QoS guarantees" (AXI-C §13.15.1).

As a result, **two documents can both be "the AMBA spec" and still disagree**, simply because they describe different versions. When reading any AMBA document, always ask: *which protocol version, and which spec issue?*

## Generations

| Generation | Year (spec dates) | Protocols introduced | Sources |
|---|---|---|---|
| AMBA (1) | Stable since Sep 1995. Intro doc Oct 1996 | ASB, APB (Rev D, strobe-timed) | INTRO96 |
| AMBA 2 | 1999 | AHB (multi-master, SPLIT/RETRY), APB2 (PCLK, PENABLE), ASB kept | AMBA2 |
| AMBA 3 | 2003–2006 | AXI3 (2003/04), APB3 (2003/04: PREADY, PSLVERR), ATBv1.0 (2006), AHB-Lite (spec 2006) | AXI-B, APB-B, ATB-B, AHB-A |
| AMBA 4 | 2010–2013 | AXI4, AXI4-Lite, AXI4-Stream (2010), APB4 (2010: PPROT, PSTRB), ACE/ACE-Lite (2011), ATBv1.1 (2012), Q/P-Channel LPI (2013) | AXI-C, AXIS-A, APB-C, ATB-B, LPI-C |
| AMBA 5 | 2014 onward | CHI (A 2014 limited, B 2017 public), AHB5 (2015), AXI5/ACE5 variants (Issue F, 2017), DTI (2016+), CXS (2018), GFB (2018), ATP (2019), LTI (2020), APB5 (2021), AXI5-Stream (2021), ATB-C (2021), CHI C2C (2024) | CHI-H, AHB-C, AXI-Fb, DTI-J, CXS-D, GFB-A, ATP-A, LTI-E, APB-E, AXIS-B, ATB-C, C2C-B |

## Per-protocol change summaries

### APB (APB-E Preface & Appendix C)
| Version | Spec issue | Adds |
|---|---|---|
| Rev E / Rev D | 1998 / 1996 | Obsolete ("APB Specification Rev E, released in 1998, is now obsolete") |
| APB2 | AMBA2 (IHI0011A) | Rising-edge PCLK, SETUP/ENABLE |
| APB3 | IHI0024 B | `PREADY` (wait states), `PSLVERR` |
| APB4 | C | `PPROT`, `PSTRB` |
| APB5 | D | `PWAKEUP`, user signals, parity, width properties, Requester/Completer terms |
| APB5 | E | RME: `PNSE` |

### AHB (AHB-C §1.2, Appendix B)
| Version | Issue | Changes |
|---|---|---|
| AHB (AMBA 2) | IHI0011A | Arbiter, HBUSREQ/HGRANT, HRESP[1:0] with SPLIT/RETRY, up to 16 masters |
| AHB-Lite | IHI0033 A | Single Manager, 1-bit HRESP, multi-layer interconnect |
| AHB5 | B / B.b | Extended memory types (HPROT[6:4]), HNONSEC, exclusives (HEXCL, HMASTER, HEXOKAY), multiple HSEL, Endian property, Stable_Between_Clock, atomicity, user signals. HPROT[3] renamed Modifiable |
| AHB5 | C | Width properties (ADDR_WIDTH…), HWSTRB, parity, signal-validity rules, Manager/Subordinate terms |

### AXI (AXI-Hc Appendix G7; AXI-L §B4)
| Version / issue | Key changes |
|---|---|
| AXI3 (B, 2004) | First release ("Version 1.0"): 5 channels, IDs, out-of-order completion, AxLEN[3:0] (max 16), WID write interleaving, locked accesses (AxLOCK[1:0]) |
| AXI4 (C, 2010) | AXI4 and AXI4-Lite chapters added: INCR up to 256, no WID, no locked, AxLOCK 1 bit, AxCACHE[1] renamed Modifiable, QoS, REGION, USER |
| D (2011) | AXI3/AXI4 text integrated, and Part C "AXI Coherency Extensions (ACE)" added |
| E (2013) | Ordered_Write_Observation and Multi_Copy_Atomicity properties, AWUNIQUE, WriteEvict, DVMv8, Manager design recommendations, ACP appendix |
| F (2017) | AXI5, AXI5-Lite, ACE5, ACE5-Lite, ACE5-LiteDVM, ACE5-LiteACP. Atomics, stashing, deallocating reads, poison, data parity (Check_Type), wake-up, untranslated transactions v1, NSAID, QoS Accept, trace, loopback, Coherency Connection, DVM v8.1, persistent CMO. Inner Shareable and barriers deprecated for AMBA 5 interfaces. The Low Power Interface chapter was removed (moved to IHI 0068) |
| G (2019) | Multi_Copy_Atomicity required, CMOs on write channels and Deep persistence, read data chunking, read-interleaving property, Unique ID indicator, MPAM, **interface parity**, AWSNOOP widened to 4 bits, ID-constraint summary |
| H (2020) / H.b / H.c (2021) | Regular transactions, Write with CMO, DVM v8.4, untranslated transactions v2, **MTE**, Prefetch, WriteZero, more interface properties. H.b: Manager/Subordinate terminology. **H.c is the last issue with AXI3, AXI4 and ACE** |
| J (2023) | Restructured: AXI3/AXI4/AXI4-Lite/ACE/ACE5 **removed**. ACE5-Lite variants and AXI5-Lite redefined as AXI5 property constraints. RME, Busy, Unique ID… |
| K | MEC, wider MPAM, Fixed_Burst_Disable, Cache_Line_Size, Device_Normal_Independence |
| L (2025) | **Credited transport**, Arm Compression Technology, new protection signalling (AxPAS), GDI, untranslated transactions v4, CMO to PoPS, `Wrap_CLS_Modifiable` (WRAP limited to one cache line by default). Corrections: wrap address equation, AxMMUVALID default = 1, MECID width 0 or 16 (AXI-L Table B4.3). Bidirectional DVM deprecated (AXI-L §A15.2) |

### CHI: see the issue table in [CHI architecture](chi-architecture.md#issues-of-chi), taken from CHI-H Appendix C5.
### ATB: v1.0 (AMBA 3) → v1.1 (AMBA 4) → ATB-C (AMBA 5). See [Debug trace (ATB)](debug-trace-atb.md).
### AXI-Stream: AXI4-Stream (A) → + AXI5-Stream wake-up and parity (B). See [Streaming interfaces](streaming-interfaces.md).

## Register of disagreements across the sources

Every disagreement flagged elsewhere in the wiki, in one place. Items 48–71 were added after a full read of AXI Issue L and CHI Issue H. **Type** says whether it is a *version change* (the protocol really changed), *wording* (same meaning, different words), an *outdated guide*, or an *internal inconsistency* inside one document.

| # | Topic | What conflicts | Type | Article |
|---|---|---|---|---|
| 1 | AMBA start date | INTRO96: stable from 1995. G-AXI: "late 1990s" | Outdated guide | [Overview](amba-overview.md) |
| 2 | CHI start date | G-AXI: 2014. CHI-H: 2014 limited, 2017 first public | Wording | [CHI](chi-architecture.md) |
| 3 | AHB5 date | G-AXI: 2016. AHB-C: Issue B, 2015 | Outdated guide | [Overview](amba-overview.md) |
| 4 | AHB-Lite generation | Listed under AMBA 3 (2003). Spec dated 2006 | Wording | [Overview](amba-overview.md) |
| 5 | ACE status | G-AXI teaches it as current. AXI-J/L removed it, G-SYS says superseded | Version change | [ACE](ace-coherency-extensions.md) |
| 6 | Initiator/responder names | Manager/Subordinate vs Requester/Completer vs Transmitter/Receiver vs master/slave | Wording | [Terminology](terminology-and-roles.md) |
| 7 | APB clocking | INTRO96: unclocked strobe, 5 clocks. AMBA2+: PCLK, 2 cycles | Version change | [Phases](transfer-phases-and-pipelining.md) |
| 8 | AHB arbitration | AMBA2: arbiter in the protocol. AHB-Lite: none (multi-layer) | Version change | [Topology](interconnect-topology-and-bridges.md) |
| 9 | AHB wait-state limit | AMBA2: ≤16 recommended. AHB-C: "predetermined maximum" only | Version change | [Topology](interconnect-topology-and-bridges.md) |
| 10 | AHB responses | AMBA2: SPLIT/RETRY, 2-bit HRESP. AHB-Lite/5: 1-bit | Version change | [Responses](responses-and-errors.md) |
| 11 | Read data on error | APB: no requirement to zero. AHB-C: recommended zero | Different recommendation | [Responses](responses-and-errors.md) |
| 12 | AHB endianness | AMBA2: not specified, no dynamic endianness. AHB5: BE8/BE32 property | Version change | [Endianness](endianness-and-byte-lanes.md) |
| 13 | "Big-endian" lane table | AMBA2's table is BE32. AHB5/AXI use BE8 | Wording (trap) | [Endianness](endianness-and-byte-lanes.md) |
| 14 | AHB min data width | AMBA2 §3.10 "minimum 32" vs §3.14 "8–1024, 32 recommended" | Internal inconsistency | [Bursts](bursts-sizes-and-alignment.md) |
| 15 | Rebuilding AHB bursts | AMBA2: must rebuild after losing the bus. AHB-C: no need after an error | Different situations | [Bursts](bursts-sizes-and-alignment.md) |
| 16 | IDLE address alignment | AHB A/B: rule. AHB C: recommendation | Version change | [Bursts](bursts-sizes-and-alignment.md) |
| 17 | AXI burst length | AXI3: 16. AXI4+: 256 (INCR) | Version change | [Bursts](bursts-sizes-and-alignment.md) |
| 18 | AXI-Lite IDs | AXI4-Lite: none. AXI5-Lite: reordering by ID allowed | Version change | [Bursts](bursts-sizes-and-alignment.md) |
| 19 | AHB write strobes | None before AHB-C. HWSTRB optional in AHB-C | Version change | [Bursts](bursts-sizes-and-alignment.md) |
| 20 | Write interleaving | AXI3: WID. AXI4: deprecated. AXI5 credited: allowed across RPs | Version change | [Ordering](transaction-ids-and-ordering.md) |
| 21 | CHI Endpoint vs Request Order | Before CHI-D Endpoint implies Request. CHI-D+ it does not | Version change | [Ordering](transaction-ids-and-ordering.md) |
| 22 | CHI TxnID width | G-CHI §3: 8-bit. G-CHI §16: 10 bits (D), then 12 bits (E). CHI-H confirms 12 bits, max 1024 outstanding | Internal inconsistency (guide) | [CHI](chi-architecture.md) |
| 23 | Default AxDOMAIN | AXI-L §A8.3.4: Non-shareable vs Shareable, a few lines apart | **Internal inconsistency (spec)** | [Coherency](cache-coherency-fundamentals.md) |
| 24 | Inner/Outer Shareable | ACE: separate. AXI-L/CHI-B+: merged | Version change | [Coherency](cache-coherency-fundamentals.md) |
| 25 | Cache states | ACE: 5. CHI: 7 | Version change | [Coherency](cache-coherency-fundamentals.md) |
| 26 | Cacheable → Modifiable | "Functionality unchanged", yet AXI4 added ordering rules and new allocate meanings | Wording vs substance | [Memory types](memory-types-and-cache-attributes.md) |
| 27 | Who should use HPROT | AMBA2 and AHB-C: Subordinates should avoid using it unless necessary. AHB5 with Extended_Memory_Types: detailed required behaviours | Opt-in extension | [Memory types](memory-types-and-cache-attributes.md) |
| 28 | Data/instruction polarity | AHB HPROT[0]=1 means data. APB/AXI PROT[2]=1 means instruction | Encoding difference (trap) | [Security](protection-and-security.md) |
| 29 | AXI PAS signalling | AxPROT+AxNSE vs AxPAS (mutually exclusive) | Version change | [Security](protection-and-security.md) |
| 30 | Locked transfers | Still in AHB5. Removed in AXI4+ | Design difference | [Atomics](exclusive-locked-and-atomic-access.md) |
| 31 | Exclusive write to an unmonitored location | AXI and CHI (Non-snoopable): location updated, OKAY. AHB5: "fail", update not stated. CHI general rule: IMPLEMENTATION DEFINED | Design difference (trap) | [Atomics](exclusive-locked-and-atomic-access.md) |
| 32 | Multi-copy atomicity | AXI G+ and CHI: required. AHB5: optional property | Design difference | [Atomics](exclusive-locked-and-atomic-access.md) |
| 33 | Exclusives in Shareable memory | ACE: yes. AXI-L: not allowed | Version change | [Atomics](exclusive-locked-and-atomic-access.md) |
| 34 | ACE5-LiteDVM | H.c: bidirectional by default. AXI-L: receive only, no snoop data | Version change | [DVM](dvm-and-address-translation.md) |
| 35 | Barriers | ACE: yes. ACE5 and CHI-B+: no | Version change | [ACE](ace-coherency-extensions.md) |
| 36 | DVM Complete | ACE: needed. CHI: not needed | Design difference | [DVM](dvm-and-address-translation.md) |
| 37 | LTI caching | G-SYS: no caching. LTI-D/E: optional translation cache | Outdated guide | [DVM](dvm-and-address-translation.md) |
| 38 | DTI transport | DTI-E: AXI4-Stream. DTI-J: AXI5-Stream | Version change | [DVM](dvm-and-address-translation.md) |
| 39 | CXS credits | CXS-B: 15. CXS-C onward (incl. CXS-D): 63 | Version change (Issue C) | [Flow control](handshakes-and-flow-control.md) |
| 40 | CXS purpose | Spec: PCIe/CCIX/CXL. G-SYS: C2C transport | Both true (reuse) | [Streaming](streaming-interfaces.md) |
| 41 | C2C on-chip connection | G-SYS: typically CXS. C2C-B: Packetization layer may drive pins directly | Typical vs allowed | [Chiplets](chiplets-and-chip-to-chip.md) |
| 42 | CHI issue count | G-CHI: 7 (A–G). CHI-H: H = 11th public release | Outdated guide | [CHI](chi-architecture.md) |
| 43 | ATB vs AXI ordering | ATB: total order across IDs. AXI: per ID | Design difference (stated by ATB) | [ATB](debug-trace-atb.md) |
| 44 | AXI as a "bus" | AHB-C glossary: "bus protocol". G-AXI: point-to-point interface | Wording | [Terminology](terminology-and-roles.md) |
| 45 | AXI low-power interface | AXI3/4: CSYSREQ/CACTIVE. Later: moved to the LPI spec (Q-Channel) | Version change | [Low power](low-power-and-wakeup.md) |
| 46 | CHI data protection | CHI-B: DataCheck. CHI-D: optional flit parity replaces it | Version change | [Parity/RAS](interface-protection-parity-and-ras.md) |
| 47 | AHB address width | AHB A/B: fixed 32. AHB C: ADDR_WIDTH property | Version change | [Properties](interface-properties-and-user-signals.md) |
| 48 | Credit return before sleep | CHI: all L-Credits explicitly returned (LCrdReturn). AXI5 credited: implicit return in STOP | Design difference | [Low power](low-power-and-wakeup.md), [Flow control](handshakes-and-flow-control.md) |
| 49 | SYSCOREQ/SYSCOACK scope | CHI and ACE5 (AXI-Hc §E1.8): snoops + DVM. AXI-L: DVM messages only | Scope narrowed when ACE was removed (same signal names) | [Low power](low-power-and-wakeup.md), [DVM](dvm-and-address-translation.md) |
| 50 | Bidirectional DVM on AXI | AXI-Hc: an option. AXI-L: deprecated | Version change | [DVM](dvm-and-address-translation.md) |
| 51 | DVM Hint opcode 0b110 | AXI-L: reserved "Hint" slot. CHI-H: 0b101–0b111 reserved | Design difference | [DVM](dvm-and-address-translation.md) |
| 52 | Parity group size | APB/AHB/CHI: ≤ 8 bits per check bit. AXI-L: may exceed 8 if the configuration requires | Design difference | [Parity/RAS](interface-protection-parity-and-ras.md) |
| 53 | Check_Type options | APB/AHB: Byte_All only. AXI-L/CHI-H: also Odd_Parity_Byte_Data | Design difference | [Parity/RAS](interface-protection-parity-and-ras.md) |
| 54 | Widest data bus | AXI/AHB: 1024 bits. CHI: 512 bits (128/256/512 only) | Design difference | [Bursts](bursts-sizes-and-alignment.md) |
| 55 | WRAP restrictions | Before AXI-L: any WRAP 2–16 beats, any memory. AXI-L: `Wrap_CLS_Modifiable` (default True) = one cache line, Modifiable | Version change | [Bursts](bursts-sizes-and-alignment.md) |
| 56 | Wrap address equation | AXI-J and earlier: Start_Addr + … AXI-L: Aligned_Addr + … (a listed correction, the same results in practice) | Erratum | [Bursts](bursts-sizes-and-alignment.md) |
| 57 | Device memory names | AXI: Device Non-bufferable/Bufferable. AHB: Device-nE/E. CHI: Device nRnE/nRE/RE. G-CHI: GRE names | Wording | [Memory types](memory-types-and-cache-attributes.md) |
| 58 | Write-Through | AXI/AHB: WT types exist. CHI-H: none | Design difference | [Memory types](memory-types-and-cache-attributes.md) |
| 59 | Prefetch hint response | AXI Prefetch: B response, unique ID. CHI PrefetchTgt: no response, no Retry | Design difference | [Memory types](memory-types-and-cache-attributes.md), [CHI](chi-architecture.md) |
| 60 | Deferrable write response | AXI: BRESP DEFER/UNSUPPORTED. CHI: RespErr OK + Resp code | Encoding difference | [Responses](responses-and-errors.md) |
| 61 | CHI PAS signalling | G-CHI: NSE + NS fields. CHI-H: 3-bit PAS field replaces them | Outdated guide / version change | [Security](protection-and-security.md) |
| 62 | Number of PASs | CHI-H glossary: four (adds Root, Realm). CHI-H §B10.2: six | **Internal inconsistency (spec)** | [Security](protection-and-security.md) |
| 63 | MTE support level names | AXI: Standard/Simplified/Basic/False. CHI: Full/Reduced/False (HN→SN only) | Wording | [Security](protection-and-security.md) |
| 64 | DWT definition | CHI-H glossary: DWT is "Sending Read data directly from a Snoopee or Subordinate to the Requester bypassing the Home Node". CHI-H body: write data RN→SN | **Internal inconsistency (spec)** | [CHI](chi-architecture.md) |
| 65 | PBHA width | CHI-H glossary: "up to two bits". CHI-H §B11.5 and AXI-L: 4 bits | **Internal inconsistency (spec)** | [CHI](chi-architecture.md) |
| 66 | Is CHI Retry mandatory? | G-CHI and earlier issues: base mechanism. CHI-H: `Retry_Support` may be False/RP0_Only | Version change | [Flow control](handshakes-and-flow-control.md), [Properties](interface-properties-and-user-signals.md) |
| 67 | Inner/Outer domains | CHI-B+: merged for memory. CHI-H: still used for DVM (SnpAttr = Inner/Outer DVM domain) | Scope difference | [Coherency](cache-coherency-fundamentals.md) |
| 68 | Cache line size | CHI: fixed 64 B. AXI5: `Cache_Line_Size` 16–2048 B (must be 64 with CHI) | Design difference | [Coherency](cache-coherency-fundamentals.md) |
| 69 | CHI exclusive-store result | CleanUnique(Excl): RespErr EXOK/OK. MakeReadUnique(Excl): EXOK not permitted, the cache state decides | Two mechanisms in one spec | [Atomics](exclusive-locked-and-atomic-access.md) |
| 70 | DataSource format | CHI-F: 5 bits. CHI-G+: 8 bits with defined subfields | Version change | [QoS](qos-and-traffic-modelling.md) |
| 71 | CHI MPAM width | CHI-F: as published. F.b: "corrected to 12 bits". G: adds 15-bit option | Erratum + extension | [QoS](qos-and-traffic-modelling.md) |

## How to handle a disagreement in practice

1. **Identify the protocol version** your IP implements (for example AXI4 or AXI5, CHI-E or CHI-G).
2. **Use the spec issue that defines that version**. For AXI3, AXI4 and ACE this means *AXI-Hc*, not AXI-L.
3. **Prefer specs over guides**. Guides can lag behind (items 1, 3, 22, 37, 42, 61).
4. **For internal inconsistencies** (items 14, 23, 62, 64, 65), choose an interpretation, document it in your interface spec, and if possible raise it with Arm (errata@arm.com or the support portal, as the spec feedback sections say).

## Related articles

All articles. Start from the [Index](index.md).

## Sources

All sources in the [Source key](sources.md).
