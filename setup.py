from setuptools import setup, find_packages

setup(
    name='pymachine',
    version='0.2',
    description='Eilenberg-machines for computational semantics',
    url='https://github.com/kornai/pymachine',
    author='Gabor Recski, Attila Zseder, David Nemeskey',
    author_email='recski@mokk.bme.hu',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='semantics nlp',

    package_dir={'': 'src'},
    packages=find_packages("src"),

    dependency_links=[
        "https://github.com/zseder/hunmisc/tarball/master#egg=hunmisc"],
    install_requires=["hunmisc", "pyparsing", "stemming"],
)
