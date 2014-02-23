cmake_minimum_required (VERSION 2.6)

set (MESSAGESEND_LIBRARIES
    agoclient
)

# add the executable
add_executable (messagesend messagesend.cpp)
target_link_libraries (messagesend ${MESSAGESEND_LIBRARIES})
