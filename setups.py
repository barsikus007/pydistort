import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pydistortssss",
    version="0.1.0",
    author="barsikus007",
    author_email='barsikus07@gmail.com',
    license="MIT",
    description='Asynchronous media distortion module',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/barsikus007/pydistort",
    # project_urls={
    #     "Bug Tracker": "https://github.com/pypa/sampleproject/issues",
    # },
    # classifiers=[
    #     "Programming Language :: Python :: 3",
    #     "License :: OSI Approved :: MIT License",
    #     "Operating System :: OS Independent",
    # ],
    # packages=setuptools.find_packages(),
    packages=['pydistort'],
    python_requires=">=3.10",
    install_requires=[
        'apng',
        'lottie[GIF]==0.6.11',
    ],
)
