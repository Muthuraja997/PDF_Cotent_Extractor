"""
Setup script for USB PD Parser package
"""

from setuptools import setup, find_packages

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="usb_pd_parser",
    version="1.0.0",
    author="Omni Developer",
    author_email="developer@example.com",
    description="A parser for USB Power Delivery specification PDF documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/usb-pd-parser",
    project_urls={
        "Bug Tracker": "https://github.com/your-username/usb-pd-parser/issues",
        "Documentation": "https://github.com/your-username/usb-pd-parser#readme",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Markup",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pdfplumber>=0.7.0",
        "PyMuPDF>=1.19.0",
        "pandas>=1.3.0",
        "openpyxl>=3.0.0",
        "jsonlines>=2.0.0",
        "tqdm>=4.62.0",
    ],
    entry_points={
        "console_scripts": [
            "usb-pd-parser=pdf_parser.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
