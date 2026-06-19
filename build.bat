@echo off
REM ============================================================
REM  KCD2ModLoader self-contained build script
REM  Re-invokes itself so ALL output is captured to build_output.log
REM ============================================================
if "%~1"=="_inner" goto :inner
cmd /c ""%~f0" _inner" > "%~dp0build_output.log" 2>&1
echo.
echo Build finished. See build_output.log for full output.
exit /b %errorlevel%

:inner
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
echo ============================================================
echo  KCD2ModLoader build started: %DATE% %TIME%
echo  ROOT=%ROOT%
echo ============================================================

REM ---------- 1. Locate Visual Studio via vswhere ----------
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
  echo [FATAL] vswhere.exe not found at "%VSWHERE%".
  echo         Visual Studio 2022 with the C++ workload does not appear to be installed.
  exit /b 101
)
echo [OK] Found vswhere.

set "VSILIST=%TEMP%\kcd2_vsinstall.txt"
"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath > "%VSILIST%" 2>nul
set "VSINSTALL="
for /f "usebackq delims=" %%i in ("%VSILIST%") do set "VSINSTALL=%%i"
if not defined VSINSTALL (
  echo [FATAL] No VS install with the C++ VC.Tools.x86.x64 component was found.
  echo         Install "Desktop development with C++" in the VS Installer.
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

REM ---------- 3. Verify toolchain ----------
echo.
echo --- Toolchain check ---
where cl
where cmake
if errorlevel 1 (
  echo [FATAL] cmake not found in PATH. Install the C++ CMake tools VS component.
  exit /b 105
)
cmake --version
where ninja
if errorlevel 1 (
  echo [FATAL] ninja not found in PATH. Install the C++ CMake tools VS component.
  exit /b 106
)
ninja --version
where git
if errorlevel 1 (
  echo [FATAL] git not found in PATH. Git is required for CMake FetchContent dependencies.
  exit /b 107
)
git --version
echo -----------------------

REM ---------- 4. Configure ----------
cd /d "%ROOT%"
echo.
echo [STEP] Configuring CMake project - RelWithDebInfo, FINAL=YES, Ninja ...
cmake -D CMAKE_BUILD_TYPE=RelWithDebInfo -D FINAL=YES -S. -Bbuild -G Ninja
if errorlevel 1 (
  echo [FATAL] CMake configure failed.
  exit /b 110
)
echo [OK] Configure complete.

REM ---------- 5. Build ----------
echo.
echo [STEP] Building target KCD2ModLoader ...
cmake --build ./build --config RelWithDebInfo --target KCD2ModLoader --
if errorlevel 1 (
  echo [FATAL] Build failed.
  exit /b 111
)
echo [OK] Build complete.

REM ---------- 6. Rename output to d3d12.dll ----------
echo.
if exist "%ROOT%build\d3d12_.dll" (
  copy /y "%ROOT%build\d3d12_.dll" "%ROOT%build\d3d12.dll" >nul
  if exist "%ROOT%build\d3d12_.pdb" copy /y "%ROOT%build\d3d12_.pdb" "%ROOT%build\d3d12.pdb" >nul
  echo [OK] Produced build\d3d12.dll
) else (
  echo [FATAL] Expected build\d3d12_.dll was not produced.
  exit /b 112
)

echo.
echo --- Output artifacts ---
dir "%ROOT%build\d3d12*.*"
echo.
echo --- SHA256 of d3d12.dll ---
certutil -hashfile "%ROOT%build\d3d12.dll" SHA256

echo.
echo ============================================================
echo  RESULT: SUCCESS  -  build\d3d12.dll is ready
echo ============================================================
exit /b 0
