all: setup lint build

setup:
	pip install --user setuptools wheel pylint pytest

setup-travis:
	pip install setuptools wheel pylint pytest tox-travis

run:
	python3 -m bindilla

build:
	python3 setup.py bdist_wheel
.PHONY: build

build-docker:
	docker build --tag stencila/bindilla .

run-docker:
	docker run -p 8888:8888 -it stencila/bindilla

install:
	pip install --user .

lint:
	pylint bindilla

test:
	tox

cover:
	tox -e cover

clean:
	rm -rf bindilla/*.pyc build dist bindilla.egg-info
