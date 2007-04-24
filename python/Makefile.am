INCLUDES=\
		 $(PYTHON_INCLUDES)\
		 @BSETTINGS_CFLAGS@

bsettings.c: bsettings.pyx
	-pyrexc bsettings.pyx

bsettings_la_LDFLAGS = -module -avoid-version -fPIC -export-symbols-regex initbsettings -lX11
bsettings_la_LIBADD = @BSETTINGS_LIBS@
bsettings_la_SOURCES = bsettings.c
bsettingsdir=$(pyexecdir)
bsettings_LTLIBRARIES=bsettings.la

EXTRA_DIST=bsettings.pyx

clean-local:
	rm -f bsettings.c
