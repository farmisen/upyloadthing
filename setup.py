from setuptools import find_packages, setup

setup(
    name="upyloadthing",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
    ],
    python_requires=">=3.7",
)
