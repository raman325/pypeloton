from setuptools import find_packages, setup

with open("pypeloton/version.py") as f:
    exec(f.read())
with open("README.md", "r") as myfile:
    longdescription = myfile.read()

PACKAGES = find_packages(exclude=["tests", "tests.*"])

setup(
    name="pypeloton",
    version=__version__,  # noqa: F821
    description="Client library for the Peloton API",
    long_description=longdescription,
    long_description_content_type="text/markdown",
    url="https://github.com/raman325/pypeloton",
    author="raman325",
    author_email="raman325@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="peloton",
    packages=PACKAGES,
    install_requires=[
        "aiohttp"
    ],
)
