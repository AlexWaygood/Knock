from typing import Sequence
from subprocess import check_call
from sys import executable


def install(packageArgs: Sequence):
    check_call([executable, "-m", "pip", "install", *packageArgs])


def AllInstalled():
    Success = True

    try:
        import matplotlib
    except ImportError:
        Success = False
        print('Matplotlib not installed correctly; installing now...')
        install(('matplotlib',))

    try:
        import numpy
    except ImportError:
        Success = False
        print('Numpy not installed correctly; installing now...')
        install(('numpy',))

    try:
        from PIL import Image
    except ImportError:
        Success = False
        print('Pillow not installed correctly; installing now')
        install(('--upgrade', 'pillow'))

    try:
        import pandas
    except ImportError:
        Success = False
        print('pandas not installed correctly; installing now')
        install(('pandas',))

    try:
        import Crypto
    except ImportError:
        Success = False
        print('pycryptodome not installed correctly; installing now')
        install(('pycryptodome',))

    try:
        import pygame
    except ImportError:
        Success = False
        print('pygame not installed correctly; installing now')
        install(('-U', 'pygame', '--user'))

    try:
        import pyinputplus
    except ImportError:
        Success = False
        print('pyinputplus not installed correctly; installing now')
        install(('pyinputplus',))

    try:
        import PyQt5
    except ImportError:
        Success = False
        print('PyQt5 not installed correctly; installing now')
        install(('PyQt5',))

    try:
        import rich
    except ImportError:
        Success = False
        print('rich not installed correctly; installing now')
        install(('rich',))

    try:
        import screeninfo
    except ImportError:
        Success = False
        print('screeninfo not installed correctly; installing now')
        install(('screeninfo',))

    try:
        import traceback_with_variables
    except ImportError:
        Success = False
        print('traceback_with_variables not installed correctly; installing now')
        install(('traceback_with_variables',))

    return Success


print('Welcome to the easy-install script for Knock!\n\n')
print('Attempting install of required modules from requirements.txt...\n\n')


try:
    check_call([executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print('Installation successful; will now check the installation of each module in turn...')
except Exception as e:
    print(f'Error: \n\n{e}\n\n')
    print('Not all modules were installed correctly; will attempt to install each module one by one.')

print('\n\n')

Success = False

for i in range(5):
    if AllInstalled():
        Success = True
        break

print('\n\n')

if Success:
    print('All required modules have been successfully installed! You can now run Knock.py.')
else:
    print('Attempted installation was not successful for all completed modules :(')
