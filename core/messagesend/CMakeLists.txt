cmake_minimum_required (VERSION 2.6)

set (MESSAGESEND_LIBRARIES
    agoclient
    qpidtypes
)

# add the executable
add_executable (messagesend messagesend.cpp)
target_link_libraries (messagesend ${MESSAGESEND_LIBRARIES})

install (TARGETS messagesend RUNTIME DESTINATION ${BINDIR})
