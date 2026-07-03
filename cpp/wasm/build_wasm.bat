@echo off
REM Build the C++ WebAssembly module using Emscripten.
REM Requires emcmake and emcc to be available in your PATH.
cd /d "%~dp0"
necho Running emcmake to configure the build...
emcmake cmake -S . -B build
echo Building WebAssembly module...
cmake --build build --config Release
echo Copying generated module to web directory...
if exist build\sector_heatmap.js copy /Y build\sector_heatmap.js ..\web\sector_heatmap.js
if exist build\sector_heatmap.wasm copy /Y build\sector_heatmap.wasm ..\web\sector_heatmap.wasm
echo Build complete. Open web\index.html in a browser or via a local static server.
pause
