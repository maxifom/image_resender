from setuptools import setup, find_packages

setup(
    name='image_resender',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'app = image_resender.cmd.app:main',
        ],
    },
)
