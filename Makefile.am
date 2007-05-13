## Process this file with automake to produce Makefile.in
bin_SCRIPTS=ccsm

DISTCLEANFILES=$(bin_SCRIPTS)

SUBDIRS = images

EXTRA_DIST=$(bin_SCRIPTS)

ccsm: $(top_srcdir)/ccsm.in Makefile
	sed -e "s|@prefix\@|$(prefix)|g" $< > $@
