INCLUDES=\
		 $(PYTHON_INCLUDES)\
		 @CCS_CFLAGS@

ccs.c: ccs.pyx
	-pyrexc ccs.pyx

ccs_la_LDFLAGS = -module -avoid-version -fPIC -export-symbols-regex initccs -lX11
ccs_la_LIBADD = @CCS_LIBS@
ccs_la_SOURCES = ccs.c
ccsdir=$(pyexecdir)
ccs_LTLIBRARIES=ccs.la

EXTRA_DIST=ccs.pyx

clean-local:
	rm -f ccs.c
