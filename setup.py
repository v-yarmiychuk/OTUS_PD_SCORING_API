from setuptools import find_packages
from setuptools import setup

setup(
    name='Scoring_API',
    version='',
    packages=find_packages(),
    url='',
    license='',
    author='v.yarmiychuk',
    author_email='v.yarmiychuk@gmail.com',
    description='Python Developer Professional  Scoring API',
    install_requires=[
        'argcomplete',
    ],
    entry_points={
        'console_scripts': [
            'scoring_api = api.entrypoint:run',
        ]
    },
)
