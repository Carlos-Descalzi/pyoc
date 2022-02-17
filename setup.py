import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="pyoc",
    version="0.0.1",
    author="Carlos Descalzi",
    author_email="carlos.descalzi@gmail.com",
    description="An IOC/Dependency injection library similar to Spring IOC Container",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Carlos-Descalzi/pyoc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
