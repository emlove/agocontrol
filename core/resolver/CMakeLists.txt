cmake_minimum_required (VERSION 2.6)

file (GLOB_RECURSE AGORESOLVER_SOURCE_FILES *.cpp)

set (RESOLVER_LIBRARIES
    yaml-cpp
    jsoncpp
    sqlite3
    agoclient
    pthread
    boost_system
    boost_filesystem
)

# add the executable
add_executable (agoresolver ${AGORESOLVER_SOURCE_FILES})
target_link_libraries (agoresolver ${RESOLVER_LIBRARIES})

install (TARGETS agoresolver RUNTIME DESTINATION ${BINDIR})
install (DIRECTORY DESTINATION ${CONFDIR}/db)
