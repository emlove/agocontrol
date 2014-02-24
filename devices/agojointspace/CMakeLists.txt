cmake_minimum_required (VERSION 2.6)

install (FILES agojointspace.py DESTINATION ${BINDIR})
install (CODE "file(MAKE_DIRECTORY \${ENV}\${CMAKE_INSTALL_PREFIX}${CONFDIR}/jointspace)")
