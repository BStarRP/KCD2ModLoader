#!/usr/bin/env python3
"""Find candidate replacements for broken KCD2ModLoader patterns."""

from __future__ import annotations

import re
from pathlib import Path

DLL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
)
data = DLL.read_bytes()


def find_all(needle: bytes, limit: int = 20) -> list[int]:
    out: list[int] = []
    start = 0
    while len(out) < limit:
        i = data.find(needle, start)
        if i < 0:
            break
        out.append(i)
        start = i + 1
    return out


def hex_preview(off: int, before: int = 16, after: int = 48) -> str:
    chunk = data[max(0, off - before) : off + after]
    return " ".join(f"{b:02X}" for b in chunk)


queries = {
    "CGeomCache anchor (48 8B F9 4C 89 71 20)": bytes.fromhex("48 8B F9 4C 89 71 20"),
    "CGeomCache alt (4C 89 71 20)": bytes.fromhex("4C 89 71 20"),
    "CPhysicalEntity VF lea/mov (48 8D 05 ... 88 4E 47)": None,
    "CPhysicalEntity partial (88 4E 47)": bytes.fromhex("88 4E 47"),
    "game_luaV_execute head (48 8B C4 48 89 58)": bytes.fromhex("48 8B C4 48 89 58"),
    "CPhysicalEntity_ctor tail (33 D2 83 8B)": bytes.fromhex("33 D2 83 8B"),
}

print(f"Scanning {DLL.name} ({len(data)} bytes)\n")

for label, needle in queries.items():
    if needle is None:
        continue
    hits = find_all(needle, 8)
    print(f"{label}: {len(hits)} hit(s)")
    for h in hits[:5]:
        print(f"  file+0x{h:X}  {hex_preview(h)}")
    print()

# regex-style search for CPhysicalEntity VF table setup
pat = re.compile(re.escape(bytes.fromhex("48 8D 05")) + b".{3}" + re.escape(bytes.fromhex("48 89 06 48 8D 05")) + b".{3}" + re.escape(bytes.fromhex("88 4E 47")))
pe_hits = [m.start() for m in pat.finditer(data)][:10]
print(f"CPhysicalEntity VF table pattern: {len(pe_hits)} hit(s)")
for h in pe_hits:
    print(f"  file+0x{h:X}  {hex_preview(h)}")

# luaV_execute: prologue with 48 81 EC and many pushes
pat2 = re.compile(bytes.fromhex("48 8B C4 48 89 58") + b"." + bytes.fromhex("89 50") + b"." + bytes.fromhex("55 56 57 41 54 41 55 41 56 41 57 48 81 EC"))
lua_hits = [m.start() for m in pat2.finditer(data)][:10]
print(f"\ngame_luaV_execute-like prologues: {len(lua_hits)} hit(s)")
for h in lua_hits:
    print(f"  file+0x{h:X}  {hex_preview(h, 0, 32)}")

# CPhysicalEntity ctor: E8 xx xx xx xx 33 D2 83 8B
pat3 = re.compile(bytes.fromhex("E8") + b"...\x33\xD2\x83\x8B")
ctor_hits = [m.start() for m in pat3.finditer(data)][:15]
print(f"\nCPhysicalEntity_ctor-like (E8 ... 33 D2 83 8B): {len(ctor_hits)} hit(s)")
for h in ctor_hits:
    print(f"  file+0x{h:X}  {hex_preview(h)}")
