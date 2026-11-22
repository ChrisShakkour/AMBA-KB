# Protection and security attributes

> Bits that label *who* is making an access (privileged or user, secure or non-secure, Realm or Root) so that memory protection units and firewalls can allow or block it.

## In plain words

Arm CPUs run code at different privilege levels and in different **security worlds**:
- **Privileged vs unprivileged**: the OS kernel versus a user application.
- **Secure vs Non-secure** (TrustZone): trusted firmware versus a normal OS.
- **Root and Realm** (the Realm Management Extension, RME, in Armv9): extra worlds for confidential computing (G-SYS §3).

When the CPU issues a bus access, these labels go with it. A peripheral or interconnect firewall can then say "only Secure code may write this key register". In a modern system the same physical address in different **Physical Address Spaces (PAS)** can even point at *different memory* (AXI-L §A4.5.3).

## The signals

| Protocol | Privilege | Data/Instr | Security | RME / extras |
|---|---|---|---|---|
| APB4/5 | `PPROT[0]` (1 = privileged) | `PPROT[2]` (1 = instruction) | `PPROT[1]` (**1 = Non-secure**) | `PNSE` (APB5, Issue E) |
| AHB | `HPROT[1]` | `HPROT[0]` (**1 = data**) | `HNONSEC` (AHB5, `Secure_Transfers` property) | — |
| AXI | `AxPROT[0]` or `AxPRIV` | `AxPROT[2]` or `AxINST` | `AxPROT[1]` (1 = Non-secure) | `AxNSE` with AxPROT, **or** `AxPAS[2:0]` |
| CHI | — (not carried) | — | Up to Issue G: `NS` (+ `NSE` for RME) | Issue H: a 3-bit **`PAS`** field in REQ and SNP flits "replaces NS and NSE" (CHI-H §B13.10.68, Table C5.11) |

Sources: APB-E §3.5–3.6; AHB-C §3.8–3.10; AXI-L §A4.5; CHI-H §B2.8.2, §B13.10.68; G-CHI §13.

### Physical address space encodings
| PAS | APB: PNSE, PPROT[1] | AXI: AxNSE, AxPROT[1] | AXI: AxPAS | CHI-H: PAS |
|---|---|---|---|---|
| Secure | 0, 0 | 0, 0 | 000 | 000 |
| Non-secure | 0, 1 | 0, 1 | 001 | 001 |
| Root | 1, 0 | 1, 0 | 010 | 010 |
| Realm | 1, 1 | 1, 1 | 011 | 011 |
| System Agent (GDI) | — | — | 100 | 100 |
| Non-secure Protected (GDI) | — | — | 101 | 101 |

(APB-E Table 3-5; AXI-L Table A4.7; CHI-H Table B13.47.) AXI Issue L says `AxPROT`/`AxNSE` are **superseded** by `AxPRIV`/`AxINST`/`AxPAS`, and an interface must use one set or the other, never both (AXI-L §A4.5.1). The AXI `AxPAS` and CHI `PAS` encodings are identical, which makes AXI↔CHI bridging of security straightforward.

In CHI, **the PAS is part of the address**. Two requests are to "the same location" only if both address and PAS match, and hardware coherency is *not* kept between PASs (CHI-H §B2.7.1, §B2.8.2). Moving a memory granule between PASs needs CMOs to the **PoPA** (CleanInvalidPoPA).

### Newer security features (AXI5 / CHI)
- **GDI (Granular Data Isolation)**: two extra PAS, *System Agent* and *Non-secure Protected*, for media pipelines and isolated subsystems (AXI-L §A4.5.5; CHI-H §B10.8). A **CPU (PE) may not access these PASs directly**, except for CMOs to the PoPA. In CHI, an RN-F declares with `GDI_Non_PE_RNF` whether it is a non-CPU agent allowed to use them. If not, it must answer snoops to those PASs with SnpResp_I (CHI-H §B16.1.31).
- **MEC (Memory Encryption Contexts)**: `AxMECID` / CHI `MECID` (16 bits) picks the encryption key or tweak per Realm. It must be zero for Secure, Non-secure and Root (AXI-L §A4.6; CHI-H Table B13.47). Data above the **Point of Encryption** travels as plaintext.
  - In CHI, MECID is carried on REQ, SNP **and** DAT. The DAT copy (snoop data) exists so a snoop filter need not store MECIDs (CHI-H §B10.6.1.3).
  - Evictions, CMOs and snoop-filter back-invalidations use the MECID **stored with the line**, not the one in the request (CHI-H §B10.6.2).
  - If a cache finds a stored MECID corrupted, all data from that line must be marked Poison or DERR, because writing it back with the wrong key would silently corrupt memory (CHI-H §B10.6.5).
  - In GDI systems a **MECID mismatch** must never leak data between contexts. Reads get masked data (all ones recommended), partial writes merge into masked data, and a snoopee flags `MismatchedMECID`. Loss of coherency is allowed, loss of confidentiality is not (CHI-H §B10.8.1).
- **NSAID** (AXI5): a 4-bit Non-secure Access ID, so a firewall can distinguish up to 16 Non-secure agents. It is zero for other PASs, and cached lines keep their NSAID (AXI-L §A10.1).
- **MPAM** partition IDs are kept separate per PAS through the 2-bit `MPAMSP` (CHI) / `MPAM_SP` (AXI) selector. For the GDI PASs the default maps System Agent → Root and Non-secure Protected → Non-secure (CHI-H §B11.4.1–2).
- **MTE (Memory Tagging Extension)**: a 4-bit tag per 16 bytes, carried with the data, used to catch use-after-free and buffer overflows (AXI-L §A12.2; CHI-H ch. B12; G-CHI §12). The requester checks tags on reads, the completer checks them on writes (`TagOp = Match`), and a separate TagMatch response or `BTAGMATCH` reports pass or fail. The write itself always goes ahead.
- **RME Device Assignment** (CHI, RME-DA / RME-CDA): a device, typically on a chip-to-chip link, sends StreamID and SecSID1. The host checks a Device Permission Table and the GPT on every request, and answers failures with NDERR. Devices only work in Realm and Non-secure PAS. They may snoop only their own memory, and the host must not leak snoops about memory the device may not see (CHI-H §B10.7; G-CHI §13).

## Where the sources agree

- **Privilege and instruction bits are hints.** "The transaction indication is provided as a hint and might not be accurate in all cases" (APB-E §3.5). The same wording appears in AHB-C §3.9.1 and AXI-L §A4.5.2. Only privileged vs unprivileged is distinguished, even if the CPU has more levels.
- **"Non-secure" is the asserted value.** A HIGH security bit means *Non-secure* in APB, AHB (`HNONSEC`) and AXI. AHB-C §3.10 explains why: "consistent with other signaling in implementations of the Arm Security Extensions". The safe default (LOW) is therefore *Secure*.
- RME support is an **opt-in property** (`RME_Support`) on APB5, AXI5 and CHI (APB-E §3.6.2; AXI-L Table A4.8; G-CHI §13).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Is PPROT really a security signal? | APB-E §3.5 note: "The primary use of PPROT is as an identifier for Secure or Non-secure transactions. It is acceptable to use different interpretations of the PPROT[0] and PPROT[2] identifiers" | AHB/AXI define all three bits normatively | APB-E states the loosening but gives no reason. *Editor's note (not from the sources): APB peripherals rarely need privilege or instruction information* |
| Can a Requester with PPROT talk to a Completer without it? | APB-E Table 3-3: Requester has PPROT, Completer doesn't → **compatible** (the Completer has no protection). Requester lacks PPROT, Completer has it → compatible only if a fixed tie-off is "functionally correct" | — | Not a conflict, but a trap. Tying a Completer's PPROT to a constant decides its security behaviour for every access |
| Data/instruction polarity | APB `PPROT[2]`=1 means **instruction**. AXI `AxPROT[2]`=1 means **instruction** | AHB `HPROT[0]`=1 means **data** (0 = opcode fetch) | A historical encoding difference between AHB (1999) and APB/AXI. Watch it in AHB↔AXI bridges: invert the bit |
| How AXI carries PAS | AXI-Hc: `AxPROT[1]` only (Secure/Non-secure). AXI-J/K add `AxNSE` for RME's Root and Realm | AXI-L §A4.5.1: `AxPAS` supersedes them, and the two sets are mutually exclusive | With GDI there are six PASs (AXI-L §A4.5.5), which do not fit in the two older bits |
| How CHI carries PAS | G-CHI §13 (Jun 2025): the `NSE` and `NS` fields define the PAS | CHI-H §B13.10.68 (Sep 2025): a 3-bit `PAS` field that "replaces NS and NSE fields in previous issues" | The same GDI reason as AXI. The guide predates Issue H |
| How many PASs exist | CHI-H glossary ("RME"): RME adds "two physical address spaces, Root and Realm" (four in total) | CHI-H §B10.2: an RME system "defines **six** Physical Address Spaces". The note says that before Issue H there were four | An **internal inconsistency** in CHI-H: the glossary was not updated for GDI |
| MTE support levels | AXI-L §A12.2.1: `MTE_Support` = Standard / Simplified / Basic / False | CHI-H §B16.1.23: `MTE_Support` = Full / Reduced / False, and it applies only to the Home→Subordinate interface | Different names for similar subsets. With Reduced/Simplified support the Home must do tag matching itself, or read-modify-write partial tag updates |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- A secure-only register block on APB: decode `PPROT[1]` (and `PNSE` if present) in the SETUP phase, and return `PSLVERR` (or read zero / ignore the write, as your security policy says) for Non-secure accesses.
- In AHB↔AXI bridges, map `HPROT[0]` (data=1) → `AxPROT[2]` (instruction=1) with an **inverter**, and `HNONSEC` → `AxPROT[1]` directly.
- Never "fix" a missing security bit by tying it to Secure on an interface that Non-secure software can reach.

## Related articles

- [Memory types and cache attributes](memory-types-and-cache-attributes.md)
- [DVM and address translation](dvm-and-address-translation.md) (StreamIDs, SMMU)
- [Interface properties and user signals](interface-properties-and-user-signals.md)

## Sources

APB-C, APB-E, AHB-C, AXI-Hc, AXI-L (read in full), CHI-H (read in full), G-CHI, G-SYS. See [Source key](sources.md).
