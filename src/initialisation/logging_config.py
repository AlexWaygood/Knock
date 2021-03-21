# This file imported by the server script and the client script

from logging import basicConfig, DEBUG, debug
from os import path
from src.misc import GetDate


# noinspection PyArgumentList
def LoggingConfig(ClientSide: bool):
	basicConfig(
		filename=path.join('DebugLogs', ("Client" if ClientSide else "Server"), f'{GetDate()}.txt'),
		level=DEBUG,
		format='{asctime}.{msecs:.0f} - {threadName} - {module} - Line {lineno} - {message}',
		datefmt='%H:%M:%S',
		style='{'
	)

	debug('\n\nNEW RUN OF PROGRAMME STARTING\n\n')
