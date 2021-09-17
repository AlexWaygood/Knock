"""This code adapted from a project by Adam Binks -- see his repo here: https://github.com/adam-binks/Fireworks"""


import math, random
from src.display.fireworks.firework_particle import FireworkParticle


class Firework:
    __slots__ = tuple()

    def __init__(self, pos, colour, velocity, particleSize, sparsity, hasTrail, lifetime, WindowDimensions):
        # sparsity is between 0 and 1, higher values mean fewer particles
        trailColour = [random.uniform(0, 255) for _ in range(3)]

        xDir = -0.5
        while xDir <= 0.5:
            yDir = -0.5
            while yDir <= 0.5:
                if xDir == yDir == 0:
                    continue
                if ((xDir * xDir) + (yDir * yDir)) <= (0.5 * 0.5):
                    FireworkParticle(
                        pos=pos,
                        colour=colour,
                        direction=[xDir, yDir],
                        velocity=velocity + random.uniform(-2, 2),
                        size=particleSize,
                        hasTrail=hasTrail,
                        lifetime=lifetime + random.uniform(-3, 3),
                        WindowDimensions=WindowDimensions,
                        shrink=True,
                        trailColour=trailColour
                    )
                yDir += sparsity
            xDir += sparsity


# Spawn particles on a proportion-sized segment of the edge of a circle, with centre and radius
class ShimmerFirework:
    __slots__ = tuple()

    accentChance = 0.2

    def __init__(self, centre, colour, velocity, particleSize, sparsity, radius, proportion,
                 focusRad, lifetime, WindowDimensions, weight):
        # sparsity lies between 0 and 1. Lower values = more particles
        # proportion lies between 0 and 1. Higher values = larger, more rounded nose of the shimmer firework
        # focusRad is the direction (in radians) the centre of the shimmer firework is facing

        # make a little firework too :)
        Firework(centre, self.darken(colour, 50), 20, particleSize * 3, sparsity, False, 5, WindowDimensions)

        accentColour = [colour[1], colour[2], colour[0]]  # accent is just the normal colour with RGBs mixed :)

        focus = [centre[0] + radius * math.sin(focusRad), centre[1] + radius * math.cos(focusRad)]

        y = centre[1] - radius/2.0

        while y < centre[1] + radius/2.0:
            # find the x coord of this y coord on the circle centred about centre
            result = radius*radius - math.pow(centre[1] - y, 2)
            x = centre[0] - math.sqrt(math.fabs(result)) * -(int(result < 0))

            # only spawn a particle if [x, y] is <= proportion*radius away from the focus
            if math.pow(x - focus[0], 2) + math.pow(y - focus[1], 2) <= math.pow(proportion*radius, 2):

                # is this an accent particle? if so use the accent colour
                if random.uniform(0, 1) < ShimmerFirework.accentChance:
                    col = accentColour
                else:
                    col = colour

                FireworkParticle(
                    pos=[x, y],
                    colour=col,
                    direction=self.getDir(x, y, focus[0], focus[1], radius, 0.4),
                    velocity=velocity,
                    size=particleSize,
                    lifetime=lifetime + random.uniform(-2, 10),
                    WindowDimensions=WindowDimensions,
                    shrink=True,
                    gravity=weight + random.uniform(-0.01, 0.01)
                )

            y += sparsity

    # find the [x, y] direction from [fx, fy] to [px, py]
    @staticmethod
    def getDir(px, py, fx, fy, r, rand):
        return [((px - fx)/r + random.uniform(-rand, rand))/3, ((py - fy)/r + random.uniform(-rand, rand))/3]

    @staticmethod
    def darken(colour, factor):
        newCol = []
        for i in range(len(colour)):
            newCol.append(colour[i] - factor)
            if newCol[i] < 0:
                newCol[i] = 0
        return newCol
