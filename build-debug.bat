@echo off
REM ============================================================
REM  KCD2ModLoader DEBUG build script
REM  Config: Debug (no FINAL), separate build-debug folder.
REM  NOTE: The real C2712 fix lives in src/kcd2_init.cpp - the SEH
REM  __try in unregister_all_rendernode() was extracted into a helper
REM  so the range-for iterators no longer force object-unwinding in a
REM  __try function under Debug /Od. /RTC1 is also dropped here just to
REM  keep the debug build lean; it can be restored now that the source
REM  is fixed.
REM  Output -> build-debug\d3d12.dll (+ .pdb) with full debug info.
REM  Re-invokes itself so ALL output is captured to build_debug_output.log
REM ============================================================
if "%~1"=="_inner" goto :inner
cmd /c ""%~f0" _inner" > "%~dp0build_debug_output.log" 2>&1
echo.
echo Debug build finished. See build_debug_output.log for full output.
exit /b %errorlevel%

:inner
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
echo ============================================================
echo  KCD2ModLoader DEBUG build started: %DATE% %TIME%
echo  ROOT=%ROOT%
echo ============================================================

REM ---------- 1. Locate Visual Studio via vswhere ----------
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
  echo [FATAL] vswhere.exe not found at "%VSWHERE%".
  exit /b 101
)
echo [OK] Found vswhere.

set "VSILIST=%TEMP%\kcd2_vsinstall.txt"
"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath > "%VSILIST%" 2>nul
set "VSINSTALL="
for /f "usebackq delims=" %%i in ("%VSILIST%") do set "VSINSTALL=%%i"
if not defined VSINSTALL (
  echo [FATAL] No VS install with the C++ VC.Tools.x86.x64 component was found.
  exit /b 102
)
echo [OK] VS install: %VSINSTALL%

REM ---------- 2. Enter MSVC developer environment ----------
set "VSDEVCMD=%VSINSTALL%\Common7\Tools\VsDevCmd.bat"
if not exist "%VSDEVCMD%" (
  echo [FATAL] VsDevCmd.bat not found at "%VSDEVCMD%".
  exit /b 103
)
echo [INFO] Calling VsDevCmd.bat ...
call "%VSDEVCMD%" -arch=amd64 -host_arch=amd64
if errorlevel 1 (
  echo [FATAL] VsDevCmd.bat failed.
  exit /b 104
)
echo [OK] MSVC environment initialized.

REM ---------- 3. Configure (Debug, /RTC1 removed) ----------
cd /d "%ROOT%"
echo.
echo [STEP] Configuring CMake project - Debug, Ninja, no /RTC1 - into build-debug ...
cmake -D CMAKE_BUILD_TYPE=Debug -D "CMAKE_CXX_FLAGS_DEBUG=/Zi /Ob0 /Od" -D "CMAKE_C_FLAGS_DEBUG=/Zi /Ob0 /Od" -S. -Bbuild-debug -G Ninja
if errorlevel 1 (
  echo [FATAL] CMake configure failed.
  exit /b 110
)
echo [OK] Configure complete.

REM ---------- 4. Build ----------
echo.
echo [STEP] Building target KCD2ModLoader (Debug) ...
cmake --build ./build-debug --config Debug --target KCD2ModLoader --
if errorlevel 1 (
  echo [FATAL] Build failed.
  exit /b 111
)
echo [OK] Build complete.

REM ---------- 5. Rename output to d3d12.dll ----------
echo.
if exist "%ROOT%build-debug\d3d12_.dll" (
  copy /y "%ROOT%build-debug\d3d12_.dll" "%ROOT%build-debug\d3d12.dll" >nul
  if exist "%ROOT%build-debug\d3d12_.pdb" copy /y "%ROOT%build-debug\d3d12_.pdb" "%ROOT%build-debug\d3d12.pdb" >nul
  echo [OK] Produced build-debug\d3d12.dll
) else (
  echo [FATAL] Expected build-debug\d3d12_.dll was not produced.
  exit /b 112
)

echo.
echo --- Output artifacts ---
dir "%ROOT%build-debug\d3d12*.*"
echo.
echo --- SHA256 of d3d12.dll ---
certutil -hashfile "%ROOT%build-debug\d3d12.dll" SHA256

echo.
echo ============================================================
echo  RESULT: SUCCESS  -  build-debug\d3d12.dll is ready
echo ============================================================
exit /b 0
