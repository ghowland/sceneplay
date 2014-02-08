"""
Rivers of Blood

(Formely code named: Ocean World Ransom)
"""


#core
import pygame
from pygame.locals import *
import time
import sys


import owr_log as log
from owr_log import Log
import owr_image
import owr_input

import yaml

import owr_game
import owr_timer
from owr_util import YamlOpen

import owr_screenplay_input


# Ocean World Ransom MEGA DATA FILE
#TODO(g): Break this bitch up!
GAME_DATA = 'data/sceneplay_000.yaml'
#GAME_DATA = 'data/defense.yaml'


class Core:
  """The core.  All non-game related functions wrapped here."""
  
  def __init__(self, title, size, data):
    """Initialize the core information."""
    self.title = title
    self.size = size
    self.data = data

    self.game = None
    
    Log('Creating core')
    
    # Initialize the Graphics stuff
    #NOTE(g): This creates self.screen
    owr_image.InitializeGraphics(self)
    
    # Create the background surface
    self.background = pygame.Surface(size)
    self.background = self.background.convert()
    
    # Create Input Handler
    self.input = owr_input.InputHandler()
    self.input_text = '' #TODO(g): Remove when full input mapper is finished...


  def Update(self, ticks=None):
    """Update everything"""
    self.game.Update(ticks=ticks)


  def HandleInput(self, game):
    """Handle input"""
    # Save the mouse position
    game.mouse.SetPos(pygame.mouse.get_pos())
    
    # Save the mouse button state (used for draw actions, use events for button
    #   down events (single fire))
    game.mouse.SetButtons(pygame.mouse.get_pressed())
    
    # Handle events through the Input Handler
    self.input.Update()
    
    #if self.input.GetAutoString():
    #  log.Log('Auto string: %s' % self.input.GetAutoString())
    
    entered_string = self.input.GetNewEnteredString()
    if entered_string:
      log.Log('Entered string: %s' % entered_string)
    
    #TODO(g): Create named input maps, which make the right function calls off
    #   of inputs.  Then we can switch which maps we're using as the game state
    #   changes, so for menus or playing or combat, or whatever.
    pass


    # Handle viewport selection UI
    #NOTE(g): Viewport selection comes in front of UI Popup because I made it so
    #   UI popup will set Viewport Select data to gagther that kind of data
    if getattr(game, 'ui_select_viewport', None) != None:
      owr_screenplay_input.HandleScreenplayViewportSelectInput(self, game)

    # Handle popup UI for Screenplay
    elif getattr(game, 'ui_popup_data', None) != None:
      owr_screenplay_input.HandleScreenplayPopupInput(self, game)

    # Else, handle normal input
    else:
      owr_screenplay_input.HandleScreenplayInput(self, game)

    
    # # Else, there is combat going on
    # elif game.combat:
    #   game.combat.HandleInput()
    
    # # Else, there is dialogue going on, handle that
    # elif game.dialogue:
    #   game.dialogue.HandleInput(self.input)
    
    
    # If they are closing the window
    if self.input.winClose:
      game.quitting = True
  
  
  def Render(self, game):
    """Handle input"""
    # Clear the screen
    self.background.fill((250, 250, 250))
    
    # Render the background
    game.Render(self.background)
    
    # Blit the background
    self.screen.blit(self.background, (0, 0))
    
    # Make background visible
    pygame.display.flip()


  def SetGame(self, game):
    self.game = game


def main(args=None):
  if not args:
    args = []

  global GAME_DATA
  data = yaml.load(YamlOpen(GAME_DATA))
  
  # Create the Data Core
  core = Core(data['window']['title'], data['window']['size'], data)
  
  # Create the game
  game = owr_game.Game(core, GAME_DATA, args=args)
  
  Log('Starting game...')
  while not game.quitting:
    owr_timer.LockFrameRate(60)
    core.Update()
    core.HandleInput(game)
    core.Render(game)
  
  Log('Quitting')


if __name__ == '__main__':
  main(sys.argv[1:])

