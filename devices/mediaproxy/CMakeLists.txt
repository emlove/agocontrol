cmake_minimum_required (VERSION 2.8.8)

add_subdirectory(groupsock)
add_subdirectory(UsageEnvironment)
add_subdirectory(liveMedia)
add_subdirectory(BasicUsageEnvironment)



include_directories("./UsageEnvironment/include")
include_directories("./groupsock/include")
include_directories("./liveMedia/include")
include_directories("./BasicUsageEnvironment/include")

set (DEVICE_EXTRA_LIBRARIES
    agoclient
    liveMedia
    groupsock
    BasicUsageEnvironment
    UsageEnvironment
)

set (DEVICE "agomediaproxy")

# add the executable
add_executable (${DEVICE} agomediaproxy.cpp)

target_link_libraries (${DEVICE} ${DEVICE_EXTRA_LIBRARIES})

install (TARGETS ${DEVICE} RUNTIME DESTINATION ${BINDIR})
