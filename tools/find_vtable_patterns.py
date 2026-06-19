#!/usr/bin/env python3
from pathlib import Path
from scan_patterns import parse_pattern, scan

DLL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
)
data = DLL.read_bytes()


def count_all(pattern_str: str) -> list[int]:
    pattern = parse_pattern(pattern_str)
    psize = len(pattern)
    scan_size = (psize >> 1) + (psize & 1)
    hits: list[int] = []
    for i in range(len(data) - psize + 1):
        ok = True
        for j in range(scan_size):
            left = pattern[j]
            if left is not None and data[i + j] != left:
                ok = False
                break
            right = pattern[psize - j - 1]
            if right is not None and data[i + psize - j - 1] != right:
                ok = False
                break
        if ok:
            hits.append(i)
    return hits


def rip_vtable(hit: int, offset: int) -> int:
    addr = hit + offset
    rel = int.from_bytes(data[addr + 4 : addr + 8], "little", signed=True)
    return addr + 4 + rel


def get_call(e8: int) -> int:
    rel = int.from_bytes(data[e8 + 1 : e8 + 5], "little", signed=True)
    return e8 + 5 + rel


# CVegetations
ctor_hit = scan(data, "E8 ? ? ? ? 48 8B D0 F2 0F 10 43")
ctor = get_call(ctor_hit)
print(f"CVegetations_Ctor call @ {hex(ctor)}")
for off in range(0x30, 0x50):
    vt = rip_vtable(ctor, off)
    if 0 <= vt < len(data):
        print(f"  offset(0x{off:X}).rip() -> {hex(vt)} first8={data[vt:vt+8].hex()}")

print("\nCVegetations vtable lea patterns:")
for p in [
    "48 8D 05 ? ? ? ? 48 89 01 48 8B C1 48 89 51 50",
    "48 8D 05 ? ? ? ? 48 89 01 48 8B C1 48 89 51 50 89 51 58 88 51 5C",
    "48 8D 05 ? ? ? ? 48 89 01 48 8B C1 48 89 51 50 89 51 58 88 51 5C 48 89 51 70",
    "48 8D 05 ? ? ? ? 48 89 01 48 8B C1 48 89 51 50 89 51 58 88 51 5C 48 89 51 70 89 51 78 66 89 51 7C",
]:
    hits = count_all(p)
    print(f"  {len(hits)} hits: {[hex(h) for h in hits]}")

# CMergedMeshRenderNode
mm_hit = scan(data, "B9 E0 02 00 00 E8")
mm_ctor = get_call(mm_hit + 0x18)
print(f"\nCMergedMeshRenderNode_Ctor @ {hex(mm_ctor)}")
for off in range(0x80, 0xA8, 4):
    vt = rip_vtable(mm_ctor, off)
    if 0 <= vt < len(data):
        print(f"  offset(0x{off:X}).rip() -> {hex(vt)} first8={data[vt:vt+8].hex()}")

print("\nCMergedMesh vtable lea patterns near ctor:")
for p in [
    "48 8D 05 ? ? ? ? 48 89 01",
    "48 8D 05 ? ? ? ? 48 89 01 48 8B",
]:
    hits = count_all(p)
    near = [h for h in hits if abs(h - mm_ctor) < 0x200]
    print(f"  {len(hits)} total, {len(near)} near ctor: {[hex(h) for h in near[:5]]}")
