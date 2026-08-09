from setuptools import find_packages, setup

setup(
    name="voting",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
