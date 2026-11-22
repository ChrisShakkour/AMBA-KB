# AMBA Knowledge Base

A concept-organised wiki of Arm's AMBA on-chip interface protocols (APB, AHB, AXI, ACE, CHI, C2C, CXS, ATB, AXI-Stream, DTI/LTI, LPI and more), written for junior RTL design engineers.

- **Start here:** [wiki/index.md](wiki/index.md)
- **Source key:** [wiki/sources.md](wiki/sources.md) explains citation codes such as `AXI-L §A5.3`.
- **Sources:** the wiki is built from 42 official Arm documents (39 specifications and learning guides, plus 3 IP product manuals). They are **not stored in this repository**. [raw/SOURCES.md](raw/SOURCES.md) lists each one with its issue, date and download link, and the `raw/` folder structure is kept so the files land where the wiki's links expect them.
- **Tools:**
  - `tools/download_sources.py` downloads the documents into `raw/` and checks each against the SHA-256 in [raw/sources.json](raw/sources.json).
  - `tools/check_arm_versions.py` checks Arm's site for newer issues.

## Getting the source documents

```
python tools/download_sources.py            # all 42 documents (~75 MB)
python tools/download_sources.py CHI AXI    # only matching documents
```

Every claim in the wiki carries a citation to a source section. Text marked *Editor's note (not from the sources)* is explanation that the specifications do not state.

The Arm specifications are copyright Arm Limited and are subject to Arm's own terms. The latest versions are available from [developer.arm.com](https://developer.arm.com/documentation).
