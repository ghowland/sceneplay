#!/usr/bin/env python

import yaml
import time

import owr_log as log
from owr_log import Log
import owr_base
import owr_actor
import owr_image
from owr_util import YamlOpen
import owr_item
import owr_gfx


#TODO(g): Remove this hard coded string.  This should come in from the Game object
DATA_FILE = 'data/owr.yaml'


class Player(owr_actor.Actor):
  
  def __init__(self, game, name):
    raw_data = yaml.load(YamlOpen(DATA_FILE))
    #TODO(g): Unhard-code the default (actor.figter) player
    self.data = raw_data['actor.fighter']
    
    """Create the player, place it on the map."""
    self.game = game
    self.name = name
    
    
    starting_position = self.data['position']
    self.pos = owr_base.Position(starting_position[0], starting_position[1])
    self.pos_last = self.pos
    
    # Determine our assets, by going through all the asset sets, and loading
    #   their data on top of our our asset dictionary
    self.assets = {}
    for asset_set in self.data['asset_sets']:
      asset_set_name = 'asset_set.%s' % asset_set
      self.assets.update(raw_data[asset_set_name])
    
    # Get the animation frames for this animation
    self.images = owr_image.GetAnimationFrames(self.assets['stand'], self.game.data['window']['scale'])
    self.image_cur = 0
    self.image_updated = time.time()
    self.image = self.images[0]
    
    # Save any attributes we want specifically out of our data
    self.money = self.data.get('money', 0)
    
    # Create our attributes (need to make new field references)
    self.attributes = {}
    for key in self.data.get('attributes', {}):
      self.attributes[key] = self.data['attributes'][key]
    
    ## Create our items
    #self.items = []
    #for key in self.data.get('items', {}):
    #  item = owr_item.Item(self.game, self, self.data['items'][key])
    #  self.items.append(item)
    
    # Save the current health of the player
    if 'heath' in self.attributes:
      self.health_current = self.attributes['health']
    else:
      #NOTE(g): This makes the player alive.  Apparently health isnt important
      #   in this game...
      self.health_current = 1
    
    # Get the quests we start with
    #TODO(g): Make this a deep copy, so we arent changing the data we loaded
    self.quests = dict(self.data['quests'])
    
    # Save the current health of the player
    if 'mana' in self.attributes:
      self.mana_current = self.attributes['mana']
    else:
      #NOTE(g): Mana is not necessary, like health i
      self.mana_current = 0
    
    # More stats
    self.fatigued = False
    
    # Achievements
    self.achievements = {}

    # Input
    #TODO(g): Remove this later?  Or should NPCs have mach inputs to match
    #   real ones?  Think on it.
    self.input = None
    self.input_text = None
    self.input_history = [] # Keep 10 entries as history for moves
    
    self.action = 'stand'
    self.action_previous = 'stand'
    
    # Look RIGHT, by default
    self.look_direction = 1
    
    # Direction we are moving/facing
    self.direction = [1, 0]
    
    # Height off the ground (jumping/falling)
    self.vertical_height = 0
    # Acceleration off the ground
    self.vertical_accel = 0
    # If we launched off the ground (jumped, not falling), then this stays on
    #   until the JUMP action is released, or vertical_maximum has been reached
    self.vertical_launch_on = False
    self.vertical_maximum = 30


  def __repr__(self):
    output = 'Player: %s\n' % self.name
    output += '  Pos: %s\n' % self.pos
    #output += '  Money: %s\n' % self.money
    #output += '  Achievements\n    %s\n\n' % self.achievements.keys()
    #output += '  Quests:\n    %s\n\n' % self.quests.keys()
    output += '  Vertical: %s %s %s %s\n' % (self.vertical_height, self.vertical_accel, self.vertical_horiz_velocity, self.vertical_launch_on)
    
    #output += '  Items:\n'
    #for item in self.items:
    #  output += '%s\n\n' % str(item)
    
    return output
  
  
  def Update(self, ticks=0):
    """Update things about the character."""
    # Get the offset to draw this animation
    self.images = owr_image.GetAnimationFrames(self.assets[self.action], self.game.data['window']['scale'])
    if 'offset' in self.assets[self.action]:
      self.image_offset = self.assets[self.action]['offset']
    else:
      self.image_offset = [0, 0]
    
    # If its been more than 100ms
    if time.time() > self.image_updated + 0.1:
      # Increment the animation
      self.image_cur += 1
      self.image_updated = time.time()
      
      # If we are out of our images range, reset current
      if self.image_cur >= len(self.images):
        self.image_cur = 0
      
      # Select current image
      self.image = self.images[self.image_cur]
      self.image_flip = owr_gfx.Flip(self.images[self.image_cur], 1, 0)
    
    # Keep the last directional input stored, so we are always facing the
    #   way we last moved, horizontally.
    if self.direction[0] != 0:
      self.look_direction = self.direction[0]
    
    
    # If we have any vertical acceleration, use it
    if self.vertical_accel or self.vertical_height:
      # Apply vertical acceleration
      self.vertical_height += self.vertical_accel
      # Decellerate, and gravity
      self.vertical_accel -= 2
      # If we hit the floor, stop
      if self.vertical_height <= 0:
        self.vertical_height = 0
        #TODO(g): Check for ground collision speed/damage?  Noise?
        self.vertical_accel = 0
        self.vertical_launch_on = False
      # If we reached our maximum launch height, turn off the launch
      if self.vertical_launch_on and self.vertical_maximum < self.vertical_height:
        self.vertical_launch_on = False
      
      # Move horizontally
      self.Move(self.vertical_horiz_velocity, 0)
  
