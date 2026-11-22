# Endianness and byte lanes

> Which wires of the data bus carry which byte, and what changes when data is big-endian or little-endian.

## In plain words

A 32-bit bus has four **byte lanes**: bits [7:0], [15:8], [23:16] and [31:24]. When you access one byte at address 0x1001, *which lane* carries it? And when you store the 32-bit number 0x0A0B0C0D, does 0x0A or 0x0D go to the lowest address? The first question is about **byte lanes**, the second about **endianness**.

AMBA's answer today is **byte invariance**: a single byte always travels on the same lane for a given address, whatever the endianness. Only the *order of bytes inside a multi-byte value* changes (AXI-L §A3.2.4; AHB-C §6.2.4).

## Key ideas

1. **Lane for a byte** (little-endian and byte-invariant big-endian): `Byte_Lane = Address mod Data_Bus_Bytes`, carried on `DATA[8×lane+7 : 8×lane]` (AHB-C §6.2.1–6.2.2; AXI-L §A3.1.6).
2. **Little-endian**: the least significant byte goes to the lowest address.
3. **Byte-invariant big-endian (BE8)**: same lanes as little-endian for single bytes, but the most significant byte goes to the lowest address.
4. **Word-invariant big-endian (BE32)**: a legacy scheme in which a *byte* uses a different lane than in little-endian (inside each 32-bit word the lane is flipped: `3 − Byte_Offset`) (AHB-C §6.2.3).
5. **Byte invariance lets mixed-endian structures share memory**. Arm's example is a packet whose header is little-endian and whose payload is big-endian (AXI-L Fig. A3.5; AHB-C Fig. 6-1).

## 32-bit bus lane tables (from AHB-C Tables 6-1 to 6-3)

| Access | Offset | Little-endian lanes | BE8 lanes | BE32 lanes |
|---|---|---|---|---|
| Word | 0 | [31:0] (MS byte in [31:24]) | [31:0] (MS byte in [7:0]) | [31:0] (MS byte in [31:24]) |
| Halfword | 0 | [15:0] | [15:0] | **[31:16]** |
| Halfword | 2 | [31:16] | [31:16] | **[15:0]** |
| Byte | 0 | [7:0] | [7:0] | **[31:24]** |
| Byte | 3 | [31:24] | [31:24] | **[7:0]** |

## Endianness inside operations

- **AXI atomics** carry an endianness bit: `AWATOP[3]` says whether an AtomicStore or AtomicLoad does arithmetic as little- or big-endian. It is ignored for bitwise operations (AXI-L §A6.4.6).
- **Strobes do not depend on endianness**. `HWSTRB[n]` always covers `HWDATA[8n+7:8n]` (AHB-C §3.5).
- **AXI-Stream**: "the low order bytes of the data bus are the earlier bytes in a data stream" (AXIS-B §2.4.2).

## Where the sources agree

- AXI and AHB5 both use **byte-invariant** endianness for mixed-endian support (AXI-L §A3.2.4; AHB-C §6.2.4).
- Narrow transfers in a burst move to **different lanes each beat** (AMBA2 §3.10.1; AHB-C §6.2; AXI-L §A3.2.3).

## Where the sources disagree (and why)

| Topic | Source A | Source B | Why |
|---|---|---|---|
| Does AHB define endianness? | AMBA2 §3.10.1, §3.10.3: "AHB **does not specify** the required endianness … all masters and slaves on the bus are of the same endianness". "**Dynamic endianness is not supported**" | AHB-C §6.2: "AHB supports both big-endian and little-endian systems". AHB5 adds the `Endian` property choosing **BE8** or **BE32** | AMBA2 §3.10.3 gives its reason: dynamic endianness "in the majority of embedded systems, … would lead to a significant silicon overhead that is redundant". It recommends bi-endian modules only for blocks used "in a wide variety of applications". *Editor's note (not from the sources): AHB-C gives no reason for adding the BE8/BE32 `Endian` property. BE8 is the big-endian format of Armv6 and later Arm processors* |
| Big-endian lane table | AMBA2 Table 3-7 (big-endian, 32-bit) puts byte 0 on [31:24] | AHB-C Table 6-2 (BE8) puts byte 0 on [7:0]. Only Table 6-3 (BE32) puts it on [31:24] | AMBA2's "big-endian" table *is* word-invariant BE32. Byte invariance (BE8) came later. Check which scheme an old IP means by "big-endian" |
| How big-endian components connect to AXI | AXI-L §A3.2.4: "components that support only big-endian transfers require a conversion function for byte-invariant operation" | AHB-C keeps BE32 as a legal native mode | *Editor's note (not from the sources):* AXI is byte-invariant only. AHB5 still allows BE32 for legacy Arm cores |

## RTL tips

*Tips that carry a source citation restate spec rules. Uncited tips are editor's implementation suggestions derived from those rules, not text from the specifications.*

- Write your lane-select logic from the equation `lane = addr % bus_bytes`, not from a hard-coded table. It then works for any bus width.
- If you bridge an old "big-endian AHB" block onto AXI, first find out whether it is BE32. If so, a byte-swap is needed inside each 32-bit word for sub-word accesses.

## Related articles

- [Bursts, sizes and alignment](bursts-sizes-and-alignment.md)
- [Exclusive access, locked transfers and atomics](exclusive-locked-and-atomic-access.md)
- [Streaming interfaces](streaming-interfaces.md)

## Sources

AMBA2, AHB-C, AXI-L, AXIS-B. See [Source key](sources.md).
