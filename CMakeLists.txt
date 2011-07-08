find_package (CompizConfig REQUIRED)
include (LibCompizConfigCommon)

# Hack
set (CMAKE_PROJECT_NAME ccsm)

file (READ ${CMAKE_SOURCE_DIR}/VERSION COMPIZ_RELEASE_VERSION LIMIT 12 OFFSET 0)
string (STRIP ${COMPIZ_RELEASE_VERSION} COMPIZ_RELEASE_VERSION)

set (VERSION ${COMPIZ_RELEASE_VERSION})

add_custom_target (python ALL
		    COMMAND python setup.py build
		    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
		    COMMENT "Generating Python Bytecode")

add_custom_target (install
		   COMMAND python setup.py install --prefix=${CMAKE_INSTALL_PREFIX}
		   WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
		   COMMENT "Installing Python Files")

add_custom_target (clean
		   COMMAND python setup.py clean
		   WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
		   COMMENT "Cleaning Python Files")

add_custom_target (uninstall
		   COMMAND python setup.py uninstall
		   WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
		   COMMENT "Uninstalling Python Files")

compiz_print_configure_header ("CompizConfig Settings Manager")
compiz_print_configure_footer ()

compiz_add_git_dist ()
compiz_add_distcheck ()
compiz_add_release ()
compiz_add_release_signoff ()


