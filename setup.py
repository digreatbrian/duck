import os
from setuptools import setup,find_packages

def get_version():
	version_file=os.path.join(os.path.abspath(os.path.dirname(__file__)),"duck","version.py")
	with open(version_file,"r") as fd:
		r=fd.read()
		r=r.split('\n')
		for x in r:
			if x.startswith('version'):
				a,b=x.split('=')
				version=b
				return version

if __name__ == '__main__':
    setup(
        version=get_version(),
        packages=find_packages(
            include=["duck","duck.*"], exclude=["__pycache__"]
        ),
        package_dir={"duck": "duck"},
        setup_requires=[],
        python_requires=">=3.7",
    )
