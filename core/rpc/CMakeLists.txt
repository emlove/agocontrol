cmake_minimum_required (VERSION 2.6)

file (GLOB_RECURSE AGORPC_SOURCE_FILES *.cpp)

set (RPC_LIBRARIES
    agoclient
    dl
    pthread
)

include_directories(
    /usr/include/jsoncpp
)

# add the executable
#add_executable (agorpc ${AGORPC_SOURCE_FILES})
add_executable (agorpc agorpc.cpp mongoose.c)
target_link_libraries (agorpc ${RPC_LIBRARIES})

add_executable (get_table_lang.cgi get_table_lang.cpp)

# configure a header file to pass some of the CMake settings
# to the source code
configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/activate.cgi.in"
    "${CMAKE_CURRENT_SOURCE_DIR}/activate.cgi"
    @ONLY
)
