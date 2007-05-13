AC_PREREQ(2.57)
AC_INIT([ccsm],esyscmd(. ./VERSION;echo -n $VERSION), [quinn@opencompositing.org])

AC_DEFINE_UNQUOTED(VERSION,"$VERSION",[Version])

AM_INIT_AUTOMAKE([1.9 dist-bzip2])
AC_CONFIG_HEADER([config.h])
AM_MAINTAINER_MODE

AC_ISC_POSIX

CCSM_REQUIRES="\
ccs-bindings >= 0.0.1"

PKG_CHECK_MODULES(CCS,$CCSM_REQUIRES)

AC_SUBST(CCSM_REQUIRES)

dnl PYTHON SPECIFIC

m4_define(required_python_abi,2.4)

#AM_PATH_PYTHON
#if test "$PYTHON_VERSION" = "2.4"
#then
#        AM_PATH_PYTHON_VERSION(2.4,2.4.0)
#else
#        AM_PATH_PYTHON_VERSION(2.5,2.5.0)
#fi

AC_OUTPUT([
Makefile
images/Makefile
misc/Makefile
])
