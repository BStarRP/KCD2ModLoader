#!/usr/bin/env python3
"""Validate hook patterns registered after PostInputEvent in kcd2_init."""

from __future__ import annotations

from pathlib import Path

from scan_patterns import parse_pattern

DLL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
)
data = DLL.read_bytes()

# Patterns from kcd2_init hook blocks (post-PostInputEvent through CryScriptSystem)
HOOKS = [
    ("PostInputEvent", "48 89 5C 24 ? 57 48 83 EC ? 48 8B DA 48 8B F9 45 84 C0 75 ? 44 38 81 D8 00 00 00 0F 84 ? ? ? ? 83 7A 10 FF"),
    ("CLog_LogV", "40 53 56 57 41 54 41 55 41 56 41 57 B8 ? ? ? ? E8 ? ? ? ? 48 2B E0 0F 29 B4 24 ? ? ? ? 48 8B 05"),
    ("XmlParserImp_ParseFile", "40 53 56 57 41 56 41 57 48 81 EC ? ? ? ? 48 8B 05 ? ? ? ? 48 33 C4 48 89 84 24 ? ? ? ? 41 8A D9"),
    ("XML_Parse", "E8 ? ? ? ? 48 8D 4D ? 83 F8"),
    ("CCryFile_Open", "E8 ? ? ? ? B3 ? 84 C0 75"),
    ("CCryPak_ctor", "E8 ? ? ? ? 48 8B F8 8A 83"),
    ("wh_db_table_patched", "E8 ? ? ? ? E9 ? ? ? ? 8B 52 ? 44 8B 79"),
    ("wh_db_table_patch_find_line", "E8 ? ? ? ? 83 F8 ? 75 ? 48 8B CB E8 ? ? ? ? 45 33 C9"),
    ("XmlParserReadOnly_Read_caller", "48 89 5C 24 ? 48 89 6C 24 ? 48 89 74 24 ? 57 48 83 EC ? 41 0F B6 E8 48 8B FA 48 8B F1 E8 ? ? ? ? 48 8B 88"),
    ("CXConsole_RegisterVar", "E8 ? ? ? ? 48 8B C3 48 8B 5C 24 ? 48 8B 6C 24 ? 0F 28 74 24"),
    ("CEntitySystem_CEntitySystem", "E8 ? ? ? ? 48 8B D8 48 8B D7 48 89 1D"),
    ("CEntity_ctor", "E8 ? ? ? ? 48 8B D8 EB ? 48 8B DF 41 8B C7"),
    ("CBrush_ctor", "E8 ? ? ? ? 48 8B D8 4C 8B 8C 24"),
    ("CEntity_SetWorldTM", "48 89 5C 24 ? 48 89 74 24 ? 48 89 7C 24 ? 55 41 54 41 55 41 56 41 57 48 8B EC 48 83 EC ? 48 8B F9 E8"),
    ("StepDataSBrush", "E8 ? ? ? ? 48 8B D8 48 85 C0 74 ? 48 8B 08"),
    ("CTerrain_Load", "E8 ? ? ? ? 48 8B D8 48 85 DB 74 ? 48 8B 03"),
    ("CBrush_SetStatObj", "E8 ? ? ? ? 8B 57 ? 49 8B CF"),
    ("CStatObj_ctor", "E8 ? ? ? ? 48 8B F8 EB ? 33 FF 4C 89 BF 60 01 00 00"),
    ("CGeomCacheRenderNode_ctor", "E8 ? ? ? ? E9 ? ? ? ? B9 ? ? ? ? E8 ? ? ? ? 48 8B C8 33 C0 48 85 C9 0F 84 ? ? ? ? E8 ? ? ? ? EB"),
    ("C_PlayerStateMovement_ctor", "48 89 5C 24 ? 48 89 74 24 ? 48 89 7C 24 ? 55 41 54 41 55 41 56 41 57 48 8B EC 48 83 EC ? 48 8B F9 E8"),
    ("C_Player_ctor", "40 55 53 56 57 41 56 48 8B EC 48 81 EC ? ? ? ? 48 8B D9 E8 ? ? ? ? 48 8B F0"),
    ("C3DEngine_ctor", "E8 ? ? ? ? 48 8B 5C 24 ? 48 89 47 ? B0"),
    ("UnProjectFromScreen", "E8 ? ? ? ? F3 44 0F 10 05 ? ? ? ? 48 8D 45 ? 48 8D 4D 14"),
    ("CD3D9Renderer_ProjectToScreen", "48 83 EC ? 48 8B 0D ? ? ? ? 0F 29 74 24 ? 0F 28 F2 0F 29 7C 24"),
    ("RayWorldIntersection", "E8 ? ? ? ? 48 FF 03 48 81 C4"),
    ("CryScriptSystem_Init", "E8 ? ? ? ? 84 C0 74 ? E8 ? ? ? ? 41 38 BE"),
    ("CryScriptSystem_Update", "48 89 5C 24 ? 48 89 74 24 ? 57 48 83 EC ? 48 8B 3D ? ? ? ? 48 8B F1 33 D2"),
    ("CryScriptSystem_ExecuteBuffer", "48 8B C4 48 89 58 ? 48 89 68 ? 48 89 70 ? 48 89 78 ? 41 56 48 83 EC ? 48 8B F9 48 89 50"),
]


def count(pattern_str: str) -> int:
    pattern = parse_pattern(pattern_str)
    psize = len(pattern)
    scan_size = (psize >> 1) + (psize & 1)
    hits = 0
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
            hits += 1
    return hits


def main() -> int:
    bad = []
    for name, pat in HOOKS:
        n = count(pat)
        status = "OK" if n == 1 else ("MISS" if n == 0 else f"MULTI({n})")
        print(f"{status:10s} {name}")
        if n != 1:
            bad.append((name, n))
    print(f"\n{len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
