"""A smattering of short functions (and one variable) to make the script cleaner in various other files."""
from string import ascii_letters, digits, punctuation


PrintableCharacters = ''.join((digits, ascii_letters, punctuation))
PrintableCharactersPlusSpace = PrintableCharacters + ' '
