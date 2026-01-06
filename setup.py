from setuptools import find_packages,setup
from typing import List

HYPEN_E_DOT='-e .'
def get_requirements(file_path:str)->List[str]:
    '''
    this function will return the list of requirements
    '''
    requirements=[]
    with open(file_path) as file_obj:
        requirements=file_obj.readlines()
        requirements=[req.replace("\n","") for req in requirements]

        if HYPEN_E_DOT in requirements:
            requirements.remove(HYPEN_E_DOT)
    
    return requirements

setup(
name='indian-tech-job-intelligence',
version='1.0.0',
author='CS Majors Team',
author_email='vigneshgogula9@gmail.com',
description='AI-Powered Indian Tech Job Market Intelligence Platform',
long_description=open('README.md').read(),
long_description_content_type='text/markdown',
url='https://github.com/yourusername/gravitohacks',
packages=find_packages(),
install_requires=get_requirements('requirements.txt'),
classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Job Seekers',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
],
python_requires='>=3.8',
)