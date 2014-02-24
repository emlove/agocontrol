cmake_minimum_required (VERSION 2.6)


include_directories("../UsageEnvironment/include")
include_directories("./include")


file(GLOB_RECURSE LIB_SOURCE_FILES *.cpp *.c)

add_library (groupsock STATIC ${LIB_SOURCE_FILES})
set_target_properties(groupsock PROPERTIES COMPILE_FLAGS "-DSOCKLEN_T=socklen_t -D_LARGEFILE_SOURCE=1 -D_FILE_OFFSET_BITS=64 ${STATIC_FLAGS}")

# Install instructions for this target
install (TARGETS groupsock ARCHIVE DESTINATION ${LIBDIR})
install (DIRECTORY include DESTINATION ${INCDIR}/groupsock)
