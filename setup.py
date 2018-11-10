import setuptools

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except IOError:
        long_description = None

setuptools.setup(
    name='bindilla',
    version='0.1.0',
    author='Nokome Bentley',
    description='A Stencila to Binder bridge',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/stencila/bindilla',
    packages=setuptools.find_packages(),
    keywords=['Jupyter', 'Stencila'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Framework :: Jupyter',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Topic :: Scientific/Engineering'
    ],
    install_requires=[
        'pycurl',
        'pytz',
        'tornado'
    ]
)
