from setuptools import setup


setup(name='vAdvisor',
      version='0.0.1',
      description='',
      long_description='',
      author='Roman Mohr',
      author_email='roman@redhat.at',
      url='',
      license="ASL2.0",
      py_modules=[],
      packages=['vadvisor', 'vadvisor/app', 'vadvisor/virt', 'vadvisor/store'],
      setup_requires=['pytest-runner'],
      tests_require=['pytest', 'pytest-cov'],
      entry_points="""
          [console_scripts]
              vAdvisor=vadvisor.vadvisor:run
      """)
