## Process this file with automake to produce Makefile.in
bin_SCRIPTS=ccsm 

DISTCLEANFILES = $(bin_SCRIPTS)

EXTRA_DIST = ccsm.in $(bin_SCRIPTS)

ccsm: $(srcdir)/ccsm.in Makefile
	sed -e "s|@prefix\@|$(prefix)|g" $< > $@
