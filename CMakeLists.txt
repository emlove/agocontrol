cmake_minimum_required (VERSION 2.6)
project (agocontrol)


# The version number.
set (AGOCONTROL_VERSION 0.1)

# FreeBSD have some differences in building, mainly 
# that non-base libs/includes are located in /usr/local.
IF (CMAKE_SYSTEM_NAME MATCHES "FreeBSD")
	set (FREEBSD YES)
	include_directories("/usr/local/include")
	LINK_DIRECTORIES(/usr/local/lib)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "FreeBSD")

# some configurable values
IF (FREEBSD)
	set (BINDIR /usr/local/bin CACHE STRING "Directory to store Binaries")
	set (ETCDIR /usr/local/etc CACHE STRING "Directory for system-wide settings")
	set (LIBDIR /usr/lib CACHE STRING "Directory for libraries")
	set (CONFDIR ${ETCDIR}/agocontrol CACHE STRING "Directory for agocontrol settings")
	set (INCDIR /usr/local/include/agocontrol CACHE STRING "Directory for include files")
	set (DATADIR /usr/local/share/agocontrol CACHE STRING "Directory for static data")
	set (LOCALSTATEDIR /usr/local/var/agocontrol CACHE STRING "Directory for variable data")
	set (HTMLDIR ${DATADIR}/html CACHE STRING "Directory for rpc HTML files")
ELSE (FREEBSD)
	set (BINDIR /opt/agocontrol/bin CACHE STRING "Directory to store Binaries")
	set (ETCDIR /etc CACHE STRING "Directory for system-wide settings")
	set (LIBDIR /usr/lib CACHE STRING "Directory for libraries")
	set (CONFDIR ${ETCDIR}/opt/agocontrol CACHE STRING "Directory for agocontrol settings")
	set (INCDIR /usr/include/agocontrol CACHE STRING "Directory for include files")
	set (DATADIR /var/opt/agocontrol CACHE STRING "Directory for static data")
	set (LOCALSTATEDIR /var/opt/agocontrol CACHE STRING "Directory for variable data")
	set (HTMLDIR /opt/agocontrol/html CACHE STRING "Directory for rpc HTML files")
ENDIF (FREEBSD)

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

# JSONCpp is used globally (agoclient.h)
IF (FREEBSD)
	set (JSONCPP_ROOT_DIR "/usr/local/lib")
	set (JSONCPP_INCLUDE_DIR "/usr/local/include/jsoncpp")
ELSE (FREEBSD)
	set (JSONCPP_ROOT_DIR "/usr/lib")
	set (JSONCPP_INCLUDE_DIR "/usr/include/jsoncpp")
ENDIF (FREEBSD)

find_package (JsonCpp REQUIRED)
if (JSONCPP_FOUND)
	include_directories(${JSONCPP_INCLUDE_DIRS})
endif (JSONCPP_FOUND)

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

