cmake_minimum_required (VERSION 2.6)

file (GLOB SCRIPT_FILES *.in)

foreach (infile ${SCRIPT_FILES})

    string(REGEX REPLACE ".in$" "" outfile ${infile})

    configure_file(
        "${infile}"
        "${outfile}"
        @ONLY
    )

endforeach (infile)
