.ONESHELL:
SHELL := /bin/bash
SRC = $(wildcard nbs/*.ipynb)

all: build docs

diff:
	nbdev_diff_nbs

clean_nbs:
	nbdev_clean_nbs

build: $(SRC)
	rm -r ./customer_segmentation_toolkit
	nbdev_build_lib

sync:
	nbdev_update_lib

docs_serve: docs
	# hint: first install bundle: `BUNDLE_GEMFILE="docs/Gemfile" bundle install`
	cd docs && bundle exec jekyll serve

docs: $(SRC)
	nbdev_build_docs
	touch docs

test:
	nbdev_test_nbs

release: pypi #conda_release
	nbdev_bump_version

conda_release:
	fastrelease_conda_package

pypi: dist
	twine upload --repository pypi dist/*

dist: clean
	python setup.py sdist bdist_wheel

clean:
	rm -rf dist

.PHONY: \
	all \
	diff \
	clean \
	build \
	sync \
	docs_serve \
	docs \
	test \
	release \
	conda_release \
	pypi \
	dist \
	rm_dist
