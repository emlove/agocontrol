cmake_minimum_required (VERSION 2.6)

configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/command.lua.in"
    "${CMAKE_CURRENT_BINARY_DIR}/command.lua"
    @ONLY
)

if(FREEBSD)
	set(LUA lua-5.2)
else(FREEBSD)
	set(LUA lua5.2)
endif(FREEBSD)

file (GLOB_RECURSE AGOLUA_SOURCE_FILES *.cpp)
set (LUA_LIBRARIES
    agoclient
	 boost_filesystem
	 boost_system
	 ${LUA}
)

# add the executable
add_executable (agolua ${AGOLUA_SOURCE_FILES})
target_link_libraries (agolua ${LUA_LIBRARIES})

install (TARGETS agolua RUNTIME DESTINATION ${BINDIR})
