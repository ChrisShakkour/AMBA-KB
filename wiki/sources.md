# Source key

Every article in this wiki cites sources with a short **code** (for example `APB-E §3.4` means *AMBA APB Protocol Specification, Issue E, section 3.4*). This page maps each code to its Arm documentation page and to its local file in [`../raw/`](../raw/). The PDFs are not stored in the repository: run `python tools/download_sources.py` from the repository root to download them (see [`../raw/SOURCES.md`](../raw/SOURCES.md)).

All sources are official, Non-Confidential Arm documents: 39 specifications and learning guides, plus 3 IP product manuals. They were downloaded from `documentation-service.arm.com` on 2026-11-21. For the full download catalog, see [`../raw/SOURCES.md`](../raw/SOURCES.md).

## Specifications

| Code | Document | Issue / date | File |
|---|---|---|---|
| INTRO96 | Introduction to AMBA (DVI 0010A) | A, Oct 1996 | [Arm page](https://developer.arm.com/documentation/dvi0010/a) · [local pdf](../raw/00-overview/DVI0010A_AMBA1_intro_1996.pdf) |
| AMBA2 | AMBA Specification Rev 2.0 (IHI 0011A): ASB, AHB, APB2 | A, 1999 | [Arm page](https://developer.arm.com/documentation/ihi0011/a) · [local pdf](../raw/00-overview/IHI0011A_AMBA2_spec_ASB_AHB_APB.pdf) |
| APB-B | AMBA 3 APB Protocol Spec (APB3) | B, 2004 | [Arm page](https://developer.arm.com/documentation/ihi0024/b) · [local pdf](../raw/10-apb/IHI0024B_APB3.pdf) |
| APB-C | AMBA APB Protocol Spec v2.0 (APB4) | C, 2010 | [Arm page](https://developer.arm.com/documentation/ihi0024/c) · [local pdf](../raw/10-apb/IHI0024C_APB4.pdf) |
| APB-D | AMBA APB Protocol Spec (first APB5) | D, 2021 | [Arm page](https://developer.arm.com/documentation/ihi0024/d) · [local pdf](../raw/10-apb/archive/IHI0024D_APB5.pdf) |
| APB-E | AMBA APB Protocol Spec (APB5 + RME) | E, 2023 | [Arm page](https://developer.arm.com/documentation/ihi0024/e) · [local pdf](../raw/10-apb/IHI0024E_APB5.pdf) |
| AHB-A | AMBA 3 AHB-Lite Protocol Spec | A, 2006 | [Arm page](https://developer.arm.com/documentation/ihi0033/a) · [local pdf](../raw/20-ahb/IHI0033A_AHB-Lite.pdf) |
| AHB-Bb | AMBA 5 AHB Protocol Spec (first AHB5) | B.b, 2015 | [Arm page](https://developer.arm.com/documentation/ihi0033/bb) · [local pdf](../raw/20-ahb/IHI0033Bb_AHB5_AHB-Lite.pdf) |
| AHB-C | AMBA AHB Protocol Spec (AHB5) | C, 2021 | [Arm page](https://developer.arm.com/documentation/ihi0033/c) · [local pdf](../raw/20-ahb/IHI0033C_AHB5.pdf) |
| AXI-B | AMBA AXI Protocol Spec v1.0 (AXI3) | B, 2004 | [Arm page](https://developer.arm.com/documentation/ihi0022/b) · [local pdf](../raw/30-axi/archive/IHI0022B_AXI3.pdf) |
| AXI-C | AMBA AXI Protocol Spec v2.0 (AXI3 + AXI4) | C, 2010 | [Arm page](https://developer.arm.com/documentation/ihi0022/c) · [local pdf](../raw/30-axi/archive/IHI0022C_AXI3_AXI4.pdf) |
| AXI-Fb | AMBA AXI and ACE Protocol Spec | F.b, 2017 | [Arm page](https://developer.arm.com/documentation/ihi0022/fb) · [local pdf](../raw/30-axi/archive/IHI0022Fb_AXI_ACE.pdf) |
| AXI-G | AMBA AXI and ACE Protocol Spec | G, 2019 | [Arm page](https://developer.arm.com/documentation/ihi0022/g) · [local pdf](../raw/30-axi/archive/IHI0022G_AXI_ACE.pdf) |
| AXI-Hc | AMBA AXI and ACE Protocol Spec: **last issue with AXI3, AXI4 and ACE** | H.c, 2021 | [Arm page](https://developer.arm.com/documentation/ihi0022/hc) · [local pdf](../raw/30-axi/IHI0022Hc_AXI3_AXI4_AXI5_ACE.pdf) |
| AXI-J | AMBA AXI Protocol Spec (restructured, AXI5 only) | J, 2023 | [Arm page](https://developer.arm.com/documentation/ihi0022/j) · [local pdf](../raw/30-axi/archive/IHI0022J_AXI.pdf) |
| AXI-L | AMBA AXI Protocol Spec (latest) | L, Aug 2025 | [Arm page](https://developer.arm.com/documentation/ihi0022/l) · [local pdf](../raw/30-axi/IHI0022L_AXI.pdf) |
| AXIS-A | AMBA 4 AXI4-Stream Protocol Spec | A, 2010 | [Arm page](https://developer.arm.com/documentation/ihi0051/a) · [local pdf](../raw/30-axi/IHI0051A_AXI4-Stream.pdf) |
| AXIS-B | AMBA AXI-Stream Protocol Spec (AXI4/AXI5-Stream) | B, 2021 | [Arm page](https://developer.arm.com/documentation/ihi0051/b) · [local pdf](../raw/30-axi/IHI0051B_AXI-Stream.pdf) |
| CHI-Ec | AMBA 5 CHI Architecture Spec | E.c, 2022 | [Arm page](https://developer.arm.com/documentation/ihi0050/ec) · [local pdf](../raw/40-coherent/archive/IHI0050Ec_CHI.pdf) |
| CHI-G | AMBA CHI Architecture Spec | G, 2024 | [Arm page](https://developer.arm.com/documentation/ihi0050/g) · [local pdf](../raw/40-coherent/archive/IHI0050G_CHI.pdf) |
| CHI-H | AMBA CHI Architecture Spec (latest) | H, Sep 2025 | [Arm page](https://developer.arm.com/documentation/ihi0050/h) · [local pdf](../raw/40-coherent/IHI0050H_CHI.pdf) |
| C2C-B | AMBA CHI Chip-to-Chip (C2C) Architecture Spec | B, Mar 2026 | [Arm page](https://developer.arm.com/documentation/ihi0098/b) · [local pdf](../raw/40-coherent/IHI0098B_CHI_C2C.pdf) |
| ATB-B | AMBA 4 ATB Protocol Spec (ATBv1.0/v1.1) | B, 2012 | [Arm page](https://developer.arm.com/documentation/ihi0032/b) · [local pdf](../raw/50-trace-debug/archive/IHI0032B_ATB.pdf) |
| ATB-C | AMBA ATB Protocol Spec (ATB-C) | C, 2021 | [Arm page](https://developer.arm.com/documentation/ihi0032/c) · [local pdf](../raw/50-trace-debug/IHI0032C_ATB.pdf) |
| DTI-E | AMBA DTI Protocol Spec | E, 2020 | [Arm page](https://developer.arm.com/documentation/ihi0088/e-a) · [local pdf](../raw/60-system-mmu/archive/IHI0088E_DTI.pdf) |
| DTI-Ec | AMBA DTI Protocol Spec (the issue that keeps DTI-TBUv1/v2) | E.c, Mar 2024 | [Arm page](https://developer.arm.com/documentation/ihi0088/ec) · [local pdf](../raw/60-system-mmu/archive/IHI0088Ec_DTI.pdf) |
| DTI-J | AMBA DTI Protocol Spec (latest) | J, Mar 2026 | [Arm page](https://developer.arm.com/documentation/ihi0088/j) · [local pdf](../raw/60-system-mmu/IHI0088J_DTI.pdf) |
| LTI-D | AMBA LTI Protocol Spec | D, Aug 2025 | [Arm page](https://developer.arm.com/documentation/ihi0089/d) · [local pdf](../raw/60-system-mmu/archive/IHI0089D_LTI.pdf) |
| LTI-E | AMBA LTI Protocol Spec (latest) | E, Mar 2026 | [Arm page](https://developer.arm.com/documentation/ihi0089/e) · [local pdf](../raw/60-system-mmu/IHI0089E_LTI.pdf) |
| CXS-B | AMBA CXS Protocol Spec | B, 2020 | [Arm page](https://developer.arm.com/documentation/ihi0079/b) · [local pdf](../raw/70-specialized/archive/IHI0079B_CXS.pdf) |
| CXS-D | AMBA CXS Protocol Spec (latest) | D, Sep 2025 | [Arm page](https://developer.arm.com/documentation/ihi0079/d) · [local pdf](../raw/70-specialized/IHI0079D_CXS.pdf) |
| GFB-A | AMBA Generic Flash Bus Protocol Spec | A, 2018 | [Arm page](https://developer.arm.com/documentation/ihi0083/a) · [local pdf](../raw/70-specialized/archive/IHI0083A_GFB.pdf) |
| GFB-Ab | AMBA Generic Flash Bus Protocol Spec | A.b, 2022 | [Arm page](https://developer.arm.com/documentation/ihi0083/ab) · [local pdf](../raw/70-specialized/IHI0083Ab_GFB.pdf) |
| LPI-C | AMBA Low Power Interface Spec | C, 2016 | [Arm page](https://developer.arm.com/documentation/ihi0068/c) · [local pdf](../raw/80-low-power/archive/IHI0068C_LPI.pdf) |
| LPI-D | AMBA Low Power Interface Spec (Q-Channel, P-Channel) | D, 2021 | [Arm page](https://developer.arm.com/documentation/ihi0068/d) · [local pdf](../raw/80-low-power/IHI0068D_LPI.pdf) |
| ATP-A | AMBA Adaptive Traffic Profiles Spec | A, 2019 | [Arm page](https://developer.arm.com/documentation/ihi0082/a) · [local pdf](../raw/00-overview/IHI0082A_ATP.pdf) |

## Arm learning guides (not normative)

| Code | Document | Version | File |
|---|---|---|---|
| G-AXI | Learn the architecture: An introduction to AMBA AXI (102202) | 3.0, Apr 2025 | [Arm page](https://developer.arm.com/documentation/102202/0300) · [local pdf](../raw/30-axi/LTA_102202_v3.0_Intro_AXI.pdf) |
| G-CHI | Learn the architecture: Introducing AMBA CHI (102407) | 1.2, Jun 2025 | [Arm page](https://developer.arm.com/documentation/102407/0102) · [local pdf](../raw/40-coherent/LTA_102407_v1.2_Intro_CHI.pdf) |
| G-SYS | Learn the architecture: Arm System Architectures (110303) | 1.0, May 2025 | [Arm page](https://developer.arm.com/documentation/110303/0100) · [local pdf](../raw/00-overview/LTA_110303_v1.0_Arm_System_Architectures.pdf) |

> **Which source wins?** When a spec and a learning guide disagree, the **specification is normative** (it is the rule). The guides are written to teach and are sometimes out of date. When two issues of the same spec disagree, the **newer issue** describes the current protocol. The older one still describes the older protocol version that existing IP may implement.

## Arm IP product manuals (not specifications)

These Technical Reference Manuals describe Arm **products** (component libraries), not protocols. The wiki cites them only in [Bridges, adapters and converters](bridges-and-adapters.md), as examples of how Arm builds bridges and converters. Where a manual and a specification differ, the specification is the rule.

| Code | Document | Issue / date | File |
|---|---|---|---|
| CMSDK-C | Cortex-M System Design Kit Technical Reference Manual, r1p0 (DDI 0479) | C, 19 Apr 2013 (Issue D also exists) | [Arm page](https://developer.arm.com/documentation/ddi0479/c) · [local pdf](../raw/90-ip-products/DDI0479C_CMSDK_TRM.pdf) |
| NIC400-J | CoreLink NIC-400 Network Interconnect Technical Reference Manual, r1p2 (DDI 0475) | J, 27 Nov 2017 | [Arm page](https://developer.arm.com/documentation/ddi0475/j) · [local pdf](../raw/90-ip-products/DDI0475J_NIC-400_TRM.pdf) |
| CSSOC-F | CoreSight SoC-400 Technical Reference Manual, r3p1 (DDI 0480) | F, 26 Sep 2013 (Issue G also exists) | [Arm page](https://developer.arm.com/documentation/ddi0480/f) · [local pdf](../raw/90-ip-products/DDI0480F_CoreSight_SoC-400_TRM.pdf) |

Reading depth: the component lists, the introduction of every bridge and converter section, and NIC-400 ch. 1–2 were read. Register descriptions, signal tables and timing diagrams were not read.

## How the sources were read

| Depth | Sources |
|---|---|
| Read in full | **AXI-L** and **CHI-H**. CHI-H C1 field-mapping and C4 per-transaction tables were spot-checked only. **AXI-Hc** covers Parts A–G, including ACE, ACE-Lite, DVM, barriers and the G7 revision history. **C2C-B**: the ch. B15 register-field tables were scanned only. **AMBA2**: ch. 1–5 read; the AHB/ASB timing-parameter tables and ch. 6 test methodology were scanned. **CXS-D**, **LPI-D** (Q- and P-Channel), **ATB-C**, **AXIS-B**, **INTRO96**, **G-SYS** and **G-CHI** |
| Protocol chapters read; field-encoding tables scanned | **DTI-J**: overview, connection management, flow control, invalidation sequence and deadlock rules, dependencies, ATS sequence, transport and revisions. Per-field encodings and the pseudocode were scanned. **LTI-E**: ch. B1–B2 and B6–B12, plus revisions. Signal tables and the C1–C6 mapping appendices were scanned. **ATP-A**: ch. 1–2 and 4, with timing tables scanned. **G-AXI**: ch. 1–3 read; ch. 4–7 skimmed. **AXI-C**: ch. 1 and the AXI4 chapter 13 |
| Every wiki citation checked by targeted search, and release notes/dates checked | APB-B, APB-C, APB-D, AHB-A (introduction, multi-layer, glossary), AHB-Bb, AXI-B, AXI-Fb, AXI-G, AXI-J, AXIS-A, CHI-Ec, CHI-G, ATB-B, DTI-E, DTI-Ec, LTI-D, CXS-B, LPI-C, GFB-A, GFB-Ab, AHB-C, APB-E. These older issues were **not** diffed line by line against the newer ones |

**Automated checks (November 2026).** A script compared every quotation in the wiki against the text of the source it cites, and confirmed that every cited section number exists in that source. Misquotes were corrected to the exact source wording. Short phrases in quotation marks that explain an idea in plain words (for example "please fetch this line") are the wiki's own glosses, not quotations.

**Editor's notes.** Any explanation that no source states is labelled *Editor's note (not from the sources)*. Each RTL-tips section also says that uncited tips are editor's suggestions. Transaction-by-transaction tables are summarised, not reproduced. Go to the spec chapter that each article cites for that level of detail.
