from setuptools import setup, find_packages

# Function to read the requirements.txt file
def parse_requirements(filename):
    with open(filename, "r") as req_file:
        return req_file.read().splitlines()
    
setup(
    name="beacon-snatch",
    version="0.1.4",
    author="RetroZelda",
    author_email="retrozelda@gmail.com",
    description="Snatch from Beacon",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/retrozelda/beacon-snatch",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=parse_requirements("dependencies"), 
    entry_points={
        "console_scripts": [
            "beacon-snatch=beacon_snatch.cli:main",
        ],
    },
)
