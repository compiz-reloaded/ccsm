AC_PREREQ(2.57)
AC_INIT([compizconfig-settings-manager],esyscmd(. ./VERSION;echo -n $VERSION), [quinn@opencompositing.org])

AC_DEFINE_UNQUOTED(VERSION,"$VERSION",[Version])

AM_INIT_AUTOMAKE([1.9 dist-bzip2])
AC_CONFIG_HEADER([config.h])
AM_MAINTAINER_MODE

IT_PROG_INTLTOOL([0.35.0])
AC_SUBST(ALL_LINGUAS)
AM_GLIB_GNU_GETTEXT
GETTEXT_PACKAGE=ccsm
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE,"$GETTEXT_PACKAGE", [Gettext package.])
AC_SUBST(GETTEXT_PACKAGE)

AC_ISC_POSIX

CCSM_REQUIRES="\
compizconfig-python >= 0.0.1"

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
po/Makefile.in
])
