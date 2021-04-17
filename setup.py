import setuptools
from distutils.util import convert_path

with open("README.md", "r") as fh:
    long_description = fh.read()

main_ns = {}
ver_path = convert_path('btconfig/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setuptools.setup(
    name="btconfig",
    version=main_ns['__version__'],
    description="A configureable backtrader execution helper",
    long_description=long_description,
    license='GNU General Public License Version 3',
    url="https://github.com/happydasch/btconfig",
    packages=setuptools.find_packages(),
    install_requires=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3"
    ],
    python_requires='>=3.6'
)
