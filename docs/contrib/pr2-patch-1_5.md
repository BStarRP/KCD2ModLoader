# PR 2 — Game patch 1.5 signature updates + fail-safe scanning  (DRAFT — not ready to submit)

**Branch suggestion:** `fix/patch-1.5-signatures`
**Target:** `xiaoxiao921/KCD2ModLoader:master`
**Status:** ⚠️ Hold until init reaches `kcd2_init: complete` on 1.5 — see "Open item".

---

## Title
Update signatures for game patch 1.5 + fail-safe vtable scanning

## Summary
On game patch `1.5` the loader crashed during early init and produced an **empty,
0-byte `ReturnOfModding\LogOutput.log`** (see issue #15). Several byte-pattern
signatures drifted with the 1.5 binary, and a failed scan was dereferenced before
the logger could flush — so the process AV'd with no diagnostics.

This change (a) hardens scanning so a stale signature logs an error instead of
crashing, (b) updates the signatures that moved in 1.5, and (c) adds lightweight
early tracing to pinpoint which hook fails on a future patch.

## Root cause of the silent crash
`scan_addresses_and_set_ptr()` did things like
`kcd2_address::scan(pattern).offset(n).rip().as<void**>()`. When `scan()` missed, it
returned a null/0 address and `.get_call()` / `.rip()` dereferenced it — an access
violation **before** any log line was written, hence the 0-byte log.

## Changes

### 1. Fail-safe vtable resolution
New `scan_to_vtable(pattern, offset, debug_name)` helper: checks the scan hit,
resolves the RIP-relative target, checks that too, and returns `nullptr` with a
`LOG(ERROR) << "Missed " << debug_name` on failure instead of AV-ing. Applied to
`CentityVFTable`, `CStatObjVFTable`, `CGeomCacheRenderNodeVFTable`, `CBrush_VFTable`,
`CPhysicalEntityVFTable`, `C3DEngine_VFTable`.

Ctor-derived vtables (`CXConsoleVFTable`, `CVegetationsVFTable`,
`CMergedMeshRenderNode_VFTable`) are now guarded with `ctor ? ...rip() : nullptr`, and
the consumers that dereference these tables (`CPhysicalEntityVFTable[0]`,
`CGeomCacheRenderNodeVFTable[0]`) get explicit null checks that `LOG(ERROR)` and bail.

### 2. Updated 1.5 signatures

| Symbol | Change |
| --- | --- |
| `game_luaV_execute` | prologue rewritten: `48 8B C4 48 89 58 08 48 89 70 10 48 89 78 18 55 41 54 41 55 41 56 41 57 48 81 EC` |
| `lua_custom_alloc` | tail `48 8D 88` → `48 8D 90 B8 00 00 00` |
| `CGeomCacheRenderNodeVFTable` | re-anchored to a direct `lea` form: `48 8D 05 ? ? ? ? 4C 89 71 18 4C 89 71 20 4C 89 71 28` (off 3) |
| `CPhysicalEntityVFTable` | tail `... 88 4E 47` → `... 48 89 46 10` |
| `CPhysicalEntity_ctor` (call-site) | `E8 ? ? ? ? 33 D2 83 8B` → `E8 ? ? ? ? 8B 83 ? ? ? ? 33 D2 83 8B` |

### 3. Early tracing for future patch breaks
- New `src/kcd2_early_trace.hpp`: `kcd2::early_trace()` writes to
  `%TEMP%\kcd2_modloader_trace.log` and `OutputDebugString`, flushing each line so a
  hard crash still leaves a breadcrumb. `early_trace_clear()` resets it on attach.
- New `add_traced_hook<detour>(name, target)` wraps `detour_hook_helper::add<>` with an
  `early_trace(name)` first; all hook registrations in `kcd2_init()` now go through it,
  and `DllMain` is instrumented. The last trace line = the hook that failed.
- `tools/scan_patterns.py`, `tools/scan_all_init_patterns.py`: offline validation of
  signatures against an installed `WHGame.dll`.

## Verification so far
Deployed the Debug DLL next to `KingdomCome.exe` on 1.5:
- reaches `DllMain` and enables hooks,
- `LogOutput.log` is 1986 bytes (was 0),
- `Initializing_Direct3D` hook fires; renderer init completes (`made it`).

## ⚠️ Open item (why this is still a draft)
`PostInputEvent` is a **6th** stale signature. Its block early-`return`s on miss:

```cpp
if (!ptr) { LOG(ERROR) << "Failed to find PostInputEvent"; return; }
```

So init currently **aborts at the 6th hook block** and every later hook — including
all the `CryScriptSystem` / Lua hooks — is skipped. The loader looks alive but is not
fully hooked on 1.5.

Before submitting:
1. Re-find the `PostInputEvent` signature in the 1.5 `WHGame.dll` (validate it matches
   exactly once with `scan_patterns.py`).
2. Have the scan-failure path log the **failed pattern name** so future drift is a named
   warning, not a silent dead hook / abort.
3. Rebuild, relaunch, and confirm `%TEMP%\kcd2_modloader_trace.log` reaches
   `kcd2_init: complete`. If it stops earlier, fix that pattern and repeat — there may be
   more drift hidden behind the early return.

Only once the trace reaches completion is the 1.5 pattern set actually done and this PR
ready.

## Suggested commit message (once complete)
```
fix: update signatures for game patch 1.5 + fail-safe scanning

Harden scan_addresses_and_set_ptr so a missed signature logs an error
instead of dereferencing null (the cause of the empty 0-byte LogOutput.log
on 1.5). Update the signatures that drifted in 1.5 (game_luaV_execute,
lua_custom_alloc, CGeomCacheRenderNodeVFTable, CPhysicalEntityVFTable,
CPhysicalEntity_ctor, PostInputEvent). Add kcd2_early_trace + add_traced_hook
so the failing hook on a future patch is identifiable from a flushed trace log.
```
