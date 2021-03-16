from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from pygame import quit as pg_quit
from pygame import locals as pg_locals

from pygame.display import get_init as pg_display_get_init
from pygame.display import get_surface as pg_display_get_surface

from pygame.mouse import get_pressed as pg_mouse_get_pressed
from pygame.time import delay, get_ticks as GetTicks
from pygame.event import get as pg_event_get
from pygame.key import get_mods as pg_key_get_mods


if TYPE_CHECKING:
	from pygame.time import Clock
	from pygame.event import Event

	from src.special_knock_types import KeyTuple
	from src.game.client_game import ClientGame as Game
	from src.players.players_client import ClientPlayer as Player
	from src.network.client_class import Client

	from src.display.display_manager import DisplayManager
	from src.display.mouse.mouse import Mouse, Scrollwheel
	from src.display.knock_surfaces.game_surf import GameSurface
	from src.display.input_context import InputContext
	from src.display.text_input import TextInput
	from src.display.error_tracker import Errors
	from src.display.interactive_scoreboard import InteractiveScoreboard


log = getLogger(__name__)


def QuitGame():
	log.debug('Quitting game.')
	pg_quit()
	raise Exception('Game has ended.')


def ControlKeyDown():
	return pg_key_get_mods() & pg_locals.KMOD_CTRL


def GameplayLoop(
		clock: Clock,
		game: Game,
		client: Client,
		dM: DisplayManager,
		mouse: Mouse,
		gamesurf: GameSurface,
		context: InputContext,
		userInput: TextInput,
		scrollwheel: Scrollwheel,
		errors: Errors,
		player: Player,
		scoreboard: InteractiveScoreboard
):

	clock.tick(100)
	Condition = (len(game.gameplayers) != game.PlayerNumber and game.StartPlay)

	if Condition or not pg_display_get_init() or not pg_display_get_surface():
		QuitGame()

	dM.Update()
	mouse.click = False

	for event in pg_event_get():
		HandleEvent(event, dM, gamesurf, context, game, client, userInput, mouse, scrollwheel, errors, player, scoreboard)

	if client.ConnectionIsBroken():
		delay(500)
		return None

	if context.ClicksNeeded() and mouse.click:
		HandleClicks(context, game, client, player, mouse)


WindowResizeKeys = (pg_locals.K_ESCAPE, pg_locals.K_TAB)
GameRematchKeys = (pg_locals.K_SPACE, pg_locals.K_RETURN)


def HandleEvent(
		event: Event,
		displayManager: DisplayManager,
		gamesurf: GameSurface,
		context: InputContext,
		game: Game,
		client: Client,
		userInput: TextInput,
		mouse: Mouse,
		scrollwheel: Scrollwheel,
		errors: Errors,
		player: Player,
		scoreboard: InteractiveScoreboard,
		WindowResizeKeys: KeyTuple = WindowResizeKeys,
		GameRematchKeys: KeyTuple = GameRematchKeys
):

	ControlKeyFunctions = {
		pg_locals.K_q: QuitGame,
		pg_locals.K_c: gamesurf.MoveToCentre,
		pg_locals.K_s: scoreboard.save,
		pg_locals.K_t: scoreboard.show,
		pg_locals.K_PLUS: displayManager.ZoomIn,
		pg_locals.K_EQUALS: displayManager.ZoomIn,
		pg_locals.K_MINUS: displayManager.ZoomOut,
		pg_locals.K_UNDERSCORE: displayManager.ZoomOut
	}

	ArrowKeyFunctions = {
		4: gamesurf.NudgeUp,
		5: gamesurf.NudgeDown,
		pg_locals.K_UP: gamesurf.NudgeUp,
		pg_locals.K_DOWN: gamesurf.NudgeDown,
		pg_locals.K_LEFT: gamesurf.NudgeLeft,
		pg_locals.K_RIGHT: gamesurf.NudgeRight
	}

	if (EvType := event.type) == pg_locals.QUIT:
		QuitGame()

	elif EvType == pg_locals.KEYDOWN:
		if (EvKey := event.key) in WindowResizeKeys:
			displayManager.NewWindowSize(EvKey, ToggleFullscreen=True)

		elif ControlKeyDown():
			if EvKey in (pg_locals.K_BACKSPACE, pg_locals.K_v):
				AddInputText(event, context, game, player, client, errors, userInput)
			else:
				try:
					ControlKeyFunctions[EvKey]()
				except KeyError:
					pass

		elif not context.FireworksDisplay:
			try:
				ArrowKeyFunctions[EvKey]()
			except KeyError:
				pass

		elif not client.ConnectionBroken:
			if context.GameReset and EvKey in GameRematchKeys:
				game.RepeatGame = True
				client.SendQueue.put('@1')
			else:
				AddInputText(event, context, game, player, client, errors, userInput)

	elif EvType == pg_locals.VIDEORESIZE:
		displayManager.VideoResizeEvent(event.size)

	elif EvType == pg_locals.MOUSEBUTTONDOWN:
		Button = event.button

		if Button == 3 and scrollwheel.IsDown:
			scrollwheel.ComesUp()

		elif ControlKeyDown():
			if scrollwheel.IsDown:
				scrollwheel.ComesUp()
			elif Button == 4:
				displayManager.ZoomIn()
			elif Button == 5:
				displayManager.ZoomOut()

		elif Button > 3:
			if scrollwheel.IsDown:
				scrollwheel.ComesUp()
			elif not context.FireworksDisplay:
				ArrowKeyFunctions[Button]()

		elif not context.FireworksDisplay and not client.ConnectionBroken:
			if Button == 1:
				if scrollwheel.IsDown:
					scrollwheel.ComesUp()
				elif context.ClicksNeeded() and not pg_mouse_get_pressed(5)[2]:
					mouse.click = True

			elif Button == 2:
				scrollwheel.clicked()

	elif not context.FireworksDisplay:
		if EvType == pg_locals.MOUSEBUTTONUP:
			if (Button := event.button) == 1 and not client.ConnectionBroken:
				mouse.click = False
			elif Button == 2 and GetTicks() > scrollwheel.OriginalDownTime + 1000:
				scrollwheel.ComesUp()

		elif EvType == pg_locals.MOUSEMOTION and pg_mouse_get_pressed(5)[0] and pg_mouse_get_pressed(5)[2]:
			gamesurf.MouseMove(event.rel)


def AddInputText(
		event: Event,
		context: InputContext,
		game: Game,
		player: Player,
		client: Client,
		errors: Errors,
		userInput: TextInput
):
	if not context.TypingNeeded:
		return None

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


def HandleClicks(
		context: InputContext,
		game: Game,
		client: Client,
		player: Player,
		mouse: Mouse
):

	if context.ClickToStart:
		game.StartPlay = True
		client.SendQueue.put('@S')

	elif mouse.cursor == 'Hand' and player.PosInTrick == len(game.PlayedCards):
		game.ExecutePlay(mouse.CardHoverID, player.playerindex)
		client.SendQueue.put(f'@C{mouse.CardHoverID}{player.playerindex}')
