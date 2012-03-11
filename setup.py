from setuptools import setup, find_packages

setup(
    name="gevent-websocket",
    version="0.3.1",
    description="Websocket handler for the gevent pywsgi server, a Python network library",
    long_description=open("README.rst").read(),
    author="Jeffrey Gelens",
    author_email="jeffrey@noppo.pro",
    license="BSD",
    url="https://bitbucket.org/Jeffrey/gevent-websocket",
    download_url="https://bitbucket.org/Jeffrey/gevent-websocket",
    install_requires=("gevent", "greenlet"),
    packages=find_packages(exclude=["examples","tests"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
)
