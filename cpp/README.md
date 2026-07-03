# C++ Integration Scaffolding

This workspace includes a C++/WebAssembly scaffold for high-impact frontend visualization and data-heavy processing.

## Structure

- `cpp/wasm/sector_heatmap.cpp`: Emscripten-compatible C++ module for safe heatmap computation and trade ticket generation.
- `cpp/wasm/CMakeLists.txt`: example CMake file for building the WebAssembly module with `emcmake`.

## Build Instructions

1. Install Emscripten: https://emscripten.org/docs/getting_started/downloads.html
2. Activate the Emscripten environment.
3. From the root folder, run:

```bash
cd cpp/wasm
emcmake cmake .
cmake --build .
```

4. The build will produce `sector_heatmap.js` and `sector_heatmap.wasm`.

## Usage

The generated module can be loaded in a browser and used to render award-style chart components with safe numeric handling.

## Notes

- The C++ code includes defensive checks for NaN/Inf and avoids unsafe memory operations.
- This scaffold is designed for a Wall Street-style analytics dashboard that can be embedded in a modern website.
