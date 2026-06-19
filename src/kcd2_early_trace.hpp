#pragma once

#include <Windows.h>

#include <cstdio>

namespace kcd2
{
	inline void early_trace(const char *msg)
	{
		OutputDebugStringA("[KCD2ModLoader] ");
		OutputDebugStringA(msg);
		OutputDebugStringA("\n");

		char path[MAX_PATH]{};
		if (GetTempPathA(MAX_PATH, path) == 0)
		{
			return;
		}

		lstrcatA(path, "kcd2_modloader_trace.log");

		FILE *file = nullptr;
		if (fopen_s(&file, path, "a") != 0 || file == nullptr)
		{
			return;
		}

		fprintf(file, "%s\n", msg);
		fflush(file);
		fclose(file);
	}

	inline void early_trace_clear()
	{
		char path[MAX_PATH]{};
		if (GetTempPathA(MAX_PATH, path) == 0)
		{
			return;
		}

		lstrcatA(path, "kcd2_modloader_trace.log");
		DeleteFileA(path);
	}
} // namespace kcd2
