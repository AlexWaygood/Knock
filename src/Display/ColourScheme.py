from src.Display.Fireworks.FireworkVars import FireworkVars
from src.DataStructures import DictLike


# noinspection PyAttributeOutsideInit
class ColourScheme(DictLike):
	__slots__ = 'MenuScreen', 'Scoreboard', 'GamePlay', 'TextDefault'

	Black = (0, 0, 0)
	Maroon = (128, 0, 0)
	Silver = (128, 128, 128)
	LightGrey = (204, 204, 204)
	Black_fade = (0, 0, 0, FireworkVars.FadeRate)
	Orange = (255, 136, 0)

	def __init__(self, Theme: str):
		if Theme == 'Classic':
			self.MenuScreen = self.Silver
			self.Scoreboard = self.Silver
			self.GamePlay = self.Maroon
			self.TextDefault = self.Black
		else:
			self.MenuScreen = self.LightGrey
			self.Scoreboard = self.LightGrey
			self.GamePlay = self.Orange
			self.TextDefault = self.Black

	def __repr__(self):
		return '\n'.join((
			'Colour scheme for the game.',
			'\n-'.join(f'{name}: {self[name]}.' for name in ("MenuScreen", "Scoreboard", "GamePlay", "TextDefault")),
			'\n\n'
		))
