from PIL import Image
from fractions import Fraction
from os import path, get_terminal_size, chdir


def ConvertImage(name, NewWidth):
	print(path.abspath(path.join('..', '..', 'Images', 'Suits', f'{name}.jpg')))
	im = Image.open(path.abspath(path.join('..', '..', 'Images', 'Suits', f'{name}.jpg'))).convert('1')
	ratio = Fraction(im.size[1], im.size[0]) * Fraction(55, 100)
	im = im.resize((NewWidth, int(NewWidth * ratio)))
	Ascii = ''.join((' ' if p else '@') for p in im.getdata())
	return [Ascii[i: i + NewWidth] for i in range(0, len(Ascii), NewWidth)]


def BufferSpace(Len):
	return ''.join(' ' for _ in range(Len))


def PrintSuits():
	try:
		width = get_terminal_size().columns
	except OSError:
		width = 140

	ImageWidth = width // 5

	Clubs, Diamonds, Hearts, Spades = [
		ConvertImage(string, ImageWidth) for string in ('Clubs', 'Diamonds', 'Hearts', 'Spades')
	]

	Len = (width - (ImageWidth * 4) // 5)

	for c, d, h, s in zip(Clubs, Diamonds, Hearts, Spades):
		print(''.join((
			BufferSpace(Len),
			c,
			BufferSpace(Len),
			d,
			BufferSpace(Len),
			h,
			BufferSpace(Len),
			s,
			BufferSpace(Len)
		)))

PrintSuits()