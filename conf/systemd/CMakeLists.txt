cmake_minimum_required (VERSION 2.6)

file (GLOB SYSTEMD_FILES *.in)

foreach (infile ${SYSTEMD_FILES})

    string(REGEX REPLACE ".in$" "" outfile ${infile})
    string(REGEX REPLACE ".*/" "" outfile ${outfile})


    configure_file(
        "${infile}"
        "${CMAKE_CURRENT_BINARY_DIR}/${outfile}"
        @ONLY
    )

    LIST(APPEND SYSTEMD_FILES_DONE ${CMAKE_CURRENT_BINARY_DIR}/${outfile})

endforeach (infile)

file (GLOB SYSTEMD_FILES *.service)
install (FILES ${SYSTEMD_FILES_DONE} ${SYSTEMD_FILES} DESTINATION /lib/systemd/system)
