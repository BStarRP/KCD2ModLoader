#!/usr/bin/env python3
"""Validate hook-registration scan patterns (match count) from kcd2_init.cpp."""

from __future__ import annotations

import re
from pathlib import Path

from scan_patterns import parse_pattern

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "kcd2_init.cpp"
DLL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
)
data = DLL.read_bytes()


def count(pattern_str: str) -> tuple[int, list[int]]:
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
    return len(hits), hits


text = SRC.read_text(encoding="utf-8")
# scan("...") and scan(\n "...")
patterns = re.findall(r'kcd2_address::scan\(\s*"([^"]+)"', text, re.DOTALL)
patterns += re.findall(
    r'scan_to_vtable\(\s*\n\s*"([^"]+)"',
    text,
    re.DOTALL,
)
named = [(m[0], m[1]) for m in re.finditer(
    r'static constexpr const char \*(\w+) =\s*\n\s*"([^"]+)"', text
)]
patterns += [pat for _, pat in named]

seen: set[str] = set()
problems = []
print(f"Scanning {len(patterns)} inline patterns from {SRC.name}\n")
for i, pat in enumerate(patterns):
    if pat in seen:
        continue
    seen.add(pat)
    n, hits = count(pat)
    status = "OK" if n == 1 else ("MISS" if n == 0 else f"MULTI({n})")
    print(f"{status:8s}  {pat[:72]}{'...' if len(pat) > 72 else ''}")
    if n != 1:
        problems.append((pat, n, hits[:5]))
        for h in hits[:3]:
            print(f"          @0x{h:X}")

for name, pat in named:
    n, hits = count(pat)
    status = "OK" if n == 1 else ("MISS" if n == 0 else f"MULTI({n})")
    print(f"{status:8s}  [{name}] {pat[:60]}...")
    if n != 1:
        problems.append((pat, n, hits[:5]))

print(f"\n{len(problems)} problem pattern(s)")
raise SystemExit(1 if problems else 0)
