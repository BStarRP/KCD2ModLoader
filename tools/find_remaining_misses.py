#!/usr/bin/env python3
from pathlib import Path
from scan_patterns import scan, parse_pattern

d = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
).read_bytes()


def count(p):
    pat = parse_pattern(p)
    ps = len(pat)
    ss = (ps >> 1) + (ps & 1)
    hits = []
    for i in range(len(d) - ps + 1):
        ok = True
        for j in range(ss):
            if pat[j] is not None and d[i + j] != pat[j]:
                ok = False
                break
            r = pat[ps - j - 1]
            if r is not None and d[i + ps - j - 1] != r:
                ok = False
                break
        if ok:
            hits.append(i)
    return hits


def dump(off, n=64):
    return " ".join(f"{b:02X}" for b in d[off : off + n])


misses = {
    "CStatObj_ctor": "E8 ? ? ? ? 48 8B F8 4C 89 BF",
    "C_Player_ctor": "40 55 53 56 57 41 56 48 8B EC 48 81 EC ? ? ? ? 48 8B D9 E8 ? ? ? ? 33 F6",
    "CD3D9Renderer_UnProjectFromScreen": "E8 ? ? ? ? F3 44 0F 10 05 ? ? ? ? 48 8D 45 ? 48 89 44 24 ? 41 0F 28 D8",
}

for name, old in misses.items():
    print(f"\n=== {name} ===")
    print("OLD:", scan(d, old))
    if name == "CStatObj_ctor":
        cands = [
            "E8 ? ? ? ? 48 8B F8 4C 89 BF",
            "E8 ? ? ? ? 48 8B F8 4C 89 BE",
            "E8 ? ? ? ? 48 8B F8 4C 89 B7",
            "E8 ? ? ? ? 48 8B F8 48 89 BF",
            "E8 ? ? ? ? 48 8B F8 4C 89 B7 ? ? ? ?",
        ]
    elif name == "C_Player_ctor":
        cands = [
            "40 55 53 56 57 41 56 48 8B EC 48 81 EC ? ? ? ? 48 8B D9 E8 ? ? ? ? 33 F6",
            "40 55 53 56 57 41 56 48 8B EC 48 81 EC ? ? ? ? 48 8B D9 E8 ? ? ? ? 33 FF",
            "40 55 53 56 57 41 56 48 8B EC 48 81 EC ? ? ? ? 48 8B D9 E8 ? ? ? ? 45 33 F6",
            "48 83 EC ? 48 8B D9 E8 ? ? ? ? 33 F6",
            "40 55 53 56 57 41 56 48 8B EC 48 81 EC ? ? ? ? 48 8B D9",
        ]
    else:
        cands = [
            "E8 ? ? ? ? F3 44 0F 10 05 ? ? ? ? 48 8D 45 ? 48 89 44 24 ? 41 0F 28 D8",
            "E8 ? ? ? ? F3 44 0F 10 05 ? ? ? ? 48 8D 45 ? 48 89 44 24 ? 41 0F 28",
            "F3 44 0F 10 05 ? ? ? ? 48 8D 45 ? 48 89 44 24 ? 41 0F 28 D8",
            "E8 ? ? ? ? F3 44 0F 10 05 ? ? ? ? 48 8D 45 ? 48 89 44 24 ? 44 0F 28 D8",
            "E8 ? ? ? ? F3 44 0F 10 05 ? ? ? ? 48 8D 45 ? 48 89 44 24 ? 0F 28 D8",
        ]
    for p in cands:
        h = count(p)
        if h:
            print(f"  {len(h)} x {p}")
            for x in h[:3]:
                print(f"    0x{x:X} {dump(x)}")
