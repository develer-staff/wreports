from setuptools import setup, find_packages

setup(name='wreports',
      version='1.0.0-pre',
      author='Matteo Bertini <naufraghi@develer.com>',
      description='Fixed page report generator',
      long_description=open('README.rst').read(),
      license='LICENSE.txt',
      keywords="qt, report",

      # dependencies
      install_requires=['mistune',
                        'bbcode'],

      # package source directory
      package_dir={'': 'src'},
      packages=find_packages('src', exclude='docs'),

      # configure the default test suite
      test_suite='tests.suite'
)
