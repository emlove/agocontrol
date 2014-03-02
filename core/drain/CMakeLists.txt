cmake_minimum_required (VERSION 2.6)

set (DRAIN_LIBRARIES
    agoclient
)

# add the executable
add_executable (agodrain agodrain.cpp)
target_link_libraries (agodrain ${DRAIN_LIBRARIES})

install (TARGETS agodrain RUNTIME DESTINATION ${BINDIR})
