from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--cov', 'static', 'tests']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(name='vAdvisor',
      version='0.0.1',
      description='',
      long_description=open('README.md', 'rb').read().decode('utf-8'),
      author='Roman Mohr',
      author_email='roman@redhat.at',
      url='',
      license="ASL2.0",
      py_modules=['vadvisor'],
      packages=[],
      cmdclass={'test': PyTest},
      tests_require=['pytest'],
      entry_points="""
          [console_scripts]
              vAdvisor=vadvisor:run
      """)
