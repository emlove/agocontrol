cmake_minimum_required (VERSION 2.6)

set (SCENARIO_LIBRARIES
    agoclient
    pthread
)

# add the executable
add_executable (agoscenario agoscenario.cpp)
target_link_libraries (agoscenario ${SCENARIO_LIBRARIES})

install (TARGETS agoscenario RUNTIME DESTINATION ${BINDIR})
