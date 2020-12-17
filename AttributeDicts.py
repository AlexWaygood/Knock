from Player import Player


def TriggerDict():
	return {
		'GameInitialisation': 0,
		'RoundStart': 0,
		'NewPack': 0,
		'CardsDealt': 0,
		'TrickStart': 0,
		'TrickEnd': 0,
		'RoundEnd': 0,
		'PointsAwarded': 0,
		'WinnersAnnounced': 0,
		'TournamentLeaders': 0,
		'NewGameReset': 0
	}


def SurfaceIterationsDict():
	return {
		'Scoreboard': 0,
		'TrumpCard': 0,
		'Hand': 0,
		'CurrentBoard': 0,
	}


def TournamentAttributesDict(server=False, NumberOfPlayers=0):
	return {
		'GamesPlayed': 0,
		'TournamentLeaders': [],
		'MaxGamesWon': 0,
		'NumberOfPlayers': NumberOfPlayers,
		'MaxCardNumber': (51 // NumberOfPlayers) if server else 0,
		'gameplayers': Player.AllPlayers if server else []
	}


def GameAttributesDict():
	return {
		'StartCardNumber': 0,
		'Winners': [],
		'MaxPoints': 0
	}


def RoundAttributesDict():
	return {
		'RoundNumber': 1,
		'PackOfCards': [],
		'CardNumberThisRound': 0,
		'TrumpCard': None,
		'trumpsuit': '',
		'RoundLeader': None
	}


def TrickAttributesDict():
	return {
		'PlayedCards': [],
		'FirstPlayerIndex': 0,
		'TrickNumber': 0,
		'Winner': None,
		'WhoseTurnPlayerIndex': -1,
		'TrickInProgress': False
	}
