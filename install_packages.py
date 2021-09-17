"""Script to install all the required packages for this application to run."""

from typing import Sequence, NamedTuple
from subprocess import check_call
from sys import executable
from importlib import import_module


def pip_install(package_args: Sequence[str]) -> None:
    """Run pip as a subprocess in order to install a package according to a sequence of supplied arguments."""
    check_call([executable, "-m", "pip", "install", *package_args])


class PackageImportArgs(NamedTuple):
    """We attempt to import the package using the module name;
    then, if that fails, we use the arguments supplied in the `args` field
    to attempt installation of the package using pip.
    """

    module_name: str
    args: Sequence[str]

    def import_was_successful(self, /) -> bool:
        """Attempt to import a package. If that fails, attempt to pip install it.
        Return `True` if the initial import attempt was successful, else `False`.
        """

        try:
            import_module(self.module_name)
        except ModuleNotFoundError:
            pip_install(self.args)
            return False
        else:
            return True


INSTALLATION_ARGS = (
    PackageImportArgs(module_name='matplotlib', args=('matplotlib',)),
    PackageImportArgs(module_name='numpy', args=('numpy',)),
    PackageImportArgs(module_name='PIL', args=('--upgrade', 'pillow')),
    PackageImportArgs(module_name='pandas', args=('pandas',)),
    PackageImportArgs(module_name='Crypto', args=('pycryptodome',)),
    PackageImportArgs(module_name='pygame', args=('--U', 'pygame', '--user')),
    PackageImportArgs(module_name='pyinputplus', args=('pyinputplus',)),
    PackageImportArgs(module_name='PyQt5', args=('PyQt5',)),
    PackageImportArgs(module_name='rich', args=('rich',)),
    PackageImportArgs(module_name='screeninfo', args=('screeninfo',)),
    PackageImportArgs(module_name='traceback_with_variables', args=('traceback_with_variables',))
)


def install_packages() -> None:
    """Attempt to install packages from the requirements.txt file; go through packages one-by-one if that fails."""

    print('Welcome to the easy-install script for Knock!\n\n')
    print('Attempting install of required modules from requirements.txt...\n\n')

    try:
        pip_install(('-r', 'requirements.txt'))
        print('Installation successful; will now check the installation of each module in turn...')
    except Exception as e:
        print(f'Error: \n\n{e}\n\n')
        print('Not all modules were installed correctly; will attempt to install each module one by one.')

    print('\n\n')

    success = False

    for _ in range(5):
        if all(module.import_was_successful for module in INSTALLATION_ARGS):
            success = True
            break

    print('\n\n')

    if success:
        print('All required modules have been successfully installed! You can now run Knock.py.')
    else:
        print('Attempted installation was not successful for all completed modules :(')


if __name__ == '__main__':
    install_packages()
