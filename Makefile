all:
	python setup.py build

install:
	python setup.py install --prefix=${PREFIX}

clean:
	rm -r build/
