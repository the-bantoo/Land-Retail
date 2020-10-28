# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in land_retail/__init__.py
from land_retail import __version__ as version

setup(
	name='land_retail',
	version=version,
	description='Land Planning And Allocation',
	author='Bantoo Accounting',
	author_email='hello@thebantoo.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
