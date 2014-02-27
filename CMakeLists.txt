cmake_minimum_required (VERSION 2.6)
project (agocontrol)


# The version number.
set (AGOCONTROL_VERSION 0.1)


# some configurable values
set (BINDIR /opt/agocontrol/bin CACHE STRING "Directory to store Binaries")
set (ETCDIR /etc CACHE STRING "Directory for system-wide settings")
set (LIBDIR /usr/lib CACHE STRING "Directory for libraries")
set (CONFDIR ${ETCDIR}/opt/agocontrol CACHE STRING "Directory for agocontrol settings")
set (INCDIR /usr/include/agocontrol CACHE STRING "Directory for include files")
set (DATADIR /var/opt/agocontrol CACHE STRING "Directory for variable data")
set (LOCALSTATEDIR /var/opt/agocontrol CACHE STRING "Directory for state info")
set (HTMLDIR /opt/agocontrol/html CACHE STRING "Directory for rpc HTML files")


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
OPTION(BUILD_SHARED "Build the agoclient shared library" ON)
if (BUILD_SHARED)
  add_subdirectory (shared) 
endif()

OPTION(BUILD_CORE "Build the CORE" ON)
if (BUILD_CORE)
  add_subdirectory (core) 
  install (PROGRAMS gateways/agomeloware.py DESTINATION ${BINDIR})
  install (FILES data/inventory.sql data/datalogger.sql DESTINATION ${DATADIR})
endif()

OPTION(BUILD_DEVICES "Build the devices" ON)
if (BUILD_DEVICES)
  add_subdirectory (devices) 
endif()

OPTION(BUILD_CONF "Build the configs" ON)
if (BUILD_CONF)
  add_subdirectory (conf) 
endif()

OPTION(BUILD_SCRIPTS "Build the scripts" ON)
if (BUILD_SCRIPTS)
  add_subdirectory (scripts)
endif()

