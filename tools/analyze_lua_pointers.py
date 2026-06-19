#!/usr/bin/env python3
"""Resolve and disassemble KCD2ModLoader Lua interop scan targets in WHGame.dll."""

from __future__ import annotations

import struct
from pathlib import Path

from scan_patterns import parse_pattern, scan

DLL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
)
data = DLL.read_bytes()
IMAGE_BASE = 0x180000000  # typical PE64; file offset == RVA for .text in many builds


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


def get_call(e8_off: int) -> int:
    rel = struct.unpack_from("<i", data, e8_off + 1)[0]
    return e8_off + 5 + rel


def disasm(off: int, n: int = 32) -> str:
    chunk = data[off : off + n]
    return " ".join(f"{b:02X}" for b in chunk)


def u32(off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


# Patterns from scan_addresses_and_set_ptr (E8 patterns resolved via get_call)
LUA_SCANS = [
    ("game_lua_call", "E8 ? ? ? ? FF C3 3B DF 7E", True),
    ("game_lua_checkstack", "E8 ? ? ? ? 85 C0 75 ? 48 8D 15 ? ? ? ? 48 8B CF E8 ? ? ? ? 80 7B", True),
    ("game_lua_concat", "E8 ? ? ? ? 2B DF", True),
    ("game_lua_createtable", "E8 ? ? ? ? 48 8B 5F ? 48 8B CF 48 2B 5F", True),
    ("game_lua_error", "E8 ? ? ? ? 41 83 C8 ? 33 D2", True),
    ("game_lua_gc", "E8 ? ? ? ? 41 83 3C 9E", True),
    ("game_lua_getfenv", "E8 ? ? ? ? 41 8B C3 48 83 C4", True),
    ("game_lua_getfield", "E8 ? ? ? ? 44 8D 7D", True),
    ("game_lua_getmetatable", "E8 ? ? ? ? 85 C0 75 ? 33 D2 44 8D 40", True),
    ("game_lua_gettable", "E8 ? ? ? ? 41 83 CB", True),
    ("game_lua_insert", "E8 ? ? ? ? 8B 56 ? 44 8B CF", True),
    ("game_lua_pcall", "E8 ? ? ? ? 48 8B 4E ? 8B D7 8B D8", True),
    ("game_luaV_execute", "48 8B C4 48 89 58 08 48 89 70 10 48 89 78 18 55 41 54 41 55 41 56 41 57 48 81 EC", False),
    ("game_lua_load", "E8 ? ? ? ? 48 83 CE ? 85 C0", True),
    ("game_lua_setmetatable", "40 53 48 83 EC ? 48 8B DA E8 ? ? ? ? 48 8B D3 E8 ? ? ? ? 48 8B 0D", False),
    ("lua_custom_alloc", "E8 ? ? ? ? 33 FF 48 8B D8 48 85 C0 0F 84 ? ? ? ? 48 8D 90 B8 00 00 00", True),
    ("game_pushref", "E8 ? ? ? ? 48 8B CB E8 ? ? ? ? 8D 4E ? 8D 56", True),
    ("game_index2adr", "85 D2 7F ? B8", False),
    ("game_luaH_new", "48 89 5C 24 ? 48 89 6C 24 ? 48 89 74 24 ? 57 48 83 EC ? 41 8B F0 8B DA 45 33 C0", False),
]

CRASH_RVA = 0x278EA0A


def main() -> None:
    print(f"WHGame.dll size: {len(data):#x}\n")

    for name, pat, is_call in LUA_SCANS:
        hits = count_all(pat)
        if not hits:
            print(f"{name}: MISS")
            continue
        if is_call:
            targets = [get_call(h) for h in hits]
        else:
            targets = hits
        print(f"{name}: {len(hits)} hit(s)")
        for i, (h, t) in enumerate(zip(hits, targets)):
            print(f"  [{i}] pattern@{t:#x} call_site@{h:#x}  prologue: {disasm(t, 24)}")
        if len(hits) == 1:
            print(f"  => resolved {name} @ {targets[0]:#x}")

    print(f"\n=== Crash site WHGame+{CRASH_RVA:#x} (file {CRASH_RVA:#x}) ===")
    print(disasm(CRASH_RVA, 48))

    # Deep dive: both game_lua_gettable call targets
    print("\n=== game_lua_gettable candidates ===")
    pat = "E8 ? ? ? ? 41 83 CB"
    for h in count_all(pat):
        t = get_call(h)
        ctx_before = disasm(h - 16, 16)
        ctx_after = disasm(h + 5, 16)
        print(f"call@{h:#x} -> target@{t:#x}")
        print(f"  before: {ctx_before}")
        print(f"  after:  {ctx_after}")
        print(f"  target: {disasm(t, 48)}")

    # lua_custom_alloc candidates
    print("\n=== lua_custom_alloc candidates ===")
    pat = "E8 ? ? ? ? 33 FF 48 8B D8 48 85 C0 0F 84 ? ? ? ? 48 8D 90 B8 00 00 00"
    for h in count_all(pat):
        t = get_call(h)
        print(f"call@{h:#x} -> target@{t:#x}  {disasm(t, 32)}")

    # game_luaV_execute candidates
    print("\n=== game_luaV_execute candidates ===")
    pat = "48 8B C4 48 89 58 08 48 89 70 10 48 89 78 18 55 41 54 41 55 41 56 41 57 48 81 EC"
    for h in count_all(pat):
        print(f"@{h:#x}  {disasm(h, 32)}")


if __name__ == "__main__":
    main()
