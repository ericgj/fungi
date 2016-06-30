
test:
	PYTHONPATH=${GAE_SDK_ROOT}:. python2 -m unittest discover -s test

.PHONY: test
