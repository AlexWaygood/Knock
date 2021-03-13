class FireworkVars:
	__slots__ = 'LastFirework', 'EndTime', 'RandomAmount'

	FadeRate = 3           # lower values mean fireworks fade out more slowly.
	FPS = 600              # Can lower this to lower the CPU usage of the fireworks display.
	SecondsDuration = 25   # The lower these two numbers, the more frequent fireworks will appear.
	Bounds = (0, 2500)     # The greater the gap between these two numbers, the more randomly...
									# ...the fireworks will be spaced.

	def __init__(self):
		self.LastFirework = 0
		self.EndTime = 0
		self.RandomAmount = 0

	def __repr__(self):
		return f'''FireworkVars object, keeps state of all firework-related variables. Current state:
FadeRate: {self.FadeRate}.
FPS: {self.FPS}.
SecondsDuration: {self.SecondsDuration}.
Bounds: {self.Bounds}.
LastFirework: {self.LastFirework}.
EndTime: {self.EndTime}.
RandomAmount: {self.RandomAmount}.
'''
