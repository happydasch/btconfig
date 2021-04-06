import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="btconfig",
    version="0.0.1",
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
