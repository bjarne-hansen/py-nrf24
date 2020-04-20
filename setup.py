import setuptools

with open("PyPI.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nrf24",
    version="0.5.2",
    keywords='nrf24l01 iot raspberry arduino',
    author="Bjarne Hansen",
    author_email="bjarne@conspicio.dk",
    license='MIT',
    description="A package enabling communication using NRF24L01 modules.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bjarne-hansen/py-nrf24",
    package_dir={"": "src"},
    packages=setuptools.find_namespace_packages(where="src"),
    install_requires=['pigpio'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)