from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="krista-infinispan",
    version="1.0.0",
    author="Vijay Bhatt",
    author_email="vijay.bhatt@kristasoft.com",
    description="Python package with Infinispan integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Vijay2351989/krista-infra-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
)