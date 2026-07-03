# WarRoom WASM Build

This folder contains the C++/WebAssembly scaffold for the sector regime heatmap.

## Build Instructions

1. Install Emscripten and ensure `emcmake` and `emcc` are on your `PATH`.
2. Open a terminal in this folder.
3. Run `build_wasm.bat` on Windows.
4. The generated `sector_heatmap.js` and `sector_heatmap.wasm` files will be copied to `../web/`.

## Notes

- The placeholder `web/sector_heatmap.js` is intentionally lightweight so the site falls back gracefully.
- The C++ module exports `build_sector_heatmap(raw_values)` and `build_trade_ticket(tickers, weights, portfolioValue)`.
- Use `web/index.html` with a local static server or file server for best compatibility.
