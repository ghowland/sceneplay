#!/usr/bin/env python

"""
OWR: Game

All the game related things work through this object.
"""

import os
import yaml

import owr_log as log
from owr_log import Log
import owr_render
import owr_base
import owr_image
import owr_screenplay
import owr_ui_control
from owr_util import YamlOpen

# Hacking in music here
import pygame


# Mapping of string to render laying function
RENDER_FUNCTIONS = {
  # Screen Playtime Renderer
  'Screenplay':owr_screenplay.Render,
  'Sidebar UI':owr_ui_control.RenderSidebarUI,
  'Bottombar UI':owr_ui_control.RenderBottombarUI,
  'Popup UI':owr_ui_control.RenderPopupUI,
  'Viewport UI':owr_ui_control.RenderViewportUI,

  # Game Render Functions
  'Game Background':owr_render.RenderBackground,
  'Game Draw Hint':owr_render.RenderMouseObstacle,
  #'Game Shadows':owr_render.RenderActors,
  #'Game Objects':owr_render.RenderActors,
  'Game Obstacles':owr_render.RenderMapObstacles,
  'Game Actors':owr_render.RenderActors,
  'Game Particles':owr_render.RenderParticles,
  #'Game Flying Actors':owr_render.RenderActors,
  'Game Speech':owr_render.RenderActorsSpeech,
  'Game UI':owr_render.RenderUI,
  'Game Pointer':owr_render.RenderPointer,

  # Mode Render Functions
  'Main Menu':owr_render.RenderMainMenu,
  'Leader Board':owr_render.RenderLeaderBoard,
  'Win Game':owr_render.RenderWinGame,
  'Lose Game':owr_render.RenderLoseGame,
  'Enter Name':owr_render.RenderEnterName,
  'Credits':owr_render.RenderCredits,
  'Intro':owr_render.RenderIntro,
}


class Mouse:
  def __init__(self):
    self.pos = [0, 0]
    self.buttons = [False, False, False]
  
  
  def SetPos(self, pos):
    self.pos = list(pos)
  
  
  def SetButtons(self, buttons):
    self.buttons = list(buttons)


class Game:
  """All things game related are stored here, as the central object."""
  
  def __init__(self, core, yaml_data, args=None):
    """Reset all the data."""
    self.core = core
    self.core.SetGame(self)
    
    # Data from the YAML file
    self.yaml_data = yaml_data
    self.data = yaml.load(YamlOpen(self.yaml_data))

    if not args:
      args = []
    self.args = args
    
    # Game Options
    self.options = {'music':True}

    if 'nomusic' in self.args:
      self.options['music'] = False

    # If we are interactive, even in render mode (forced), will not play through and stop
    if 'interactive' in self.args:
      self.render_interactive = True
    else:
      self.render_interactive = False
      

    if 'render' in self.args:
      self.options['render'] = True
    else:
      self.options['render'] = False

    # Create the mouse object
    self.mouse = Mouse()
    
    # Our map dictionary
    self.maps = {}
    
    # Save track being played to not restart it
    self.playing_music = None
    
    #TODO(g): Make map loading dynamic
    #self.map = owr_map.Map(self, MAP_HARDCODED)
    self.SelectLocation(self.data['game']['initial_location'])

    # We're just getting started!
    self.quitting = False
    
    # For the editor-cursor: mouse
    self.cursor_map_pos = owr_base.Position()
    
    # Player object goes here
    self.player = None
    
    # Save dialogue stuff going on.
    #TODO(g): This is cheating for having a game state stack, which I should do
    #   but will put off because it will take longer and I want NPC dialogue
    #   NOW!!!
    self.dialogue = None
    
    # When this list is non-null, the player and listed characters are battling
    self.combat = []
    
    # The game has one camera that focuses on the players in the game to keep
    #   edges of the world visible.  This offset tracks where the camera 
    #   moves so the background can be drawn accordingly
    self.camera_offset = [0, 0]

    # Time tracking
    self.ticks = 0


  def __repr__(self):
    output = 'Game:\n'
    
    output += '  ----\n'
    keys = self.data.keys()
    keys.sort()
    for key in keys:
      output += '  %s = %s' % (key, self.data[key])
    
    return output


  def Update(self, ticks=None):
    """Update the game state.  ticks are milliseconds since last updated."""
    self.ticks = ticks

    # Update the player, if they exist
    if self.data['game']['player_actor'] and self.player:
      self.player.Update(ticks=ticks)
    
    ## Update the map
    #self.map.Update(ticks=ticks)
    
    # Update the Camera
    self.UpdateCamera(ticks=ticks)

  
  def UpdateCamera(self, ticks=0):
    """Update the camera position, based on where the players are standing to
    give a good view of the edges of the background, as possible.
    """
    if self.data['game']['player_actor'] and self.player:
      player_screen_pos = self.player.GetScreenPos()
      
      #TODO(g): Dont hard code, look it up in the screen size
      if player_screen_pos[0] > 500:
        self.camera_offset[0] -= 10 #TODO(g): Use ticks to adjust distance scrolled
      elif player_screen_pos[0] < 100:
        self.camera_offset[0] += 10 #TODO(g): Use ticks to adjust distance scrolled
      
      # Determine the Max X Offset by scaling the enviornment width and the screen height
      SCREEN_HEIGHT = 640#TODO: Un-Hard code this
      SCALING = 3#TODO: Un-Hard code this
      if self.location_data['mask']:
        max_offset_x = -(self.location_data['mask'].get_width()*self.data['window']['scale'] - self.data['window']['size'][0])
      else:
        #TODO(g):PLACEHOLDER: This is totally not correct, just putting something in to avoid mask failure...
        max_offset_x = player_sceen_pos + self.data['window']['size'][0]
      
      # Constrain X, so it doesnt scroll where we dont have images
      if self.camera_offset[0] > 0:
        self.camera_offset[0] = 0
      # And so it doesnt scroll the too far the long way, also
      elif self.camera_offset[0] < max_offset_x:
        self.camera_offset[0] = max_offset_x
      
      #Log('Position: [%d, %d] (%d, %d)  {%d : %d}' % (player_screen_pos[0], player_screen_pos[1], self.player.pos[0], self.player.pos[1], self.camera_offset[0], max_offset_x))
  

  def Render(self, surface):
    """Render the game, layer by layer."""
    global RENDER_FUNCTIONS
    
    try:
      # Render all the layers for the location data render spec
      for layer_key in self.location_data['render']:
        #print RENDER_FUNCTIONS
        layer_function = RENDER_FUNCTIONS[layer_key]
        layer_function(self, surface)

        # If we're quitting, stop rendering things.  Something may go wrong.
        if self.quitting:
          break
    
    
      # If we dont have an output file, make it
      if not os.path.exists('output/output.png'):
        try:
          owr_image.Save(surface, 'output/output.png')
        except:
          # As a packaged application, this doesnt work.  Dont crash over it.
          pass
    
    # Skip this render pass if we just changed locations
    except owr_render.LocationChange, e:
      pass


  def SelectLocation(self, location_name):
    """Select the location we will be using."""
    # Ghetto reset global
    owr_render.TEMP_ACTORS = {}
    
    # Reload all our data
    self.data = yaml.load(YamlOpen(self.yaml_data))
    
    # -- End Ghetto Code --
    
    # Select the Location
    self.location = location_name

    Log('Adding game location: %s' % self.location)
    location_str = 'location.%s' % self.location
      
    self.location_data = self.data[location_str]
    Log('Added location data: %s' % self.location_data)
    
    #TODO(g): This is old, remove later  
    if 0:
      self.location_data['images'] = owr_image.GetAnimationFrames(self.location_data['assets']['background'], self.data['window']['scale'])
      self.location_data['image'] = self.location_data['images'][0]


    #self.location_data['image'] = owr_image.Load(self.location_data['images'][0], self.data['window']['scale'])
    
    # Log('  Image Series')
    # # Load images in a series, in case we have an animation (Win/Lose)
    # self.location_data['image_series'] = []
    # for image in self.location_data['images']:
    #   self.location_data['image_series'].append(owr_image.Load(image, self.data['window']['scale']))
    
    #TODO(g): This is old, remove later  
    # Load background mask
    if 0:
      Log('  Background Mask')
      
      if self.location_data['assets']['background']['masks']:
        self.location_data['mask'] = owr_image.Load(self.location_data['assets']['background']['masks']['walkable']['images'][0], convert=False, scale=self.data['window']['scale'])
      else:
        self.location_data['mask'] = None
    
    # Log('  Obstacles')
    
    # # Load all the obstacles
    # for (key, data) in self.location_data['obstacles'].items():
    #   data['image_data'] = owr_image.Load(data['image'], scale=self.data['window']['scale'])

    Log('Location Selected...')
    
    # # Load all the actor images
    # # Penguin - Small
    # for (key, data) in self.data['actor.penguin_small']['assets']['walk'].items():
    #   data['images_data'] = []
    #   for filename in data['images']:
    #     data['images_data'].append(owr_image.Load(filename, self.data['window']['scale'], flip_x=data['flip_horizontal']))

    # # Penguin - Medium
    # for (key, data) in self.data['actor.penguin_medium']['assets']['walk'].items():
    #   data['images_data'] = []
    #   for filename in data['images']:
    #     data['images_data'].append(owr_image.Load(filename, self.data['window']['scale'], flip_x=data['flip_horizontal']))

    # # Penguin - Boss
    # for (key, data) in self.data['actor.penguin_boss']['assets']['walk'].items():
    #   data['images_data'] = []
    #   for filename in data['images']:
    #     data['images_data'].append(owr_image.Load(filename, self.data['window']['scale'], flip_x=data['flip_horizontal']))
    
    # # Load all the Eskimo Throw animations
    # if 'eskimo_throw' in self.location_data['assets']:
    #   eskimo_throw_glob = "data/defense/actors/turret_eskimo_throw/EskimoSnowBall_*.png"
    #   import glob, os
    #   files = glob.glob(eskimo_throw_glob)
    #   for filename in files:
    #     filename_info = os.path.basename(filename).split('.')[0]
    #     (_, direction, frame) = filename_info.split('_')
    #     frame = int(frame) - 1
    #     # 16 frames
    #     angle = (270 + (int(direction) * 22)) % 360
    #     print '%s - %s' % (filename_info, angle)
    #     if angle not in self.location_data['assets']['eskimo_throw']['angles']:
    #       self.location_data['assets']['eskimo_throw']['angles'][angle] = {}

    #     # Load and cache the file
    #     self.location_data['assets']['eskimo_throw']['angles'][angle][frame] = owr_image.Load(filename, self.data['window']['scale'])
    
    # # If this location has music, play it
    # if 'music' in self.location_data:
    #   if self.playing_music != self.location_data['music']:
    #     print 'Stopping music'
    #     pygame.mixer.music.set_volume(0.0)
    #     pygame.mixer.music.stop()
      
    #   if self.location_data['music'] != None and self.playing_music != self.location_data['music']:
    #     print 'Playing song: %s' % self.location_data['music']
    #     self.playing_music = self.location_data['music']
    #     pygame.mixer.music.load(self.location_data['music'])
    #     pygame.mixer.music.set_volume(1.0)
    #     pygame.mixer.music.play(1)


