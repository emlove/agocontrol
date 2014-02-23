cmake_minimum_required (VERSION 2.6)

file (GLOB SYSV_FILES *.in)

foreach (infile ${SYSV_FILES})

    string(REGEX REPLACE ".in$" "" outfile ${infile})
    string(REGEX REPLACE ".*/" "" outfile ${outfile})


    configure_file(
        "${infile}"
        "${CMAKE_CURRENT_BINARY_DIR}/${outfile}"
        @ONLY
    )

endforeach (infile)
