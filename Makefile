
test:
	PYTHONPATH=${GAE_SDK_ROOT}:. python2 test/suite.py

.PHONY: test
