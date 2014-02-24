cmake_minimum_required (VERSION 2.6)

# configure a header file to pass some of the CMake settings
# to the source code
configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/agocontrol-init-script.sh.in"
    "${CMAKE_CURRENT_BINARY_DIR}/agocontrol-init-script.sh"
    @ONLY
)

install (FILES agodrain.py myavahi.py agoctrl.sh DESTINATION ${BINDIR})

add_subdirectory (resolver)
add_subdirectory (rpc)
add_subdirectory (messagesend)
add_subdirectory (timer)
add_subdirectory (scenario)
add_subdirectory (event)
add_subdirectory (datalogger)

# options what to build
OPTION(BUILD_AGOLUA "Build agolua" ON)
if (BUILD_AGOLUA)
  add_subdirectory (lua)
endif()

add_subdirectory (security)
