cmake_minimum_required (VERSION 2.6)

configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/agocontrol.in"
    "${CMAKE_CURRENT_SOURCE_DIR}/agocontrol"
    @ONLY
)
