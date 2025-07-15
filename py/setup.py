from pathlib import Path
from setuptools import setup, find_packages

this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="scjson",
    version="0.1.0",
    description="Tools for converting between scjson and SCXML",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
    data_files=[("", ["LEGAL.md"])],
)
