from pathlib import Path
import re

data = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
).read_bytes()

# CPhysicalEntity VF: lea rax,[rip]; mov [rsi], rax; lea rax,[rip]
pat = re.compile(bytes.fromhex("48 8D 05") + b".{3}" + bytes.fromhex("48 89 06 48 8D 05") + b".{3}")
hits = [m.start() for m in pat.finditer(data)]
print(f"CPhysicalEntity-like lea/mov/lea: {len(hits)}")
for h in hits[:12]:
    chunk = data[h : h + 40]
    print(f"  0x{h:X}  {' '.join(f'{b:02X}' for b in chunk)}")

pat2 = bytes.fromhex("48 8B C4 48 89 58 08 48 89 70 10 48 89 78 18 55 41 54 41 55 41 56 41 57 48 8D A8")
print(f"\nluaV-like prologue hits: {data.count(pat2)}")
start = 0
for _ in range(8):
    h = data.find(pat2, start)
    if h < 0:
        break
    print(f"  0x{h:X}")
    start = h + 1

# CGeomCache vtable setup candidates
pat3 = re.compile(bytes.fromhex("48 8D 05") + b".{3}" + bytes.fromhex("4C 89 71 18 4C 89 71 20 4C 89 71 28"))
hits3 = [m.start() for m in pat3.finditer(data)]
print(f"\nCGeomCache-like vtable init: {len(hits3)}")
for h in hits3[:8]:
    chunk = data[h : h + 48]
    print(f"  0x{h:X}  {' '.join(f'{b:02X}' for b in chunk)}")

# CPhysicalEntity ctor: look for E8 rel32 33 D2 83 8B with broader window
pat4 = re.compile(bytes.fromhex("E8") + b".{4}" + bytes.fromhex("33 D2 83 8B"))
hits4 = [m.start() for m in pat4.finditer(data)]
print(f"\nE8..33 D2 83 8B hits: {len(hits4)}")
for h in hits4[:8]:
    chunk = data[h : h + 24]
    print(f"  0x{h:X}  {' '.join(f'{b:02X}' for b in chunk)}")

# verify candidate patterns with scanner logic from scan_patterns.py
from scan_patterns import scan

candidates = [
    ("luaV_execute_v2", "48 8B C4 48 89 58 08 48 89 70 10 48 89 78 18 55 41 54 41 55 41 56 41 57 48 8D A8"),
    ("CGeomCache_v2", "48 8D 05 ? ? ? ? 4C 89 71 18 4C 89 71 20 4C 89 71 28"),
    ("CPhysicalEntityVF_v2", "48 8D 05 ? ? ? ? 48 89 06 48 8D 05"),
    ("CPhysicalEntity_ctor_v2", "E8 ? ? ? ? 33 D2 83 8B"),
]
print("\nCandidate unique matches:")
for name, pat in candidates:
    off = scan(data, pat)
    print(f"  {name}: {'MISS' if off is None else f'0x{off:X}'}")
