cmake_minimum_required (VERSION 2.6)

file (GLOB INIT_FILES *.in)

foreach (infile ${INIT_FILES})

    string(REGEX REPLACE ".in$" "" outfile ${infile})

    configure_file(
        "${infile}"
        "${outfile}"
        @ONLY
    )

endforeach (infile)

add_subdirectory (systemd)
add_subdirectory (conf.d)
add_subdirectory (sysvinit)
