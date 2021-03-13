from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from pygame import key
from pygame.time import get_ticks as GetTicks


def QuitGame():
	pg.quit()
	raise Exception('Game has ended.')


def GameplayLoop(clock, game, client, dM, mouse, gamesurf, context, userInput, scrollwheel, errors, player):
	"""
	@type clock: pygame.time.Clock
	@type game: src.Game.ClientGame.ClientGame
	@type client: src.Network.Client.Client
	@type dM: src.Display.DisplayManager.DisplayManager
	@type mouse: src.Mouse.Mouse.Mouse
	@type gamesurf: src.Display.KnockSurfaces.GameSurf.GameSurface
	@type context: src.Display.InputContext.InputContext
	@type userInput: src.Display.TextInput.TextInput
	@type scrollwheel: src.Mouse.Mouse.Scrollwheel
	@type errors: src.Display.ErrorTracker.Errors
	@type player: src.Players.ClientPlayers.ClientPlayer
	"""

	clock.tick(100)
	Condition = (len(game.gameplayers) != game.PlayerNumber and game.StartPlay)

	if Condition or not pg.display.get_init() or not pg.display.get_surface():
		QuitGame()

	if client.LastUpdate < pg.time.get_ticks() - 10000:
		pg.mouse.set_cursor(pg.SYSTEM_CURSOR_WAIT)
		pg.display.set_caption('LOST CONNECTION WITH THE SERVER.')

		for event in pg.event.get():
			if event.type == pg.QUIT or (event.type == pg.KEYDOWN and (pg.key.get_mods() & pg.KMOD_CTRL)):
				QuitGame()

		pg.display.update()
		pg.time.delay(500)
		return None

	dM.Update()
	mouse.click = False

	for event in pg.event.get():
		HandleEvent(event, dM, gamesurf, context, game, client, userInput, mouse, scrollwheel, errors, player)

	if context.ClicksNeeded() and mouse.click:
		HandleClicks(context, game, client, player, mouse)


def HandleEvent(event, displayManager, gamesurf, context, game, client, userInput, mouse, scrollwheel, errors, player):
	"""
	@type event: pygame.event.Event
	@type displayManager: src.Display.DisplayManager.DisplayManager
	@type gamesurf: src.Display.KnockSurfaces.GameSurf.GameSurface
	@type context: src.Display.InputContext.InputContext
	@type game: src.Game.ClientGame.ClientGame
	@type client: src.Network.ClientClass.Client
	@type userInput: src.Display.TextInput.TextInput
	@type mouse: src.Display.Mouse.Mouse.Mouse
	@type scrollwheel: src.Display.Mouse.Mouse.Scrollwheel
	@type errors: src.Display.ErrorTracker.Errors
	@type player: src.Players.ClientPlayers.ClientPlayer
	"""

	if (EvType := event.type) == pg.QUIT:
		QuitGame()

	elif EvType == pg.KEYDOWN:
		if (EvKey := event.key) == pg.K_TAB or (EvKey == pg.K_ESCAPE and displayManager.Fullscreen):
			displayManager.NewWindowSize(ToggleFullscreen=True)

		elif key.get_mods() & pg.KMOD_CTRL:
			if EvKey == pg.K_q:
				QuitGame()

			elif EvKey == pg.K_t and game.StartPlay and not context.FireworksDisplay:
				game.gameplayers.Scoreboard.show()

			elif EvKey == pg.K_c:
				gamesurf.MoveToCentre()

			elif EvKey in (pg.K_PLUS, pg.K_MINUS):
				displayManager.ZoomWindow(EvKey)

		elif context.GameReset and EvKey in (pg.K_SPACE, pg.K_RETURN):
			game.RepeatGame = True
			client.SendQueue.put('@1')

		elif not context.FireworksDisplay and EvKey in (pg.K_UP, pg.K_DOWN, pg.K_RIGHT, pg.K_LEFT):
			gamesurf.ArrowKeyMove(EvKey)

		elif context.TypingNeeded:
			AddInputText(event, game, player, client, errors, userInput)

	elif EvType == pg.VIDEORESIZE:
		displayManager.VideoResizeEvent(event)

	elif EvType == pg.MOUSEBUTTONDOWN:
		Button = event.button

		if Button == 1 and context.ClicksNeeded() and not pg.mouse.get_pressed(5)[2]:
			mouse.click = True

		elif Button == 2 and not context.FireworksDisplay:
			scrollwheel.clicked(pg.mouse.get_pos(), GetTicks())

		elif Button in (4, 5):
			if key.get_mods() & pg.KMOD_CTRL:
				displayManager.ZoomWindow(Button)
			elif not context.FireworksDisplay:
				gamesurf.ArrowKeyMove(pg.K_UP if Button == 4 else pg.K_DOWN)

	elif not context.FireworksDisplay:
		if EvType == pg.MOUSEBUTTONUP:
			if (Button := event.button) == 1:
				mouse.click = False
			elif Button == 2 and GetTicks() > scrollwheel.OriginalDownTime + 1000:
				scrollwheel.IsDown = False

		elif EvType == pg.MOUSEMOTION and pg.mouse.get_pressed(5)[0] and pg.mouse.get_pressed(5)[2]:
			gamesurf.MouseMove(event.rel)


def AddInputText(event, game, player, client, errors, userInput):
	"""
	@type event: pygame.event.Event
	@type game: src.Game.ClientGame.ClientGame
	@type player: src.Players.ClientPlayers.ClientPlayer
	@type client: src.Network.ClientClass.Client
	@type errors: src.Display.ErrorTracker.Errors
	@type userInput: src.Display.TextInput.TextInput
	"""

	if not (Input := userInput.AddInputText(event)):
		return None

	if isinstance(player.name, int):
		if len(Input) < 30:
			# Don't need to check that letters are ASCII-compliant;
			# wouldn't have been able to type them if they weren't.
			player.name = Input
			client.SendQueue.put(f'@P{Input}')
		else:
			errors.ThisPass.append('Name must be <30 characters; please try again.')

	elif not (game.StartCardNumber or player.playerindex):
		# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
		try:
			assert 1 <= float(Input) <= game.MaxCardNumber and float(Input).is_integer()
			game.StartCardNumber = int(Input)
			client.SendQueue.put(f'@N{Input}')
		except:
			errors.ThisPass.append(f'Please enter an integer between 1 and {game.MaxCardNumber}')

	elif player.Bid == -1:
		# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
		Count = len(player.Hand)

		try:
			assert 0 <= float(Input) <= Count and float(Input).is_integer()
			game.PlayerMakesBid(Input, player.playerindex)
			client.SendQueue.put(''.join((f'@B', f'{f"{Input}" : 0>2}', f'{player.playerindex}')))
		except:
			errors.ThisPass.append(f'Your bid must be an integer between 0 and {Count}.')


def HandleClicks(context, game, client, player, mouse):
	"""
	@type context: src.Display.InputContext.InputContext
	@type game: src.Game.ClientGame.ClientGame
	@type client: src.Network.ClientClass.Client
	@type player: src.Players.ClientPlayer.ClientPlayer
	@type mouse: src.Display.Mouse.Mouse.Mouse
	"""

	if context.ClickToStart:
		game.StartPlay = True
		client.SendQueue.put('@S')

	elif mouse.cursor == 'Hand' and player.PosInTrick == len(game.PlayedCards):
		game.ExecutePlay(mouse.CardHoverID, player.playerindex)
		client.SendQueue.put(f'@C{mouse.CardHoverID}{player.playerindex}')
