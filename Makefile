all:
	@python setup.py build --prefix=${PREFIX}

install: all
	@python setup.py install --prefix=${PREFIX}

uninstall:
	@python setup.py uninstall --prefix=${PREFIX}

clean:
	rm -rf build/
