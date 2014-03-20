cmake_minimum_required (VERSION 2.6)

file (GLOB SCRIPT_FILES *.in)

foreach (infile ${SCRIPT_FILES})

    string(REGEX REPLACE ".in$" "" outfile ${infile})
    string(REGEX REPLACE ".*/" "" outfile ${outfile})


    configure_file(
        "${infile}"
        "${CMAKE_CURRENT_BINARY_DIR}/${outfile}"
        @ONLY
    )

    LIST(APPEND SCRIPT_FILES_DONE ${CMAKE_CURRENT_BINARY_DIR}/${outfile})

endforeach (infile)

install (PROGRAMS ${SCRIPT_FILES_DONE} convert-zwave-uuid.py convert-scenario.py convert-event.py convert-config.py DESTINATION ${BINDIR})
