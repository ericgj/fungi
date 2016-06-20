from setuptools import setup

setup(
  name='fungi',
  version='0.1',
  description='Functional Gateway Interface Drug',
  url='https://github.com/ericgj/fungi',
  author='Eric Gjertsen',
  author_email='ericgj72@gmail.com',
  license='MIT',
  packages=['fungi', 'fungi/gae', 'fungi/util', 'pymonad_extra', 'pymonad_extra/util' ],
  dependency_links=[
    'git+https://bitbucket.org/ericgj/pymonad.git'
  ],
  install_requires=[
    'typing >=3.5, <3.6',
    'webob >=1.6, <1.7'
  ]
)

