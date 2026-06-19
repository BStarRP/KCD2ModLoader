#pragma once

#include <Windows.h>

namespace big
{
	struct dll_proxy
	{
		static void init();

		// Real Microsoft D3D12.dll from System32 — not the game-folder proxy.
		static HMODULE load_system_d3d12();
	};
} // namespace big
