all:
	@python setup.py build --prefix=${PREFIX}

install:
	@python setup.py install --prefix=${PREFIX}

clean:
	rm -r build/
