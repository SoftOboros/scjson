from setuptools import setup, find_packages

setup(
    name="scjson",
    version="0.1.0",
    description="Tools for converting between scjson and SCXML",
    packages=find_packages(),
    install_requires=[
        "click",
        "xmlschema",
        "xsdata",
        "pydantic",
    ],
    entry_points={
        "console_scripts": [
            "scjson=scjson.cli:main",
        ]
    },
)
