cmake_minimum_required(VERSION 3.18)
project(WarRoomWasm)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Requires Emscripten toolchain via emcmake.
add_executable(sector_heatmap sector_heatmap.cpp)

set_target_properties(sector_heatmap PROPERTIES
    LINK_FLAGS "-s WASM=1 -s MODULARIZE=1 -s EXPORT_NAME=WarRoomModule -s ALLOW_MEMORY_GROWTH=1 -s EXPORTED_FUNCTIONS='[\"_main\"]'"
    SUFFIX ".js"
)
