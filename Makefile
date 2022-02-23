SRC=pyoc


all: clean check tests build

clean:
	rm -rf build dist cover *.egg-info *.db

check:
	autoflake --in-place -r $(SRC)

tests:
	nosetests --with-coverage --cover-html --cover-package=$(SRC) test/

build:
	python3 setup.py sdist bdist_wheel

