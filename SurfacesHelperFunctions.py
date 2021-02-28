from functools import lru_cache


@lru_cache
def BoardDimensionsHelper(SurfWidth, SurfHeight, CardX, CardY, NormalLinesize, PlayerNo):
	BoardFifth = SurfHeight // 5

	TripleLinesize = 3 * NormalLinesize
	TwoFifthsBoard, ThreeFifthsBoard = (BoardFifth * 2), (BoardFifth * 3)
	HalfCardWidth, DoubleCardWidth = (CardX // 2), (CardX * 2)

	PlayerTextPositions = [
		(CardX, int(TwoFifthsBoard - TripleLinesize)),
		((SurfWidth - CardX), int(TwoFifthsBoard - TripleLinesize))
	]

	# Top-left position & top-right position
	CardRectsOnBoard = [
		((CardX + HalfCardWidth), (PlayerTextPositions[0][1] - HalfCardWidth)),
		((SurfWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[1][1] - HalfCardWidth))
	]

	if PlayerNo != 2:
		BoardMid = SurfWidth // 2

		if PlayerNo != 4:
			# Top-middle position
			PlayerTextPositions.insert(1, (BoardMid, (NormalLinesize // 2)))
			CardRectsOnBoard.insert(1, (
				(BoardMid - HalfCardWidth), (PlayerTextPositions[1][1] + (NormalLinesize * 4))))

		if PlayerNo != 3:
			# Bottom-right position
			PlayerTextPositions.append(((SurfWidth - CardX), ThreeFifthsBoard))
			CardRectsOnBoard.append(
				((SurfWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[-1][1] - HalfCardWidth)))

			# Bottom-mid position
			if PlayerNo != 4:
				PlayerTextPositions.append((BoardMid, int(SurfHeight - (NormalLinesize * 5))))
				CardRectsOnBoard.append(
					((BoardMid - HalfCardWidth), (PlayerTextPositions[-1][1] - CardY - NormalLinesize)))

			# Bottom-left position
			if PlayerNo != 5:
				PlayerTextPositions.append((CardX, ThreeFifthsBoard))
				CardRectsOnBoard.append((DoubleCardWidth, (PlayerTextPositions[-1][1] - HalfCardWidth)))

	return CardRectsOnBoard, PlayerTextPositions


@lru_cache
def TrumpCardDimensionsHelper(GameX, CardX, CardY, NormalLinesize):
	return (GameX - (CardX + 50)), (CardX + 2), (CardY + int(NormalLinesize * 2.5) + 10), (1, int(NormalLinesize * 2.5))
