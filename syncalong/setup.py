import setuptools
    
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="syncalong",
    version="0.0.1",
    author="Itai Fainstein, Shira Asa-El",
    author_email=["shira.asael@gmail.com", "itaifain@gmail.com"],
    description="Sync your music!",
    install_requires=requirements,
    url="https://github.com/shirasael/20588",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.6',
)
