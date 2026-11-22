# AMBA Knowledge Base: Source Catalog

All files are official, **Non-Confidential** Arm documents, downloaded from
`documentation-service.arm.com` on 2026-11-21. Each file's document number and issue
were checked against its title page.

**The PDFs are not stored in this repository.** Download them into this folder with:

```
python tools/download_sources.py            # all 39 documents (~69 MB)
python tools/download_sources.py CHI AXI    # only matching documents
```

The script reads [`sources.json`](sources.json) (path, document number, issue, Arm page, direct
URL and SHA-256 for each file) and checks every download against its checksum, so you get the
exact issue the wiki cites. Each file name in the inventory below also links to its direct download.
The folder structure is kept with empty `.gitkeep` files.

- Landing page for any document: `https://developer.arm.com/documentation/<doc>/<version>`
- Check for newer issues: `python tools/check_arm_versions.py ihi0022 ihi0050 ...`
- `archive/` folders hold superseded issues. They are kept for version-delta notes and for
  protocols that were removed from newer specs (e.g., AXI3/AXI4/ACE are no longer in IHI0022 J+).

## 1. Coverage: every topic mapped to its source

| Protocol / topic | Gen | Primary source (latest) | Supporting / historical sources |
|---|---|---|---|
| ASB | AMBA 1–2 | `00-overview/IHI0011A` (Rev 2.0, ch. 4) | `00-overview/DVI0010A` (1996 intro) |
| APB (original, Rev D) | AMBA 1 | `00-overview/DVI0010A` | `IHI0011A` §5.8 (Rev D → Rev 2.0 interfacing) |
| APB2 | AMBA 2 | `00-overview/IHI0011A` (ch. 5) | |
| APB3 | AMBA 3 | `10-apb/IHI0024B` | `10-apb/IHI0024E` |
| APB4 | AMBA 4 | `10-apb/IHI0024C` | `10-apb/IHI0024E` |
| APB5 | AMBA 5 | `10-apb/IHI0024E` (Feb 2023, adds RME) | `10-apb/archive/IHI0024D` (first APB5) |
| AHB (AMBA 2) | AMBA 2 | `00-overview/IHI0011A` (ch. 3) | |
| AHB-Lite | AMBA 3 | `20-ahb/IHI0033A` | `20-ahb/IHI0033B.b` |
| AHB5 | AMBA 5 | `20-ahb/IHI0033C` (Sep 2021) | `20-ahb/IHI0033B.b` (first AHB5) |
| AXI3 | AMBA 3 | `30-axi/IHI0022H.c` | `30-axi/archive/IHI0022B` (AXI v1.0), `IHI0022C` |
| AXI4, AXI4-Lite | AMBA 4 | `30-axi/IHI0022H.c` | `30-axi/archive/IHI0022C` (first AXI4) |
| AXI5, AXI5-Lite | AMBA 5 | `30-axi/IHI0022L` (Aug 2025) | `30-axi/archive/IHI0022J` (restructured spec) |
| AXI4-Stream | AMBA 4 | `30-axi/IHI0051B` | `30-axi/IHI0051A` (original) |
| AXI5-Stream | AMBA 5 | `30-axi/IHI0051B` (2021) | |
| ACE, ACE-Lite | AMBA 4 | `30-axi/IHI0022H.c` (Part D) | `30-axi/archive/IHI0022F.b`, `IHI0022G` |
| ACE5, ACE5-Lite, ACE5-LiteDVM, ACE5-LiteACP | AMBA 5 | `30-axi/IHI0022H.c` (full ACE5) | `30-axi/IHI0022L` (ACE5-Lite variants only; full ACE5 removed) |
| CHI | AMBA 5 | `40-coherent/IHI0050H` (Sep 2025) | `40-coherent/archive/IHI0050G`, `IHI0050E.c` |
| CHI C2C | AMBA 5 | `40-coherent/IHI0098B` (Mar 2026) | |
| ATB v1.0 / v1.1 | AMBA 3–4 | `50-trace-debug/IHI0032C` (Dec 2021) | `50-trace-debug/archive/IHI0032B` |
| DTI (DTI-TBU, DTI-ATS) | AMBA 5 | `60-system-mmu/IHI0088J` (Mar 2026) | `archive/IHI0088E`, `IHI0088E.c` |
| LTI | AMBA 5 | `60-system-mmu/IHI0089E` (Mar 2026) | `archive/IHI0089D` |
| CXS | AMBA 5 | `70-specialized/IHI0079D` (Sep 2025) | `archive/IHI0079B` |
| GFB | AMBA 5 | `70-specialized/IHI0083A.b` (May 2022) | `archive/IHI0083A` |
| Q-Channel, P-Channel (LPI) | AMBA 4–5 | `80-low-power/IHI0068D` (Sep 2021) | `archive/IHI0068C` |
| ATP (Adaptive Traffic Profiles) | AMBA 5 | `00-overview/IHI0082A` (2019) | ATP Engine: github.com/ARM-software/ATP-Engine |
| Overview / learning | all | `00-overview/LTA_110303` Arm System Architectures (2025) | `30-axi/LTA_102202` Intro to AXI v3.0; `40-coherent/LTA_102407` Intro to CHI v1.2 |

## 2. File inventory

| File | Document | Issue | Date |
|---|---|---|---|
| [00-overview/DVI0010A_AMBA1_intro_1996.pdf](https://documentation-service.arm.com/static/5f106ce80daa596235e81425) | Introduction to AMBA | A | 1996 |
| [00-overview/IHI0011A_AMBA2_spec_ASB_AHB_APB.pdf](https://documentation-service.arm.com/static/642569a2314e245d086bc87e) | AMBA Specification Rev 2.0 | A | 1999 |
| [00-overview/IHI0082A_ATP.pdf](https://documentation-service.arm.com/static/5f914f6ef86e16515cdc2b62) | AMBA Adaptive Traffic Profiles Spec | A | Mar 2019 |
| [00-overview/LTA_110303_v1.0_Arm_System_Architectures.pdf](https://documentation-service.arm.com/static/682ae34f0aae2a5d8f045749) | Learn the arch: Arm System Architectures | 1.0 | May 2025 |
| [10-apb/IHI0024B_APB3.pdf](https://documentation-service.arm.com/static/64257d8379edab6d64fb6f68) | AMBA 3 APB Protocol Spec | B | Aug 2004 |
| [10-apb/IHI0024C_APB4.pdf](https://documentation-service.arm.com/static/64257f64314e245d086bc8b7) | AMBA APB Protocol Spec v2.0 | C | Apr 2010 |
| [10-apb/IHI0024E_APB5.pdf](https://documentation-service.arm.com/static/63fe2c1356ea36189d4e79f3) | AMBA APB Protocol Spec | **E (latest)** | Feb 2023 |
| [10-apb/archive/IHI0024D_APB5.pdf](https://documentation-service.arm.com/static/60d5b505677cf7536a55c245) | AMBA APB Protocol Spec | D | Apr 2021 |
| [20-ahb/IHI0033A_AHB-Lite.pdf](https://documentation-service.arm.com/static/64258237314e245d086bc8c6) | AMBA 3 AHB-Lite Protocol Spec | A | Jun 2006 |
| [20-ahb/IHI0033Bb_AHB5_AHB-Lite.pdf](https://documentation-service.arm.com/static/5f91607cf86e16515cdc3b4b) | AMBA 5 AHB Protocol Spec | B.b | Oct 2015 |
| [20-ahb/IHI0033C_AHB5.pdf](https://documentation-service.arm.com/static/6141bf0d674a052ae36ca811) | AMBA AHB Protocol Spec | **C (latest)** | Sep 2021 |
| [30-axi/IHI0022Hc_AXI3_AXI4_AXI5_ACE.pdf](https://documentation-service.arm.com/static/602a9df190ee6824a1e02b98) | AMBA AXI and ACE Protocol Spec | H.c | Jan 2021 |
| [30-axi/IHI0022L_AXI.pdf](https://documentation-service.arm.com/static/68b03beb01ae952d9559f9eb) | AMBA AXI Protocol Spec | **L (latest)** | Aug 2025 |
| [30-axi/IHI0051A_AXI4-Stream.pdf](https://documentation-service.arm.com/static/642583d7314e245d086bc8c9) | AMBA 4 AXI4-Stream Protocol Spec | A | Mar 2010 |
| [30-axi/IHI0051B_AXI-Stream.pdf](https://documentation-service.arm.com/static/64819f1516f0f201aa6b963c) | AMBA AXI-Stream Protocol Spec | **B (latest)** | Apr 2021 |
| [30-axi/LTA_102202_v3.0_Intro_AXI.pdf](https://documentation-service.arm.com/static/6800e9e95b1a8c5a27aa1a59) | Learn the arch: Intro to AMBA AXI | 3.0 / 05 | Apr 2025 |
| [30-axi/archive/IHI0022B_AXI3.pdf](https://documentation-service.arm.com/static/5f915920f86e16515cdc3342) | AMBA AXI Protocol Spec v1.0 | B | Mar 2004 |
| [30-axi/archive/IHI0022C_AXI3_AXI4.pdf](https://documentation-service.arm.com/static/64256e84314e245d086bc88f) | AMBA AXI Protocol Spec v2.0 | C | Mar 2010 |
| [30-axi/archive/IHI0022Fb_AXI_ACE.pdf](https://documentation-service.arm.com/static/5f915bbcf86e16515cdc3b23) | AMBA AXI and ACE Protocol Spec | F.b | Dec 2017 |
| [30-axi/archive/IHI0022G_AXI_ACE.pdf](https://documentation-service.arm.com/static/5f915905f86e16515cdc333b) | AMBA AXI and ACE Protocol Spec | G | Jul 2019 |
| [30-axi/archive/IHI0022J_AXI.pdf](https://documentation-service.arm.com/static/63ff0ebd56ea36189d4e7ee7) | AMBA AXI Protocol Spec | J | Mar 2023 |
| [40-coherent/IHI0050H_CHI.pdf](https://documentation-service.arm.com/static/69df590612ab715369d31af4) | AMBA CHI Architecture Spec | **H (latest)** | Sep 2025 |
| [40-coherent/IHI0098B_CHI_C2C.pdf](https://documentation-service.arm.com/static/69cbbaf03fb3b839f93e2ec2) | AMBA CHI C2C Architecture Spec | **B (latest)** | Mar 2026 |
| [40-coherent/LTA_102407_v1.2_Intro_CHI.pdf](https://documentation-service.arm.com/static/68590853961937560be90eb2) | Learn the arch: Introducing AMBA CHI | 1.2 | Jun 2025 |
| [40-coherent/archive/IHI0050G_CHI.pdf](https://documentation-service.arm.com/static/69e73291379d3e7aaa33ab54) | AMBA CHI Architecture Spec | G | Mar 2024 |
| [40-coherent/archive/IHI0050Ec_CHI.pdf](https://documentation-service.arm.com/static/63341ee5da191e7fe057d04b) | AMBA 5 CHI Architecture Spec | E.c | Sep 2022 |
| [50-trace-debug/IHI0032C_ATB.pdf](https://documentation-service.arm.com/static/61b0bea883e60c5c768e4c6a) | AMBA ATB Protocol Spec | **C (latest)** | Dec 2021 |
| [50-trace-debug/archive/IHI0032B_ATB.pdf](https://documentation-service.arm.com/static/5fb7ec16d77dd807b9a80cb6) | AMBA 4 ATB Protocol Spec | B | Mar 2012 |
| [60-system-mmu/IHI0088J_DTI.pdf](https://documentation-service.arm.com/static/69cd3daac1586b7c59b1c8af) | AMBA DTI Protocol Spec | **J (latest)** | Mar 2026 |
| [60-system-mmu/IHI0089E_LTI.pdf](https://documentation-service.arm.com/static/69cd3e493fb3b839f93e3178) | AMBA LTI Protocol Spec | **E (latest)** | Mar 2026 |
| [60-system-mmu/archive/IHI0088E_DTI.pdf](https://documentation-service.arm.com/static/60ddf202677cf7536a55cd55) | AMBA DTI Protocol Spec | E | Aug 2020 |
| [60-system-mmu/archive/IHI0088Ec_DTI.pdf](https://documentation-service.arm.com/static/65e83b84a97073311e216fc1) | AMBA DTI Protocol Spec | E.c | Mar 2024 |
| [60-system-mmu/archive/IHI0089D_LTI.pdf](https://documentation-service.arm.com/static/68ada17f46f4553a6890bc55) | AMBA LTI Protocol Spec | D | Aug 2025 |
| [70-specialized/IHI0079D_CXS.pdf](https://documentation-service.arm.com/static/68da8cd1bd7cab51328c2998) | AMBA CXS Protocol Spec | **D (latest)** | Sep 2025 |
| [70-specialized/IHI0083Ab_GFB.pdf](https://documentation-service.arm.com/static/6294e5a131ea212bb662277e) | AMBA Generic Flash Bus Protocol Spec | **A.b (latest)** | May 2022 |
| [70-specialized/archive/IHI0079B_CXS.pdf](https://documentation-service.arm.com/static/60002aa43f22832ff1d6871b) | AMBA CXS Protocol Spec | B | Dec 2020 |
| [70-specialized/archive/IHI0083A_GFB.pdf](https://documentation-service.arm.com/static/5f915d9ff86e16515cdc3b30) | AMBA Generic Flash Bus Protocol Spec | A | Jul 2018 |
| [80-low-power/IHI0068D_LPI.pdf](https://documentation-service.arm.com/static/617a637283e60c5c768e2241) | AMBA Low Power Interface Spec | **D (latest)** | Sep 2021 |
| [80-low-power/archive/IHI0068C_LPI.pdf](https://documentation-service.arm.com/static/5f915e69f86e16515cdc3b3e) | AMBA Low Power Interface Spec | C | Sep 2016 |

## 3. Known gaps

- **AMBA 1 formal spec (Rev D, 1996):** Arm doesn't host it. The 1996 *Introduction to AMBA*
  (DVI0010A) and the Rev D → Rev 2.0 notes in IHI0011A are the only official sources found.
- **No Arm "Learn the architecture" guide for APB, AHB or ACE.** Use the specs directly.
  For ACE, CHI guide 102407 and the AXI guide 102202 give context.
- **Errata documents** (e.g., CHI Issue F errata) were not collected.
- **Not downloaded:** intermediate issues CHI F/F.b/G.b, CHI C2C A/A.b, CXS A/C, DTI F–H, LTI A–C.
  Fetch them with `tools/check_arm_versions.py` if you need exact version deltas.
