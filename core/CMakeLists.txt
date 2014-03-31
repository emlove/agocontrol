cmake_minimum_required (VERSION 2.6)

# configure a header file to pass some of the CMake settings
# to the source code
configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/agocontrol-init-script.sh.in"
    "${CMAKE_CURRENT_BINARY_DIR}/agocontrol-init-script.sh"
    @ONLY
)

install (PROGRAMS agodrain.py myavahi.py agoctrl.sh DESTINATION ${BINDIR})
install (DIRECTORY DESTINATION ${CONFDIR}/schema.d)
install (DIRECTORY DESTINATION ${CONFDIR}/maps)

OPTION(BUILD_CORE_drain "Build agodrain" ON)
if (BUILD_CORE_drain)
  add_subdirectory (drain)
endif()

OPTION(BUILD_CORE_resolver "Build agoresolver" ON)
if (BUILD_CORE_resolver)
  add_subdirectory (resolver)
endif()

OPTION(BUILD_CORE_rpc "Build agorpc" ON)
if (BUILD_CORE_rpc)
  add_subdirectory (rpc)
endif()

OPTION(BUILD_CORE_messagesend "Build messagesend" ON)
if (BUILD_CORE_messagesend)
  add_subdirectory (messagesend)
endif()

OPTION(BUILD_CORE_timer "Build agotimer" ON)
if (BUILD_CORE_timer)
  add_subdirectory (timer)
endif()

OPTION(BUILD_CORE_scenario "Build agoscenario" ON)
if (BUILD_CORE_scenario)
  add_subdirectory (scenario)
endif()

OPTION(BUILD_CORE_event "Build agoevent" ON)
if (BUILD_CORE_event)
  add_subdirectory (event)
endif()

OPTION(BUILD_CORE_datalogger "Build agodatalogger" ON)
if (BUILD_CORE_datalogger)
  add_subdirectory (datalogger)
endif()

OPTION(BUILD_CORE_lua "Build agolua" ON)
if (BUILD_CORE_lua)
  add_subdirectory (lua)
endif()

OPTION(BUILD_CORE_security "Build agosecurity" ON)
if (BUILD_CORE_security)
  add_subdirectory (security)
endif()

