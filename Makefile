all: setup lint build

setup:
	pip install --user setuptools wheel pylint pytest

setup-travis:
	pip install setuptools wheel pylint pytest tox-travis

run:
	python3 -m bindila

build:
	python3 setup.py bdist_wheel
.PHONY: build

build-docker:
	docker build --tag stencila/bindila .

run-docker:
	docker run -p 8888:8888 -it stencila/bindila

install:
	pip install --user .

lint:
	pylint bindila

test:
	tox

clean:
	rm -rf bindila/*.pyc build dist bindila.egg-info
