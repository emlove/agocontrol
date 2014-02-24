cmake_minimum_required (VERSION 2.6)

file (GLOB_RECURSE AGODATALOGGER_SOURCE_FILES *.cpp)
set (DATALOGGER_LIBRARIES
    agoclient
    sqlite3
    boost_date_time
)

# add the executable
add_executable (agodatalogger ${AGODATALOGGER_SOURCE_FILES})
target_link_libraries (agodatalogger ${DATALOGGER_LIBRARIES})

install (TARGETS agodatalogger RUNTIME DESTINATION ${BINDIR})
