from setuptools import setup

setup(
  name='fungi',
  version='0.6',
  description='Functional Gateway Interface Drug',
  url='https://github.com/ericgj/fungi',
  author='Eric Gjertsen',
  author_email='ericgj72@gmail.com',
  license='MIT',
  packages=['fungi', 'fungi/gae', 'fungi/util' ],
  dependency_links=[
    'https://bitbucket.org/ericgj/pymonad/get/master.zip#egg=pymonad',
    'https://bitbucket.org/ericgj/pymonad-extra/get/master.zip#egg=pymonad_extra'
  ],
  install_requires=[
    'typing >=3.5, <3.6',
    'webob >=1.6, <1.7',
    'oauth2client >=2.2, <2.3',
    'httplib2 >=0.9, <0.10'
  ],
  tests_require=[
    'webtest >=2.0, <2.1'
  ]
)

