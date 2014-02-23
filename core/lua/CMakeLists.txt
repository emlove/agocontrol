cmake_minimum_required (VERSION 2.6)

configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/command.lua.in"
    "${CMAKE_CURRENT_SOURCE_DIR}/command.lua"
    @ONLY
)


file (GLOB_RECURSE AGOLUA_SOURCE_FILES *.cpp)
set (LUA_LIBRARIES
    agoclient
    lua5.2
)

# add the executable
add_executable (agolua ${AGOLUA_SOURCE_FILES})
target_link_libraries (agolua ${LUA_LIBRARIES})

