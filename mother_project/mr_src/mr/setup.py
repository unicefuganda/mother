#from setuptools import setup, find_packages
from setuptools import find_packages
from distutils.core import setup

setup(
    name='rapidsms-mr',
    version='0.1',
    license="BSD",

    install_requires=[
        'django==1.3',
        'django-extensions',
        'django-uni-form',
        'django-mptt',
        'djtables',
        'django-nose',
    ],

    description='An application for sending automated messages, polls and emails in a sequence to mothers reminding them to receive regular treatments',
    long_description=open('README.rst').read(),
    author='Revence Kalibwani',
    author_email='revence@1st.ug',

    url='http://github.com/unicefuganda/mr/',
    download_url='http://github.com/unicefuganda/downloads',

    include_package_data=True,

    packages=find_packages(),
    package_data={'mr':['templates/*/*.html', 'templates/*/*/*.html', 'static/*/*'],
                  'healthmodels':['templates/*/*.html', 'templates/*/*/*.html', 'static/*/*'],
                  'script':['templates/*/*.html', 'templates/*/*/*.html', 'static/*/*'],
                  'poll':['templates/*/*.html', 'templates/*/*/*.html', 'static/*/*'],
                  'contact':['templates/*/*.html', 'templates/*/*/*.html', 'static/*/*'],
                  'generic':['templates/*/*.html', 'templates/*/*/*.html', 'static/*/*'], },
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],

)
