from setuptools import setup

setup(
  name='fungi',
  version='0.2',
  description='Functional Gateway Interface Drug',
  url='https://github.com/ericgj/fungi',
  author='Eric Gjertsen',
  author_email='ericgj72@gmail.com',
  license='MIT',
  packages=['fungi', 'fungi/gae', 'fungi/util', 'pymonad_extra', 'pymonad_extra/util' ],
  dependency_links=[
    'https://bitbucket.org/ericgj/pymonad/get/master.tar.gz#egg=pymonad'
  ],
  install_requires=[
    'typing >=3.5, <3.6',
    'webob >=1.6, <1.7',
    'pymonad'
  ]
)

