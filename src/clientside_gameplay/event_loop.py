from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from pygame import (quit as pg_quit,
                    locals as pg_locals)

from pygame.display import (get_init as pg_display_get_init,
                            get_surface as pg_display_get_surface)

from pygame.time import delay, get_ticks as GetTicks
from pygame.mouse import get_pressed as pg_mouse_get_pressed
from pygame.event import get as pg_event_get
from pygame.key import get_mods as pg_key_get_mods


if TYPE_CHECKING:
	from pygame.time import Clock
	from pygame.event import Event

	from src.special_knock_types import KeyTuple
	from src.game.client_game import ClientGame as Game
	from src.players.players_client import ClientPlayer as Player
	from src.network.netw_client import Client

	from src.display.display_manager import DisplayManager
	from src.display.mouse.mouse import Mouse, Scrollwheel
	from src.display.knock_surfaces.game import GameSurface
	from src.display.input_context import InputContext
	from src.display.text_input import TextInput
	from src.display.error_tracker import Errors
	from src.display.matplotlib_scoreboard import InteractiveScoreboard


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

	if mouse.click:
		if context.ClickToStart:
			game.TimeToStart()

		elif context.TrickClickNeeded and mouse.cursor == 'Hand' and player.PosInTrick == len(game.PlayedCards):
			game.ExecutePlay(mouse.CardHoverID, player.playerindex)


WindowResizeKeys = (pg_locals.K_ESCAPE, pg_locals.K_TAB)


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
		WindowResizeKeys: KeyTuple = WindowResizeKeys
):

	ControlKeyFunctions = {
		pg_locals.K_c: gamesurf.MoveToCentre,
		pg_locals.K_q: QuitGame,
		pg_locals.K_s: scoreboard.save,
		pg_locals.K_t: scoreboard.show,
		pg_locals.K_v: userInput.PasteEvent,
		pg_locals.K_BACKSPACE: userInput.ControlBackspaceEvent,
		pg_locals.K_PLUS: displayManager.ZoomIn,
		pg_locals.K_EQUALS: displayManager.ZoomIn,
		pg_locals.K_MINUS: displayManager.ZoomOut,
		pg_locals.K_UNDERSCORE: displayManager.ZoomOut
	}

	if (EvType := event.type) == pg_locals.QUIT:
		QuitGame()

	elif EvType == pg_locals.KEYDOWN:
		if scrollwheel.IsDown:
			scrollwheel.ComesUp()

		elif (EvKey := event.key) in WindowResizeKeys:
			displayManager.NewWindowSize(EvKey, ToggleFullscreen=True)

		elif ControlKeyDown():
			try:
				ControlKeyFunctions[EvKey]()
			except KeyError:
				KeyDownEvents(event, EvKey, context, gamesurf, client, game, userInput, player, errors)

		else:
			KeyDownEvents(event, EvKey, context, gamesurf, client, game, userInput, player, errors)

	elif EvType == pg_locals.VIDEORESIZE:
		displayManager.VideoResizeEvent(event.size)

	elif EvType == pg_locals.MOUSEBUTTONDOWN:
		Button = event.button

		# pushing the scrollwheel down will click the scrollwheel, no matter what else is going on
		if Button == 2:
			scrollwheel.clicked()

		# if the scrollwheel is down, any button on the mouse being pushed will cause it to come up.
		elif scrollwheel.IsDown:
			scrollwheel.ComesUp()

		# This only applies if it ISN'T  scrollwheel press and the scrollwheel is NOT currently down.
		elif not context.FireworksDisplay:
			if ControlKeyDown():
				if Button == 4:
					displayManager.ZoomIn()
				elif Button == 5:
					displayManager.ZoomOut()
				elif not client.ConnectionBroken and Button == 1 and not pg_mouse_get_pressed(5)[2]:
					mouse.click = True

			elif Button == 4:
				gamesurf.NudgeUp()

			elif Button == 5:
				gamesurf.NudgeDown()

			# Whether or not clicks are needed is tested in the Gameplay Loop function
			elif not client.ConnectionBroken and Button == 1 and not pg_mouse_get_pressed(5)[2]:
				mouse.click = True

	elif not context.FireworksDisplay:
		if EvType == pg_locals.MOUSEBUTTONUP:
			if (Button := event.button) == 1 and not client.ConnectionBroken:
				mouse.click = False
			elif Button == 2 and GetTicks() > scrollwheel.OriginalDownTime + 1000:
				scrollwheel.ComesUp()

		elif EvType == pg_locals.MOUSEMOTION and pg_mouse_get_pressed(5)[0] and pg_mouse_get_pressed(5)[2]:
			gamesurf.MouseMove(event.rel)


GameRematchKeys = (pg_locals.K_SPACE, pg_locals.K_RETURN)
ArrowKeys = (pg_locals.K_UP, pg_locals.K_DOWN, pg_locals.K_LEFT, pg_locals.K_RIGHT)


def KeyDownEvents(
		event: Event,
		EvKey: int,
		context: InputContext,
		gamesurf: GameSurface,
		client: Client,
		game: Game,
		userInput: TextInput,
		player: Player,
		errors: Errors,
		ArrowKeys: KeyTuple = ArrowKeys,
		GameRematchKeys: KeyTuple = GameRematchKeys
):

	ArrowKeyFunctions = {
		pg_locals.K_UP: gamesurf.NudgeUp,
		pg_locals.K_DOWN: gamesurf.NudgeDown,
		pg_locals.K_LEFT: gamesurf.NudgeLeft,
		pg_locals.K_RIGHT: gamesurf.NudgeRight
	}

	if not context.FireworksDisplay and EvKey in ArrowKeys:
		ArrowKeyFunctions[EvKey]()

	elif not client.ConnectionBroken:
		if context.GameReset and EvKey in GameRematchKeys:
			game.RepeatGame = True
			client.SendQueue.put('@1')
		elif EvKey == pg_locals.K_BACKSPACE:
			userInput.NormalBackspaceEvent()
		elif EvKey == pg_locals.K_RETURN:
			HandleTextInput(userInput.EnterEvent(), game, player, client, errors)
		else:
			userInput.AddTextEvent(event.unicode)


def HandleTextInput(
		Input,
		game: Game,
		player: Player,
		client: Client,
		errors: Errors
):
	if not Input:
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
