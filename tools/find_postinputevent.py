#!/usr/bin/env python3
"""Find PostInputEvent replacement signature in WHGame.dll."""

from __future__ import annotations

import re
from pathlib import Path

from scan_patterns import parse_pattern, scan

DLL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
)
data = DLL.read_bytes()
BASE = 0x180000000

OLD = "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 7A"


def count_matches(pattern_str: str) -> list[int]:
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


def dump(off: int, before: int = 0, length: int = 64) -> str:
    chunk = data[off - before : off + length]
    return " ".join(f"{b:02X}" for b in chunk)


print(f"OLD PostInputEvent: {scan(data, OLD)}")
print()

# Partial anchors from old pattern head/tail
partials = [
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0",
    "48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81",
    "45 84 C0 75 ? 44 38 81",
    "44 38 81 ? ? ? ? 74 ? 83 7A",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9",
]
for p in partials:
    hits = count_matches(p)
    print(f"{len(hits):4d}  {p[:60]}...")
    for h in hits[:3]:
        print(f"      @0x{h:X} VA~0x{BASE + h:X}  {dump(h, 0, 48)}")

# Search for PostInputEvent string xrefs - string in binary
for needle in [b"PostInputEvent", b"postinput", b"InputEvent"]:
    idx = data.find(needle)
    print(f"\nString {needle!r}: {hex(idx) if idx >= 0 else 'not found'}")

# CryInput PostInputEvent often has specific prologue - try evolved variants
candidates = [
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 7B",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 79",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 39 7A",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 7B ?",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 39 81 ? ? ? ? 74 ? 83 7A",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 7B ? 00",
    "48 89 5C 24 ? 48 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 7A",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 0F B6 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 7A",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 41 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 7A",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 BB",
    "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 ? ? ? ? 74 ? 83 BF",
]
print("\nCandidate patterns:")
for p in candidates:
    hits = count_matches(p)
    if hits:
        print(f"  {len(hits)} hit(s): {p}")
        for h in hits:
            print(f"    0x{h:X}  {dump(h, 0, 56)}")
