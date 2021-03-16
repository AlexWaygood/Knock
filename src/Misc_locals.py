"""A smattering of short functions (and one variable) to make the script cleaner in various other files."""
from string import ascii_letters, digits, punctuation
from time import strftime, localtime


PrintableCharacters = ''.join((digits, ascii_letters, punctuation))
PrintableCharactersPlusSpace = PrintableCharacters + ' '


def GetDate():
	return strftime("%d-%m-%Y", localtime())
