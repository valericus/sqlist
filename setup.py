from setuptools import setup, find_packages

setup(
    name='sqlist',
    version='0.2.1',
    packages=find_packages(),
    description='List-like wrapper for SQLite',
    long_description=open('README.rst').read(),

    author='Valery Ryaboshapko',
    author_email='valera@creator.su',
    license='MIT',
    url='https://github.com/valericus/sqlist',

    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],

    zip_safe=True
)
