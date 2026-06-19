#!/usr/bin/env python3
"""Scan every pattern used in scan_addresses_and_set_ptr."""

from __future__ import annotations

from pathlib import Path

from scan_patterns import scan

DLL = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Bin\Win64MasterMasterSteamPGO\WHGame.dll"
)
data = DLL.read_bytes()

PATTERNS = [
    ("game_lua_call", "E8 ? ? ? ? FF C3 3B DF 7E", "get_call"),
    ("game_lua_checkstack", "E8 ? ? ? ? 85 C0 75 ? 48 8D 15 ? ? ? ? 48 8B CF E8 ? ? ? ? 80 7B", "get_call"),
    ("game_lua_concat", "E8 ? ? ? ? 2B DF", "get_call"),
    ("game_lua_createtable", "E8 ? ? ? ? 48 8B 5F ? 48 8B CF 48 2B 5F", "get_call"),
    ("game_lua_error", "E8 ? ? ? ? 41 83 C8 ? 33 D2", "get_call"),
    ("game_lua_gc", "E8 ? ? ? ? 41 83 3C 9E", "get_call"),
    ("game_lua_getfenv", "E8 ? ? ? ? 41 8B C3 48 83 C4", "get_call"),
    ("game_lua_getfield", "E8 ? ? ? ? 44 8D 7D", "get_call"),
    ("game_lua_getmetatable", "E8 ? ? ? ? 85 C0 75 ? 33 D2 44 8D 40", "get_call"),
    ("game_lua_gettable", "E8 ? ? ? ? 41 83 CB", "get_call"),
    ("game_lua_insert", "E8 ? ? ? ? 8B 56 ? 44 8B CF", "get_call"),
    ("game_lua_pcall", "E8 ? ? ? ? 48 8B 4E ? 8B D7 8B D8", "get_call"),
    ("game_luaV_execute", "48 8B C4 48 89 58 08 48 89 70 10 48 89 78 18 55 41 54 41 55 41 56 41 57 48 81 EC", "direct"),
    ("game_lua_load", "E8 ? ? ? ? 48 83 CE ? 85 C0", "get_call"),
    ("CScriptableBase_Init_func", "E8 ? ? ? ? 48 8B CB E8 ? ? ? ? 39 3D", "get_call"),
    ("game_lua_setmetatable", "40 53 48 83 EC ? 48 8B DA E8 ? ? ? ? 48 8B D3 E8 ? ? ? ? 48 8B 0D", "direct"),
    ("lua_custom_alloc", "E8 ? ? ? ? 33 FF 48 8B D8 48 85 C0 0F 84 ? ? ? ? 48 8D 88", "get_call"),
    ("game_pushref", "E8 ? ? ? ? 48 8B CB E8 ? ? ? ? 8D 4E ? 8D 56", "get_call"),
    ("game index2adr", "85 D2 7F ? B8", "direct"),
    ("game luaH_new", "48 89 5C 24 ? 48 89 6C 24 ? 48 89 74 24 ? 57 48 83 EC ? 41 8B F0 8B DA 45 33 C0", "direct"),
    ("g_C3DEngine_UnRegisterEntityImpl_ptr", "E8 ? ? ? ? 49 8D 8E ? ? ? ? 48 8B D7 4C 8D 5C 24", "get_call"),
    ("CXConsole_Ctor", "E8 ? ? ? ? 48 8B C8 EB 03 49 8B CF 48 8B 46 20 48 89 88 A8 00 00 00", "get_call"),
    ("CentityVFTable", "48 8D 05 ? ? ? ? 48 89 01 4C 89 A1 A0 00 00 00", "vtable+3"),
    ("CStatObjVFTable", "48 8D 05 ? ? ? ? 48 89 77 58 48 89 07", "vtable+3"),
    ("CGeomCacheRenderNodeVFTable", "48 8D 05 ? ? ? ? 4C 89 71 18 4C 89 71 20 4C 89 71 28", "vtable+3"),
    ("CVegetations_Ctor", "E8 ? ? ? ? 48 8B D0 F2 0F 10 43", "get_call"),
    ("CMergedMeshRenderNode_Ctor", "B9 E0 02 00 00 E8", "offset18_get_call"),
    ("CBrush_VFTable", "48 8D 05 ? ? ? ? 83 A1 B0 00 00 00 F8", "vtable+3"),
    ("CPhysicalEntityVFTable", "48 8D 05 ? ? ? ? 48 89 06 48 8D 05 ? ? ? ? 48 89 46 10", "vtable+3"),
    ("C3DEngine_VFTable", "48 8D 0D ? ? ? ? 48 89 0E 48 8D 4E 10", "vtable+3"),
]


def rip(off: int, rel_off: int = 0) -> int:
    addr = off + rel_off
    rel = int.from_bytes(data[addr + 4 : addr + 8], "little", signed=True)
    return addr + 4 + rel


def main() -> int:
    misses = []
    for name, pattern, kind in PATTERNS:
        off = scan(data, pattern)
        if off is None:
            print(f"MISS  {name}")
            misses.append(name)
            continue
        try:
            if kind == "get_call":
                resolved = rip(off, 1)
            elif kind == "vtable+3":
                resolved = rip(off, 3)
            elif kind == "offset18_get_call":
                resolved = rip(off + 0x18, 1)
            else:
                resolved = off
            print(f"OK    {name} @ 0x{off:X} -> 0x{resolved:X}")
        except Exception as exc:
            print(f"FAIL  {name} @ 0x{off:X} ({exc})")
            misses.append(name)

    print(f"\n{len(misses)} problem(s)")
    return 1 if misses else 0


if __name__ == "__main__":
    raise SystemExit(main())
