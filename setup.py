import os
from setuptools import find_packages, setup

import bronto


os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

VERSION = bronto.__version__
github_url = 'http://github.com/Scotts-Marketplace/bronto-python/'
requires = ['suds', ]

setup(name='bronto-python',
      version=VERSION,
      author='Joey Wilhelm',
      author_email='joey@scottsmarketplace.com',
      license='Apache',
      url=github_url,
      download_url='%sarchive/%s.tar.gz' % (github_url, VERSION),
      packages=find_packages(),
      include_package_data=True,
      install_requires=requires,
      tests_require=requires,
      description='A python wrapper around Bronto\'s SOAP API',
      long_description=open('README.rst').read(),
      keywords=['bronto', 'soap', 'marketing'],
      classifiers=[
           'Development Status :: 4 - Beta',
           'Environment :: Web Environment',
           'Intended Audience :: Developers',
           'License :: OSI Approved :: Apache Software License',
           'Natural Language :: English',
           'Operating System :: OS Independent',
           'Programming Language :: Python',
      ]
)
