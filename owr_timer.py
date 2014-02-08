#!/usr/bin/env python

"""
RPG: Timer
"""

CLOCK = None

import pygame
  

def LockFrameRate(framerate=60):
  global CLOCK
  if not CLOCK:
    CLOCK = pygame.time.Clock()
  
  CLOCK.tick(framerate)


