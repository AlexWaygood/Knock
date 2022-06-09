"""Configure logging options for the programme.

This module is imported by the client script and the server script.
"""

from logging import basicConfig, DEBUG, getLogger, NullHandler
from os import path
from src import get_date
import src.config as rc


def configure_logging(*, client_side: bool) -> None:
	"""Configure logging options for the programme.

	If this script is being run in Python, we log a lot of detail to a file.
	If, instead, this script is frozen, that means the script has been compiled using pyinstaller.

	In that eventuality, we don't do any logging at all,
	as it would be unexpected for another user to have files logged to their hard drive by a computer game.
	Instead, logging is circumvented by adding a `NullHandler` object to the logging configuration.

	Parameters
	----------
	client_side: bool
		`True` if this function is being run from the client script.
		`False` if this function is being run from the server script.
	"""

	if rc.FrozenState:
		getLogger(__name__).addHandler(NullHandler())
	else:
		# noinspection PyArgumentList
		basicConfig(
			filename=path.join('DebugLogs', ("Client" if client_side else "Server"), f'{get_date()}.txt'),
			level=DEBUG,
			format='{asctime}.{msecs:.0f} - {threadName} - {module} - Line {lineno} - {message}',
			datefmt='%H:%M:%s',
			style='{'
		)
