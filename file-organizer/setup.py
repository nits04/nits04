from setuptools import setup, find_packages

setup(
    name="file-organizer",
    version="1.0.0",
    description="CLI tool to automatically organize files by type, date, or extension",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "rich>=13.0.0",
        "watchdog>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "organize=main:main",
        ],
    },
)
