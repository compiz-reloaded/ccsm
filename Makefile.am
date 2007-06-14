## Process this file with automake to produce Makefile.in
bin_SCRIPTS=ccsm

DISTCLEANFILES = $(bin_SCRIPTS)

SUBDIRS = images misc

EXTRA_DIST = ccsm.in $(bin_SCRIPTS)

ccsm: $(top_srcdir)/ccsm.in Makefile
	sed -e "s|@prefix\@|$(prefix)|g" $< > $@
