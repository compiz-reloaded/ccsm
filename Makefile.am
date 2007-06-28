## Process this file with automake to produce Makefile.in
bin_SCRIPTS=ccsm

DISTCLEANFILES = $(bin_SCRIPTS) \
  	intltool-extract 	\
	intltool-merge   	\
	intltool-update  

SUBDIRS = images misc po

EXTRA_DIST = ccsm.in $(bin_SCRIPTS) \
	$(desktop_DATA)         \
	intltool-extract.in 	\
	intltool-merge.in   	\
	intltool-update.in

ccsm: $(top_srcdir)/ccsm.in Makefile
	sed -e "s|@prefix\@|$(prefix)|g" $< > $@
