cmake_minimum_required (VERSION 2.6)

file (GLOB AGORPC_SOURCE_FILES *.cpp)

set (RPC_LIBRARIES
    agoclient
    dl
    pthread
)


find_package (JsonCpp REQUIRED)
if (JSONCPP_FOUND)
  include_directories(${JSONCPP_INCLUDE_DIRS})
endif (JSONCPP_FOUND)

# add the executable
#add_executable (agorpc ${AGORPC_SOURCE_FILES})
add_executable (agorpc agorpc.cpp mongoose.c)
target_link_libraries (agorpc ${RPC_LIBRARIES})

add_executable (get_table_lang.cgi get_table_lang.cpp)


set (RPCPASSWD_LIBRARIES
    dl
    pthread
)
add_executable (rpc-htpasswd rpc-htpasswd.cpp mongoose.c)
target_link_libraries (rpc-htpasswd ${RPCPASSWD_LIBRARIES})


# configure a header file to pass some of the CMake settings
# to the source code
configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/activate.cgi.in"
    "${CMAKE_CURRENT_BINARY_DIR}/html/cgi-bin/activate.cgi"
    @ONLY
)

# workaround to making the translations
add_custom_target(translations) 
add_dependencies(agorpc translations)


file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/html DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

file(GLOB_RECURSE HTML_FILES ${CMAKE_CURRENT_BINARY_DIR}/html *.in.html)

foreach (infile ${HTML_FILES})

    string(REGEX REPLACE ".in.html$" ".html" outfile ${infile})
    string(REGEX REPLACE "${CMAKE_CURRENT_SOURCE_DIR}" "${CMAKE_CURRENT_BINARY_DIR}" outfile ${outfile})

    list(APPEND HTML_FILES_DONE ${outfile})

    add_custom_command(
        TARGET translations
        COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/mergetranslation.sh ${infile} ${outfile}
        COMMENT "Generate html files")

endforeach (infile)

install (FILES ${HTML_FILES_DONE} DESTINATION ${HTMLDIR})
install (TARGETS agorpc rpc-htpasswd RUNTIME DESTINATION ${BINDIR})
