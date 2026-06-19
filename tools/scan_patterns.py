#!/usr/bin/env python3
"""Scan WHGame.dll for KCD2ModLoader patterns (same logic as kcd2_address.hpp)."""

from __future__ import annotations

import sys
from pathlib import Path


def parse_pattern(pattern_str: str) -> list[int | None]:
    pattern: list[int | None] = []
    i = 0
    while i < len(pattern_str):
        if pattern_str[i] == " ":
            i += 1
            continue
        token = pattern_str[i : i + 2]
        if token == "??":
            pattern.append(None)
            i += 2
            if i < len(pattern_str) and pattern_str[i] == " ":
                i += 1
            continue
        if token.startswith("?"):
            pattern.append(None)
            i += 1
            if i < len(pattern_str) and pattern_str[i] == " ":
                i += 1
            continue
        pattern.append(int(token, 16))
        i += 3 if i + 2 < len(pattern_str) and pattern_str[i + 2] == " " else 2
    return pattern


def scan(data: bytes, pattern_str: str) -> int | None:
    pattern = parse_pattern(pattern_str)
    size = len(data)
    psize = len(pattern)
    scan_size = (psize >> 1) + (psize & 1)
    for i in range(size - psize + 1):
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
            return i
    return None


PATTERNS = [
    ("game_lua_call", "E8 ? ? ? ? FF C3 3B DF 7E"),
    ("game_lua_checkstack", "E8 ? ? ? ? 85 C0 75 ? 48 8D 15 ? ? ? ? 48 8B CF E8 ? ? ? ? 80 7B"),
    ("game_luaV_execute", "48 8B C4 48 89 58 ? 89 50 ? 55 56 57 41 54 41 55 41 56 41 57 48 81 EC"),
    ("game index2adr", "85 D2 7F ? B8"),
    ("game luaH_new", "48 89 5C 24 ? 48 89 6C 24 ? 48 89 74 24 ? 57 48 83 EC ? 41 8B F0 8B DA 45 33 C0"),
    ("g_C3DEngine_UnRegisterEntityImpl_ptr", "E8 ? ? ? ? 49 8D 8E ? ? ? ? 48 8B D7 4C 8D 5C 24"),
    ("CXConsole_Ctor", "E8 ? ? ? ? 48 8B C8 EB 03 49 8B CF 48 8B 46 20 48 89 88 A8 00 00 00"),
    ("CentityVFTable", "48 8D 05 ? ? ? ? 48 89 01 4C 89 A1 A0 00 00 00"),
    ("CStatObjVFTable", "48 8D 05 ? ? ? ? 48 89 77 58 48 89 07"),
    ("CGeomCacheRenderNodeVFTable", "48 8B F9 4C 89 71 20"),
    ("CVegetations_Ctor", "E8 ? ? ? ? 48 8B D0 F2 0F 10 43"),
    ("CMergedMeshRenderNode_Ctor", "B9 E0 02 00 00 E8"),
    ("CBrush_VFTable", "48 8D 05 ? ? ? ? 83 A1 B0 00 00 00 F8"),
    ("CPhysicalEntityVFTable", "48 8D 05 ? ? ? ? 48 89 06 48 8D 05 ? ? ? ? 88 4E 47"),
    ("C3DEngine_VFTable", "48 8D 0D ? ? ? ? 48 89 0E 48 8D 4E 10"),
    ("cryengine_attachVariable", "E8 ? ? ? ? 4C 8D 0D ? ? ? ? 4C 8D 05 ? ? ? ? 48 8B CB"),
    ("LoadCommonData", "E8 ? ? ? ? F2 41 0F 10 46"),
    ("CPhysicalEntity_ctor", "E8 ? ? ? ? 33 D2 83 8B"),
    ("REGISTER_CVAR", "E8 ? ? ? ? 48 8B 0D ? ? ? ? 48 8D 1D ? ? ? ? 48 85 C9 74 ? 48 8B 01 4C 8D 05"),
    ("init_renderer", "E8 ? ? ? ? 48 83 3D ? ? ? ? ? 75 ? 48 8D 0D"),
    ("CryScriptSystem::Init", "E8 ? ? ? ? 84 C0 74 ? E8 ? ? ? ? 41 38 BE"),
    ("CryScriptSystem::Update", "48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC ? 48 8B 3D ? ? ? ? 48 8B F1 33 D2"),
]


def main() -> int:
    dll_path = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
    )
    data = dll_path.read_bytes()
    base = 0x180000000  # typical PE base; only used for display

    print(f"Scanning {dll_path} ({len(data)} bytes)\n")
    misses = []
    for name, pattern in PATTERNS:
        off = scan(data, pattern)
        if off is None:
            print(f"MISS  {name}")
            misses.append(name)
        else:
            print(f"OK    {name} @ file+0x{off:X} (VA ~0x{base + off:X})")

    print(f"\n{len(misses)} miss(es) out of {len(PATTERNS)}")
    return 1 if misses else 0


if __name__ == "__main__":
    raise SystemExit(main())
