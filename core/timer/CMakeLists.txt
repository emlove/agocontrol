cmake_minimum_required (VERSION 2.6)

file (GLOB_RECURSE AGOTIMER_SOURCE_FILES *.cpp)
set (TIMER_LIBRARIES
    agoclient
    boost_system
    pthread
)

# add the executable
add_executable (agotimer ${AGOTIMER_SOURCE_FILES})
target_link_libraries (agotimer ${TIMER_LIBRARIES})

install (TARGETS agotimer RUNTIME DESTINATION ${BINDIR})
