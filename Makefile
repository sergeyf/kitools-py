.PHONY: build
build: clean
	python setup.py sdist bdist_wheel


.PHONY: build_clean
clean:
	rm -rf build/*
	rm -rf dist/*
	rm -rf htmlcov


.PHONY: init_dev
init_dev:
	pip install -r requirements.txt


.PHONY: test
test:
	pytest -v --cov


.PHONY: test_html
test_html:
	pytest -v --cov --cov-report html


.PHONY: install_local
install_local:
	pip install -e .


.PHONY: install_test
install_test:
	pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple kitools


.PHONY: publish_test
publish_test: build
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*


.PHONY: uninstall
uninstall:
	pip uninstall -y kitools
