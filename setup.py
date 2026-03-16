from setuptools import setup

setup(
    name="codebase-analyzer",
    version="1.0.0",
    description="CLI tool for analyzing Python codebases using AST",
    author="Vansh Kamra",
    py_modules=["analyzer"],
    install_requires=["rich>=13.0"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "codebase-analyzer=analyzer:main",
        ],
    },
)
