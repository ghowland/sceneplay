#!/usr/bin/env python

import yaml
import random

import owr_log
from owr_log import Log
import owr_base
import owr_image
import owr_item


class Actor:
  
  def __init__(self, game, data, name=None):
    """Create the actor, place it on the map."""
    self.game = game
    self.data = data
    if not name:
      self.name = data['name']
    else:
      self.name = name
    
    # Create our attributes (need to make new field references)
    self.attributes = {}
    for key in self.data.get('attributes', {}):
      self.attributes[key] = self.data['attributes'][key]
    
    ## Create items
    #self.items = []
    #for key in self.data.get('items', {}):
    #  item = owr_item.Item(self.game, self, self.data['items'][key])
    #  self.items.append(item)
    
    # Image
    self.image = owr_image.Load(data['image'],
                                colorkey=data.get('image_color_key',
                                game.data['game']['color_key']))
    
    # Set starting Position in environment
    starting_position = data['pos']
    self.pos = owr_base.Position(starting_position[0], starting_position[1])
    self.pos_last = self.pos
    
    # Save any data we need to manipulate
    self.money = data.get('money', 0)
    
    
    # More stats
    self.fatigued = False
    
    # Input
    #TODO(g): Remove this later?  Or should NPCs have mach inputs to match
    #   real ones?  Think on it.
    self.input = None
    self.input_text = None
    self.input_history = [] # Keep 10 entries as history for moves
    
    self.action = 'stand'
    self.action_previous = 'stand'
    
    # Direction we are moving/facing
    self.direction = [1, 0]
    self.direction_value = [0, 0]
    self.look_direction = 1
    
    # Height off the ground (jumping/falling)
    self.vertical_height = 0
    # Acceleration off the ground
    self.vertical_accel = 0
    # If we launched off the ground (jumped, not falling), then this stays on
    #   until the JUMP action is released, or vertical_maximum has been reached
    self.vertical_launch_on = False
    self.vertical_maximum = 100
    
    #Log('Actor data: %s' % self.data)


  def __repr__(self):
    output = 'Actor: %s\n' % self.name
    output += '  Pos: %s' % self.pos
    output += '  ---\n'
    
    keys = self.data.keys()
    keys.sort()
    for key in keys:
      output = '  %s: %s\n' % (key, self.data[key])
    
    output += '\n'
    
    return output


  def Update(self, ticks=0):
    """Actor AI"""
    if random.randint(0,5) == 0:
      x = random.randint(-1, 1)
      y = random.randint(-1, 1)
      self.Move(x, y)


  def ProcessInput(self, input):
    """Process the recorded input.
    
    TODO(g): Move this into a different module (Player probably), because Actor is more generic to AI and such that dont do this...  Network Players will also be different...
    """
    self.input = input
    
    # Update the values of the directions, which determine velocity or acceleration (depending on the move)
    self.direction_value = [input.joyDir[0], input.joyDir[1]]
    
    # Left
    if input.joyDir[0] < -0.2:
      # Up
      if input.joyDir[1] < -0.2:
        dir = 'left+up'
        self.direction = [-1, -1]
      # Down
      elif input.joyDir[1] > 0.2:
        dir = 'left+down'
        self.direction = [-1, 1]
      # Middle
      else:
        dir = 'left'
        self.direction = [-1, 0]
    
    # Right
    elif input.joyDir[0] > 0.2:
      # Up
      if input.joyDir[1] < -0.2:
        dir = 'right+up'
        self.direction = [1, -1]
      # Down
      elif input.joyDir[1] > 0.2:
        dir = 'right+down'
        self.direction = [1, 1]
      # Middle
      else:
        dir = 'right'
        self.direction = [1, 0]
    
    # Middle
    else:
      # Up
      if input.joyDir[1] < -0.2:
        dir = 'up'
        self.direction = [0, -1]
      # Down
      elif input.joyDir[1] > 0.2:
        dir = 'down'
        self.direction = [0, 1]
      # Middle
      else:
        dir = 'none'
        self.direction = [0, 0]
    
    
    # Buttons
    button = ''
    if input.joyButton[0] == 1:
      button += 'button1'
    if input.joyButton[1] == 1:
      if button:
        button += '+'
      button += 'button2'
    if input.joyButton[2] == 1:
      if button:
        button += '+'
      button += 'button3'
    if input.joyButton[8] == 1:
      if button:
        button += '+'
      button += 'buttonStart'
    
    # Create the total text
    text = dir
    if button:
      text += '+%s' % button
    
    # Save the text
    self.input_text = text
    if not self.input_history or self.input_history[-1] != text:
      self.input_history.append(text)
      
    # If there are more than TEN entries push the last one
    if len(self.input_history) > 10:
      self.input_history.remove(self.input_history[0])
    
    #Log('History: %s' % self.input_history)
    
    self.DetermineAction(dir, button)
    
    
    return text


  def DetermineAction(self, dir, button):
    """Inspect our self.input_history for a combo move."""
    history = self.input_history
    
    if history[-4:] == ['down', 'right+down', 'right', 'right+button1']:
      Log('COMBO: Right Fireball!')
      action = 'uppercut'
    elif history[-4:] == ['down', 'left+down', 'left', 'left+button1']:
      Log('COMBO: Left Fireball!')
      action = 'uppercut'
    # elif history[-3:] == ['left', 'none', 'left']:
    #   action = 'run'
    # elif history[-3:] == ['right', 'none', 'right']:
    #   action = 'run'
    elif 'button1+button2' in history[-1]:
      action = 'jump'
      
      # If the actor is currently standing, and they are not trying to GO up,
      #   then revert this to a stand.  No one wants to jump straight up normally,
      #   its a stupid thing to do.  But when pressing up, its ok.
      if self.action == 'stand' and self.direction[1] != -1:
          action = 'stand'
      
    elif 'button1' in history[-1]:
      action = 'punch'
    elif 'button2' in history[-1]:
      action = 'kick'
    elif dir != 'none':
      Log('X Input Value: %s' % self.direction_value[0])
      if self.direction_value[0] < 0.75 and self.direction_value[0] > -0.75:
        action = 'walk'
      else:
        action = 'run'
    else:
      # If we're running, keep running
      if self.action == 'run':
        action = 'run'
      else:
        action = 'stand'
    
    current_action = action
    
    # If the action changed
    just_started = False
    if action != self.action:
      change_allowed = True
      
      # If the actor is jumping...
      if self.action == 'jump':
        # If the actor is still launching, or his height isnt 0
        if self.vertical_height != 0 or self.vertical_launch_on == True:
          #TODO(g): Need to allow layered moves, like throws/punch/attacks while jumping, and still doing the launch control!  :)
          change_allowed = False
      
      # If this change is allowed, do it
      if change_allowed:
        Log('Action change: %s -> %s' % (self.action, action))
        self.action_previous = self.action
        self.action = action
        just_started = True
    
    # Perform our action
    self.PerformAction(just_started, current_action)


  def PerformAction(self, just_started, current_action):
    """Perform the action being requested of us.
    
    TODO(g): 
      - Remove hard-coded speeds.  They should move into YAML DATA...  Eventually into Box2d formatted acceleration
    """
    #TODO(g): Need to sync with time somewhere!
    if self.action == 'walk':
      x = self.input.joyDir[0] * 3.0
      y = self.input.joyDir[1] * 2.0
      
      self.Move(x, y)
    
    elif self.action == 'run':
      x = 5.0 * self.look_direction
      
      y = self.input.joyDir[1] * 3.0
      
      self.Move(x, y)
    
    elif self.action == 'jump':
      # Starting the jump
      if just_started:
        self.vertical_accel = 16
        self.vertical_launch_on = True
        
        # Was walking
        if self.action_previous == 'walk':
          self.vertical_horiz_velocity = 4.0 * self.look_direction
        # Was running
        elif self.action_previous == 'run':
          self.vertical_horiz_velocity = 5.0 * self.look_direction
        else:
          self.vertical_horiz_velocity = 0.0
      
      # Else, continuing jump
      else:
        
        # Slow down decelleration (launch-boost), or turn off the launch
        if current_action == 'jump' and self.vertical_launch_on:
          self.vertical_accel += 1
        elif self.vertical_launch_on:
          self.vertical_launch_on = False
        # Else, if we reached the ground, stand
        elif self.vertical_height == 0:
          if self.action_previous in ('run', 'walk'):
            self.action = self.action_previous
          else:
            self.action = 'stand'


  def Move(self, x, y):
    """x and y should be values between -1 and 1."""
    
    new_x = self.pos.x + x
    new_y = self.pos.y + y
    
    # Bound the position by the map size
    if new_x < 0:
      #TODO(g): If there is a door here, this is when it would trigger, or should doors be only by masks?  It makes sense to only allow masks to be doors
      new_x = 0
    
    if new_y < 0:
      new_y = 0
    
    #if new_x >= self.game.map.width:
    #TODO(g): Import information into Game object, and figure out dynamic method for margin, based on actor size.  AND SCALING!
    if new_x >= self.game.location_data['mask'].get_width()*3 - 1:
      new_x = self.game.location_data['mask'].get_width()*3 - 1
    
    #if new_y >= self.game.map.height:
    if new_y >= 410:
      new_y = 410
    
    # See if we can actually move to this new position
    #is_blocked = self.game.map.IsTileBlocked(new_x, new_y, self)
    is_blocked = False
    
    # Check with our terrain
    # Get the kind of terrain being touched now
    color = self.game.location_data['mask'].get_at((int(new_x/3), int(new_y/3)))
    index = self.game.location_data['mask'].map_rgb(color)
    #Log('Pos: %s  Color: %s  Index: %s' % (game.player.pos, color, index))
    terrain = self.game.location_data['assets']['background']['masks']['walkable']['palette'][index]
    if terrain not in ('walkable'):
      is_blocked = True
    
    
    if not is_blocked:
      # Save our last position
      self.pos_last = owr_base.Position(self.pos.x, self.pos.y)
      
      # Update our new position
      self.pos.x = new_x
      self.pos.y = new_y
      
      #Log('Moved to position: %s' % self.pos)
      
      # If this is the player, then do these
      if self == self.game.player:
        ## Check for Map features of this tile
        #self.game.map.ProcessPlayerTileMove()
        
        # After a move, ensure the map is positioned properly
        self.PostMove()


  def PostMove(self):
    """Update things about the character."""
  
  
  def GetScreenPos(self):
    """Returns the pixel position on the screen."""
    #screen_x = (self.pos.x - self.game.map.offset[0]) * \
    #            self.game.data['map']['tile_size']
    #screen_y = (self.pos.y - self.game.map.offset[1]) * \
    #            self.game.data['map']['tile_size']
    
    screen_x = self.pos.x
    screen_y = self.pos.y
    
    # Adjust screen position with the Game Camera offset
    screen_x += self.game.camera_offset[0]
    screen_y += self.game.camera_offset[1]
    
    return (screen_x, screen_y)
  

  def IsOffScreen(self):
    """Is the player off the screen?"""
    #tiles = self.game.map.GetTilesPerScreen()
    #
    #if self.pos.x < self.game.map.offset[0] or \
    #    self.pos.x > self.game.map.offset[0] + tiles[0]:
    #  Log('OFF X: Player: %s  Map: %s' % (self.pos, self.game.map.offset))
    #  return True
    #
    #if self.pos.y < self.game.map.offset[1] or \
    #    self.pos.y > self.game.map.offset[1] + tiles[1]:
    #  Log('OFF Y: Player: %s  Map: %s' % (self.pos, self.game.map.offset))
    #  return True
    return False


  def Pay(self, source_actor, target_actor, amount, reason=None):
    """Returns success of payment."""
    #TODO(g): Source actor should be this actor, should only need target.  FIX
    
    # If the source can pay, then pay
    if source_actor.money >= amount:
      source_actor.money -= amount
      target_actor.money += amount
      
      Log('%s pays %s %s: %s' % (source_actor.name, target_actor.name,
                                 amount, reason))
      return True
    
    # Else, log failure
    else:
      Log('%s FAILS to pay %s %s: %s' % (source_actor.name, target_actor.name,
                                         amount, reason))
      return False


  def ConditionCheck(self, condition):
    """Returns boolean."""
    value = None
    value_target = None
    
    # If it wants an attribute
    if 'attribute' in condition:
      value = self.attributes[condition['attribute']]
    else:
      Log('Actor: ConditionCheck: Unknown value type', status=owr_log.LEVEL_CRITICAL)
    
    # If it wants an attribute
    if 'target_attribute' in condition:
      value_target = self.attributes[condition['target_attributetribute']]
    
    
    # Condition
    if 'greater_than' in condition:
      # If this is a percentage, convert the percentage item
      if '%' in condition['greater_than']:
        percent = int(str(['greater_than']).replace('%', '')) * 0.01
        value_target *= percent
      
      # Compare the values
      if value > value_target:
        return True
      else:
        return False
    else:
      Log('Actor: ConditionCheck: Unknown condition check', status=owr_log.LEVEL_CRITICAL)
    
    
    # If it got here, it's set up wrong
    Log('Actor: ConditionCheck: No valid condition path', status=owr_log.LEVEL_CRITICAL)
    return False

