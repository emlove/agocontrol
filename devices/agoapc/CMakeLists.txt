cmake_minimum_required (VERSION 2.6)

install (FILES agoapc.py DESTINATION ${BINDIR})
install (CODE "file(MAKE_DIRECTORY \${ENV}\${CMAKE_INSTALL_PREFIX}${CONFDIR}/apc)")
