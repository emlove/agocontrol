cmake_minimum_required (VERSION 2.6)

set (DEVICE_SOURCE_FILES agoenocean3.cpp esp3.cpp)

set (DEVICE_EXTRA_LIBRARIES
     agoclient
     pthread
)

set (DEVICE "agoenocean3")

# add the executable
add_executable (${DEVICE} ${DEVICE_SOURCE_FILES})
target_link_libraries (${DEVICE} ${DEVICE_EXTRA_LIBRARIES})

install (TARGETS ${DEVICE} RUNTIME DESTINATION ${BINDIR})
