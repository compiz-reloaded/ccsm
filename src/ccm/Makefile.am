## Process this file with automake to produce Makefile.in
bin_SCRIPTS=Constants.py

DISTCLEANFILES = $(bin_SCRIPTS)

EXTRA_DIST = Constants.in $(bin_SCRIPTS)

Constants.py: Constants.in Makefile
	sed -e "s|@prefix\@|$(prefix)|g" $< > $@
