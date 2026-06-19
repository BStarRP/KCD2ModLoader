# PR 1 — Fix Debug (`/Od`) build: C2712 in `unregister_all_rendernode`

**Branch suggestion:** `fix/debug-c2712-seh`
**Target:** `xiaoxiao921/KCD2ModLoader:master`
**Scope:** `src/kcd2_init.cpp` only. No behavior change.

---

## Title
Fix Debug build: C2712 "cannot use `__try` in functions that require object unwinding"

## Summary
The project only ever builds Release in CI (`RelWithDebInfo` + `FINAL=YES`), so a
Debug (`/Od`) build has been silently broken. Compiling the `Debug` config fails with:

```
src/kcd2_init.cpp(1719): error C2712: Cannot use __try in functions that require object unwinding
```

This makes it impossible to produce an unoptimized, fully-symbolized build for
debugging — exactly what you want when chasing an early-init crash.

## Root cause
`unregister_all_rendernode()` placed an SEH `__try`/`__except` **inside** a
range-`for` over `g_rendernodes` (`ankerl::unordered_dense::set<IRenderNode*>`):

```cpp
for (auto render_node : g_rendernodes)
{
    __try { g_hooking->get_original<hook_C3DEngine_UnRegisterEntityImpl>()(g_C3DEngine, render_node); }
    __except (EXCEPTION_EXECUTE_HANDLER) { continue; }
}
```

Two sources of objects-requiring-unwinding share the function with the `__try`:
1. the range-`for` iterators (`__begin`/`__end`) over the dense-set, and
2. the temporaries created by instantiating `get_original<...>()`.

Under `/Od` the compiler keeps those objects live, so the function "requires object
unwinding," which `__try` forbids → C2712. Release builds only because optimization
elides them.

## Fix
Move the SEH so its frame sees nothing but raw pointers. The hook call is pushed into
a leaf helper, and the `__try` wrapper calls only that:

```cpp
static void call_unregister_entity_impl(uintptr_t engine, IRenderNode *render_node)
{
    g_hooking->get_original<hook_C3DEngine_UnRegisterEntityImpl>()(engine, render_node);
}

// SEH helpers must not contain C++ objects that require unwinding (Debug /Od -> C2712).
static void unregister_one_rendernode(IRenderNode *render_node)
{
    __try { call_unregister_entity_impl(g_C3DEngine, render_node); }
    __except (EXCEPTION_EXECUTE_HANDLER) {}
}

void unregister_all_rendernode()
{
    for (auto render_node : g_rendernodes)
        unregister_one_rendernode(render_node);
}
```

`safe_render_node_type()` is also simplified to `return` directly from inside the
`__try` (removes its stack local), same intent.

## Why this is safe
- **Behavior is identical**: per-node "skip on exception and keep going" is preserved
  (the old `continue` is now the helper simply returning).
- **EH model unchanged** (`/EHsc`). Note: switching to `/EHa` would also silence C2712
  but is the wrong fix here — it makes `catch(...)` swallow access violations, which
  would mask the very crashes this loader is trying to survive. This PR deliberately
  avoids that.
- Compiles in **all** configs (Release `FINAL`, RelWithDebInfo, and now Debug `/Od`).

## Testing
- `cmake -D CMAKE_BUILD_TYPE=Debug -S. -Bbuild-debug -G Ninja` then
  `cmake --build ./build-debug --target KCD2ModLoader` → builds clean.
- Release/`FINAL` build unchanged and still green.

## Suggested commit message
```
fix: resolve C2712 in Debug build (SEH + object unwinding)

unregister_all_rendernode put an SEH __try inside a range-for over an
unordered_dense set and around get_original<>(), both of which introduce
objects requiring unwinding. Under /Od this triggers C2712 and breaks the
Debug config (CI only builds Release, so it went unnoticed).

Extract the hook call into call_unregister_entity_impl() and the __try into
unregister_one_rendernode(), so the SEH frame only sees raw pointers.
Behavior unchanged; builds in all configurations. EH model kept at /EHsc.
```
