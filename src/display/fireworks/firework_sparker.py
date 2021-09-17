"""The code in this file was adapted from code by Adam Binks (https://github.com/adam-binks/Fireworks)"""

import random, math
from src.display.fireworks.firework import Firework, ShimmerFirework
# noinspection PyUnresolvedReferences
from src import pre_pygame_import
import pygame as pg


class FireworkSparker:
    __slots__ = 'targetPos', 'fwVelocity', 'particleSize', 'sparsity', 'hasTrail', 'isShimmer', 'fwLifetime', 'radius',\
                'focusRad', 'WindowDimensions', 'proportion', 'weight', 'pos', 'direction', 'velocity', 'surface', \
                'colour'

    size = 3
    startVelocity = 100
    minVelocity = 0
    gravityPower = 5

    allSparkers = []

    def __init__(self, pos, colour, velocity, particleSize, sparsity, hasTrail, lifetime, WindowDimensions,
                 isShimmer=False, radius=0, proportion=0, focusRad=0, weight=0) -> None:
        # store firework attributes
        self.targetPos = pos
        self.colour = colour
        self.fwVelocity = velocity
        self.particleSize = particleSize
        self.sparsity = sparsity
        self.hasTrail = hasTrail
        self.fwLifetime = lifetime
        self.isShimmer = isShimmer
        self.radius = radius
        self.proportion = proportion
        self.focusRad = focusRad
        self.WindowDimensions = WindowDimensions
        self.weight = weight

        # setup sparker to fly in direction of cursor
        self.pos = [random.uniform(WindowDimensions[0] * 1/3, WindowDimensions[0] * 2/3),
                    WindowDimensions[1]]
        rad = math.atan2(self.targetPos[1] - self.pos[1], self.targetPos[0] - self.pos[0])
        self.direction = [math.cos(rad), math.sin(rad)]
        self.velocity = FireworkSparker.startVelocity

        self.surface = pg.Surface((FireworkSparker.size, FireworkSparker.size))
        self.surface.fill(FireworkSparker.colour)

        FireworkSparker.allSparkers.append(self)

    def update(self, dt):
        # move
        for axis in (0, 1):
            self.pos[axis] += self.direction[axis] * self.velocity * dt

        # gravity acts
        self.velocity -= FireworkSparker.gravityPower * dt

        # if above target y or going slowly, time to detonate
        if self.pos[1] <= self.targetPos[1] or self.velocity < FireworkSparker.minVelocity:
            self.detonate()

    def draw(self, screen):
        screen.blit(self.surface, self.pos)

    def detonate(self):
        # create the firework object
        if self.isShimmer:
            ShimmerFirework(self.pos, self.colour, self.velocity, self.particleSize, self.sparsity,
                            self.radius, self.proportion, self.focusRad, self.fwLifetime, self.WindowDimensions,
                            self.weight)
        else:
            Firework(self.pos, self.colour, self.fwVelocity, self.particleSize,
                     self.sparsity, self.hasTrail, self.fwLifetime, self.WindowDimensions)

        # destroy the sparker
        FireworkSparker.allSparkers.remove(self)