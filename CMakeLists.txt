cmake_minimum_required (VERSION 2.6)
project (agocontrol)


# The version number.
set (AGOCONTROL_VERSION 0.1)


# some configurable values
set (BINDIR /opt/agocontrol/bin)
set (ETCDIR /etc)
set (LIBDIR /usr/lib)
set (CONFDIR ${ETCDIR}/opt/agocontrol)
set (INCDIR /usr/include/agocontrol)
set (DATADIR /var/opt/agocontrol)
set (LOCALSTATEDIR /var/opt/agocontrol)
set (HTMLDIR /opt/agocontrol/html)

# options what to build
OPTION(BUILD_AGOLUA "Build agolua" ON)


# configure a header file to pass some of the CMake settings
# to the source code
configure_file (
    "${PROJECT_SOURCE_DIR}/version.h.in"
    "${PROJECT_BINARY_DIR}/version.h"
    @ONLY
)
 

# add the binary tree to the search path for include files
# so that we will find version.h and other configured files
include_directories("${PROJECT_BINARY_DIR}")
include_directories("${PROJECT_BINARY_DIR}/shared")
include_directories("${PROJECT_SOURCE_DIR}/shared")


set (CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")
set (JSONCPP_ROOT_DIR "/usr/lib")
set (JSONCPP_INCLUDE_DIR "/usr/include/jsoncpp")

set (ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${LIBDIR}")
set (LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${LIBDIR}")
set (RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${BINDIR}")


# add sub directories
add_subdirectory (shared) 
add_subdirectory (core) 
#add_subdirectory (devices) 
add_subdirectory (conf) 
add_subdirectory (scripts)
