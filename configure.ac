AC_PREREQ(2.57)
AC_INIT([bsettings-bindings],esyscmd(. ./VERSION;echo -n $VERSION), [livinglatexkali@gmail.com])

AC_DEFINE_UNQUOTED(VERSION,0.0.1,[Version])

AM_INIT_AUTOMAKE([1.9 dist-bzip2])
AC_CONFIG_HEADER([config.h])
AM_MAINTAINER_MODE

AC_ISC_POSIX
AC_PROG_CC
AC_PROG_CPP
AC_PROG_LIBTOOL
AC_HEADER_STDC

BSETTINGS_REQUIRES="\
bsettings >= 0.1.2 \
glib-2.0 >= 2.6 "

PKG_CHECK_MODULES(BSETTINGS,$BSETTINGS_REQUIRES)

AC_SUBST(BSETTINGS_REQUIRES)

dnl PYTHON SPECIFIC

m4_define(required_python_abi,2.4)

AM_PATH_PYTHON
if test "$PYTHON_VERSION" = "2.4"
then
	AM_PATH_PYTHON_VERSION(2.4,2.4.0)
else
	AM_PATH_PYTHON_VERSION(2.5,2.5.0)
fi

AC_CHECK_PROGS(PYREX, pyrexc)
if test -z "$PYREX"
then
	AC_MSG_ERROR([Couldn't find Pyrex])
fi

AC_CONFIG_FILES([
	bsettings-bindings.pc
	Makefile
	python/Makefile
])

AC_OUTPUT
