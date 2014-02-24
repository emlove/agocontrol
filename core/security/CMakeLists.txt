cmake_minimum_required (VERSION 2.6)

set (SECURITY_LIBRARIES
    agoclient
    pthread
)

# add the executable
add_executable (agosecurity agosecurity.cpp)
target_link_libraries (agosecurity ${SECURITY_LIBRARIES})

install (TARGETS agosecurity RUNTIME DESTINATION ${BINDIR})
