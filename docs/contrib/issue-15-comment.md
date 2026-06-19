# Issue #15 comment — diagnosis of the 1.5 early crash / empty log

> Paste into the issue thread. Trim as you like.

---

Dug into this on game build `release_1_5_1164953_841`. Root cause of the **empty,
0-byte `ReturnOfModding\LogOutput.log`** is that the crash happens *before* the logger
ever flushes a line.

**What's happening:** several byte-pattern signatures drifted in 1.5. In
`scan_addresses_and_set_ptr()`, a missed `scan()` returns a null address that is then
immediately dereferenced via `.get_call()` / `.offset().rip()`. That's an access
violation during very early init — before the first log write — so the log file gets
created but stays 0 bytes. (Consistent with the other report of empty logs + vanilla
launching fine.)

**Signatures that moved in 1.5:**
- `game_luaV_execute` — prologue changed
- `lua_custom_alloc` — `48 8D 88` → `48 8D 90 B8 00 00 00`
- `CGeomCacheRenderNodeVFTable` — old anchor gone; re-anchored to a direct `lea` form
- `CPhysicalEntityVFTable` — tail `88 4E 47` → `48 89 46 10`
- `CPhysicalEntity_ctor` — call-site bytes changed
- `PostInputEvent` — still being re-found (its block early-returns, so it currently
  aborts the rest of init — worth noting for anyone testing: the loader reaches D3D but
  the Lua/script hooks after it don't install until this one is fixed)

**Fixes that make this robust, not just patched:**
1. A `scan_to_vtable()` helper + null-guards so a stale signature **logs an error and
   bails** instead of AV-ing with no diagnostics.
2. Early tracing (`%TEMP%\kcd2_modloader_trace.log`, flushed per line) plus a traced
   hook wrapper, so the last line written names the hook that failed — turning a future
   patch break from a silent crash into a 5-minute "signature X is stale" fix.
3. Offline `tools/scan_patterns.py` to validate signatures against an installed
   `WHGame.dll` before shipping.

With the safe-scan changes the loader now boots on 1.5: reaches `DllMain`, enables
hooks, `LogOutput.log` grows past 0 bytes, and the D3D init hook fires. Happy to open a
PR with the signature updates + the fail-safe scanning once `PostInputEvent` is re-found
and init traces through to completion.
