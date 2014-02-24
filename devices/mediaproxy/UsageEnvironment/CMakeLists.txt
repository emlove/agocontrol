cmake_minimum_required (VERSION 2.6)


include_directories("../groupsock/include")
include_directories("./include")


file(GLOB_RECURSE LIB_SOURCE_FILES *.cpp)

add_library (UsageEnvironment STATIC ${LIB_SOURCE_FILES})
set_target_properties(UsageEnvironment PROPERTIES COMPILE_FLAGS "-DSOCKLEN_T=socklen_t -D_LARGEFILE_SOURCE=1 -D_FILE_OFFSET_BITS=64 ${STATIC_FLAGS}")

# Install instructions for this target
install (TARGETS UsageEnvironment ARCHIVE DESTINATION ${LIBDIR})
install (DIRECTORY include DESTINATION ${INCDIR}/UsageEnvironment)
