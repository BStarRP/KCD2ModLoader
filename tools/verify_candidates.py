from pathlib import Path
from scan_patterns import scan

data = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
).read_bytes()


def dump(off: int, before: int = 32, after: int = 48) -> None:
    chunk = data[off - before : off + after]
    print(f"@{off:#x}: {' '.join(f'{b:02X}' for b in chunk)}")


candidates = [
    ("CGeomCache VF v2", "48 8D 05 ? ? ? ? 4C 89 71 18 4C 89 71 20 4C 89 71 28"),
    ("CGeomCache VF v3", "48 89 01 48 8D 05 ? ? ? ? 4C 89 71 18 4C 89 71 20"),
    ("CPhysicalEntity VF v2", "48 8D 05 ? ? ? ? 48 89 06 48 8D 05 ? ? ? ? 88 4E"),
    ("CPhysicalEntity VF v3", "48 8D 05 ? ? ? ? 48 89 06 48 8D 05 ? ? ? ? C6 46 47"),
    ("CPhysicalEntity VF v4", "48 8D 05 ? ? ? ? 48 89 06 48 8D 05 ? ? ? ? 88 46 47"),
    ("CPhysicalEntity ctor v3", "E8 ? ? ? ? 8B 83 24 02 00 00 33 D2 83 8B"),
    ("CPhysicalEntity ctor v4", "E8 ? ? ? ? 8B 83 ? ? ? ? 33 D2 83 8B"),
    ("luaV_execute v2", "48 8B C4 48 89 58 08 48 89 70 10 48 89 78 18 55 41 54 41 55 41 56 41 57 48 81 EC"),
]

for name, pat in candidates:
    off = scan(data, pat)
    print(f"{name}: {off:#x}" if off is not None else f"{name}: MISS")

print("\nContext around CPhysicalEntity-ish site 0x58f50:")
dump(0x58F50, 0, 64)

print("\nContext around 0x38b6288 (33 D2 83 8B):")
dump(0x38B6288, 48, 16)

# find E8 before 0x38b6288 within 32 bytes
for back in range(4, 40):
    off = 0x38B6288 - back
    if data[off] == 0xE8:
        rel = int.from_bytes(data[off + 1 : off + 5], "little", signed=True)
        target = off + 5 + rel
        print(f"E8 at {off:#x} -> {target:#x}")
