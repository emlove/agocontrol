cmake_minimum_required (VERSION 2.6)

set (RPC_LIBRARIES
    agoclient
    pthread
)

# add the executable
add_executable (agorpc agorpc.cpp mongoose.c)
target_link_libraries (agorpc ${RPC_LIBRARIES})

add_executable (get_table_lang.cgi get_table_lang.cpp)

set (RPCPASSWD_LIBRARIES
    pthread
)

IF (NOT FREEBSD)
	list(APPEND RPC_LIBRARIES dl )
	list(APPEND RPCPASSWD_LIBRARIES dl )
ENDIF (NOT FREEBSD)

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

file(GLOB_RECURSE HTML_FILES ${CMAKE_CURRENT_BINARY_DIR}/html/*.in.html)

foreach (infile ${HTML_FILES})

    string(REGEX REPLACE ".in.html$" ".html" outfile ${infile})

    add_custom_command(
        TARGET translations
        COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/mergetranslation.sh ${infile} ${outfile}
        COMMENT "Generate html files")

endforeach (infile)

install (TARGETS agorpc rpc-htpasswd RUNTIME DESTINATION ${BINDIR})
install (TARGETS get_table_lang.cgi RUNTIME DESTINATION ${HTMLDIR}/cgi-bin)
install(
   CODE "
   file(GLOB_RECURSE HTML_FILES ${CMAKE_CURRENT_BINARY_DIR}/html/*.in.html)
   file(REMOVE \${HTML_FILES})
   file(GLOB CGI_SCRIPTS ${CMAKE_CURRENT_BINARY_DIR}/html/cgi-bin/*.cgi)
   file(INSTALL \${CGI_SCRIPTS} DESTINATION ${HTMLDIR}/cgi-bin/ FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)
   file(REMOVE \${CGI_SCRIPTS})
   file(GLOB HTML_FILES ${CMAKE_CURRENT_BINARY_DIR}/html/*) \n
   file(INSTALL DESTINATION ${HTMLDIR}
   TYPE FILE FILES \${HTML_FILES})
   "
)

