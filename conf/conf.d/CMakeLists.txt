cmake_minimum_required (VERSION 2.6)

file (GLOB CONFD_FILES *.in)

foreach (infile ${CONFD_FILES})

    string(REGEX REPLACE ".in$" "" outfile ${infile})

    configure_file(
        "${infile}"
        "${outfile}"
        @ONLY
    )

endforeach (infile)
