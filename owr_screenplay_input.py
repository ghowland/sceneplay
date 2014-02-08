import time
import os
import yaml

import pygame

from pygame.locals import *


import owr_screenplay
import owr_behavior



def HandleScreenplayViewportSelectInput(self, game):
  """Extending out Core's input handler"""
  # If they hit ESC, clear selection
  if self.input.IsKeyDown(K_ESCAPE, once=True):
    game.ui_select_viewport = None
    print 'Quit Select Viewport'

  rect = pygame.Rect([0, 0], game.core.data['window']['viewport size'])
  if rect.collidepoint(self.input.mousePos) and self.input.mouseButtons[0] == self.input.ticks:
    print 'Viewport Select: %s: %s' % (str(self.input.mousePos), game.ui_select_viewport)

    # If we are selection position for a Actor's data keys
    if game.ui_select_viewport['action'] == 'select position':
      current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
      actor = game.ui_select_viewport['data'][0]
      actor_data = current_state['actors'][actor]
      key = game.ui_select_viewport['data'][1]

      #TODO(g): Convert to World Coordinates, not just Screen Coords, this is WRONG!
      actor_data[key] = list(self.input.mousePos)

      # Clear this selection - Leads to double hitting ESC which cancels stuff
      game.ui_select_viewport = None

      # Regenerate Timeline
      owr_screenplay.RegenerateTimeline(game)

      print 'Selected Actor Pos: %s: %s: %s' % (actor, key, actor_data[key])

    # Else, if a Goal Key that needs Viewport Select, 
    elif game.ui_select_viewport['action'] in ('add goal key', 'edit goal key'):
      # Change the Actor data
      current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
      actor_data = current_state['actors'][game.ui_select_viewport['actor']]

      # Set the goal key value to the Viewport Pos
      actor_data['goal'][game.ui_select_viewport['goal_number']][game.ui_select_viewport['key']] = list(self.input.mousePos)

      # If this is a primary key, set all the default keys if they dont already exist
      if game.ui_select_viewport['key'] in owr_behavior.GOAL_KEYS:
        if game.ui_select_viewport['key'] in owr_behavior.GOAL_DEFAULTS:
          for (goal_key, default_value) in owr_behavior.GOAL_DEFAULTS[game.ui_select_viewport['key']].items():
            # If we dont already have this goal key, set the default value
            if goal_key not in actor_data['goal'][game.ui_select_viewport['goal_number']]:
              actor_data['goal'][game.ui_select_viewport['goal_number']][goal_key] = default_value


      # Clear the Viewport and popup UI - We did everything here
      game.ui_select_viewport = None
      game.ui_popup_data = None

      # Regenerate Timeline
      owr_screenplay.RegenerateTimeline(game)

    elif game.ui_select_viewport['action'] == 'position camera':
      # # Render any Camera Rects, if we arent using the camera view
      # if state['cameras'] and not game.use_camera_view:
      #   camera = state['cameras'][0]

      # Populate first position
      if game.ui_select_viewport['first'] == None:
        game.ui_select_viewport['first'] = list(self.input.mousePos)

      # Populate second position and save
      elif game.ui_select_viewport['second'] == None:
        game.ui_select_viewport['second'] = list(self.input.mousePos)

        # Determine the rect position and size
        





def HandleScreenplayPopupInput(self, game):
  """Extending out Core's input handler"""
  # If they hit ESC, clear the popup
  if self.input.IsKeyDown(K_ESCAPE, once=True):
    game.ui_popup_data = None
    print 'Quit Select Viewport'

  # If we have Input Targets (UI)
  if hasattr(game, 'input_targets'):
    for input_target in game.input_targets:
      rect = pygame.Rect(input_target['pos'], input_target['size'])
      if rect.collidepoint(self.input.mousePos) and self.input.mouseButtons[0] == self.input.ticks:
        print '%s: %s' % (input_target['action'], input_target['data'])

        # Else, if we are trying to edit a goal key
        if input_target['action'] == 'add goal key:select:key':
          game.ui_popup_data['key'] = input_target['data']
          game.ui_popup_data['prompt'] = 'Enter Key Value: %s' % game.ui_popup_data['key']



def HandleScreenplayInput(self, game):
  """Extending out Core's input handler"""
  MOVE_ONCE = False

  # Clear any hover over, as we dont know of any so far
  game.ui_hover_over_button = None

  # If we have Input Targets (UI)
  if hasattr(game, 'input_targets'):
    for input_target in game.input_targets:
      rect = pygame.Rect(input_target['pos'], input_target['size'])

      # Hovered over, but not clicked
      if rect.collidepoint(self.input.mousePos) and self.input.mouseButtons[0] != self.input.ticks:
        print 'Hover over: %s' % input_target['name']
        game.ui_hover_over_button = input_target['name']

      # Else, if clicked button
      elif rect.collidepoint(self.input.mousePos) and self.input.mouseButtons[0] == self.input.ticks:
        print '%s: %s' % (input_target['action'], input_target['data'])

        # If we are selecting an actor, toggle
        if input_target['action'] == 'select actor':
          # If we dont have this yet, add it
          if input_target['name'] not in game.ui_selected_actors:
            game.ui_selected_actors.append(input_target['name'])
          else:
            game.ui_selected_actors.remove(input_target['name'])

        # Else, if we are trying to delete an actor
        elif input_target['action'] == 'delete actor':
          current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
          del current_state['actors'][input_target['data']]

          # Regenerate Timeline
          owr_screenplay.RegenerateTimeline(game)

        # Else, if we are trying to delete a goal key
        elif input_target['action'] == 'delete goal key':
          current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
          actor = input_target['data'][0]
          goal_number = input_target['data'][1]
          goal_key = input_target['data'][2]
          del current_state['actors'][actor]['goal'][goal_number][goal_key]

          # Regenerate Timeline
          owr_screenplay.RegenerateTimeline(game)

        # Else, if we are trying to delete a goal
        elif input_target['action'] == 'delete goal':
          current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
          actor = input_target['data'][0]
          goal_number = input_target['data'][1]
          del current_state['actors'][actor]['goal'][goal_number]

          # Regenerate Timeline
          owr_screenplay.RegenerateTimeline(game)

        # Else, if we are trying to add a goal key
        elif input_target['action'] == 'add goal key':
          # Clear the string, so we can get it
          game.core.input.ClearAutoString()

          # Create UI Popup information, to create a popup input display
          actor = input_target['data'][0]
          goal_number = input_target['data'][1]
          game.ui_popup_data = {'action':input_target['action'], 'prompt':'Select Goal:', 'actor':actor, 'goal_number':goal_number, 'key':None, 'value':None}

        # Else, if we are trying to add a goal
        elif input_target['action'] == 'add goal':
          # Clear the string, so we can get it
          game.core.input.ClearAutoString()

          # Add a new goal - No need to RegenerateTime() because it doesnt do anything yet
          current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
          actor = input_target['data']
          # Insert empty goal dict
          current_state['actors'][actor]['goal'].append({})

        # Else, if we are trying to edit a goal key
        elif input_target['action'] == 'edit goal key':
          # Clear the string, so we can get it
          game.core.input.ClearAutoString()

          # Set the auto-string to the current value
          print 'Setting initial string: %s' % str(input_target['data'][3])
          game.core.input.autoKeyString = str(input_target['data'][3])

          prompt = 'Enter Key Value: %s' % input_target['data'][2]

          # Create UI Popup information, to create a popup input display
          game.ui_popup_data = {'action':input_target['action'], 'prompt':prompt, 'actor':input_target['data'][0], 'goal_number':input_target['data'][1], 'key':input_target['data'][2], 'value':None}

          # # Regenerate Timeline
          # owr_screenplay.RegenerateTimeline(game)

        # Else, if we are trying to edit a goal key
        elif input_target['action'] == 'select position':
          print 'Select Viewport Position'
          # Set the UI Select Viewport data, so that this input mode enages
          game.ui_select_viewport = input_target
  
  # If there is a player playing, let them process the input
  if game.player:
    input_text = game.player.ProcessInput(self.input)
    self.input_text = input_text #TODO(g): This is in the wrong place: startup code
    #Log('Input: %s' % input_text)
  
  
  # Get information
  if self.input.IsKeyDown(K_i, once=True):
    #Log('Game:\n%s' % self.game)
    Log('Player:\n%s' % self.game.player)
  
  # If no Shift or Ctrl is being pressed
  if not ((self.input.IsKeyDown(K_LSHIFT) or self.input.IsKeyDown(K_RSHIFT)) or self.input.IsKeyDown(K_LCTRL)):
    # If they hit 1
    if self.input.IsKeyDown(K_1, once=True):
      game.use_camera_view = not game.use_camera_view
      print 'Using Camera View: %s' % game.use_camera_view

    # If they hit LEFT
    if self.input.IsKeyDown(K_LEFT):
      game.time_elapsed -= 0.2
      if game.time_elapsed < 0.0:
        game.time_elapsed = 0.0
      print 'BACK: %0.1f seconds since start' % (game.time_elapsed)
    
    # If they hit RIGHT
    if self.input.IsKeyDown(K_RIGHT):
      game.time_elapsed += 0.2
      #TODO(g):HARDCODED: Remove hard coded max time, it should be based on timeline total length, which can be slid out dynamically
      #TODO(g): Add shorten/length timeline stuff.  Dont bother deleting any scenes or goals, just crop as necessary and let deleting them be specific
      if game.time_elapsed >= 300.0:
        game.time_elapsed = 299.9
      print 'FWRD: %0.1f seconds since start' % (game.time_elapsed)

    if self.input.IsKeyDown(K_UP):
      game.time_elapsed -= 2.0
      if game.time_elapsed < 0.0:
        game.time_elapsed = 0.0
      print 'BACK: %0.1f seconds since start' % (game.time_elapsed)
    
    if self.input.IsKeyDown(K_DOWN):
      game.time_elapsed += 2.0
      if game.time_elapsed >= 300.0:
        game.time_elapsed = 299.9
      print 'FWRD: %0.1f seconds since start' % (game.time_elapsed)
    
    # Select Next Actor
    if self.input.IsKeyDown(K_TAB, once=True):
      selected_actor = owr_screenplay.SelectNextActor(game)
      print 'TAB: Selected Actor: %s' % (selected_actor)

    # Adjust how much to skip between Future/Past frames
    if self.input.IsKeyDown(K_LEFTBRACKET):
      game.future_past_skip -= 1
      if game.future_past_skip < 1:
        game.future_past_skip = 1
      print 'Skip adjusted: %s' % game.future_past_skip
    if self.input.IsKeyDown(K_RIGHTBRACKET):
      game.future_past_skip += 1
      if game.future_past_skip > 50:
        game.future_past_skip = 50
      print 'Skip adjusted: %s' % game.future_past_skip

  # If only Left Shift is being held down
  if (self.input.IsKeyDown(K_LSHIFT) or self.input.IsKeyDown(K_RSHIFT)) and not self.input.IsKeyDown(K_LCTRL):
    # Select Previous Actor
    if self.input.IsKeyDown(K_TAB, once=True):
      selected_actor = owr_screenplay.SelectNextActor(game, reverse=True)
      print 'TAB: Selected Actor: %s' % (selected_actor)

    # If they hit LEFT
    if self.input.IsKeyDown(K_LEFT, once=True):
      previous_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed, get_previous_state=True)
      game.time_elapsed = previous_state['at']
      print 'PREVIOUS CHANGE POINT: %0.1f seconds since start' % (game.time_elapsed)
    
    # If they hit RIGHT
    if self.input.IsKeyDown(K_RIGHT, once=True):
      next_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed, get_next_state=True)
      game.time_elapsed = next_state['at']
      print 'NEXT CHANGE POINT: %0.1f seconds since start' % (game.time_elapsed)

    # If they hit RIGHT - Move only 1 frame worth of time
    if self.input.IsKeyDown(K_DOWN, once=True):
      game.time_elapsed += (1.0 / float(owr_screenplay.FRAMES_PER_SECOND))
      #TODO(g):HARDCODED: Remove hard coded max time, it should be based on timeline total length, which can be slid out dynamically
      #TODO(g): Add shorten/length timeline stuff.  Dont bother deleting any scenes or goals, just crop as necessary and let deleting them be specific
      if game.time_elapsed >= 300.0:
        game.time_elapsed = 299.9
      print 'FWRD STEP: %0.1f seconds since start' % (game.time_elapsed)

    # If they hit LEFT - Move only 1 frame worth of time
    if self.input.IsKeyDown(K_UP, once=True):
      game.time_elapsed -= (1.0 / float(owr_screenplay.FRAMES_PER_SECOND))
      #TODO(g):HARDCODED: Remove hard coded max time, it should be based on timeline total length, which can be slid out dynamically
      #TODO(g): Add shorten/length timeline stuff.  Dont bother deleting any scenes or goals, just crop as necessary and let deleting them be specific
      if game.time_elapsed < 0.0:
        game.time_elapsed = 0.0
      print 'REVERSE STEP: %0.1f seconds since start' % (game.time_elapsed)


    # Adjust how much to skip between Future frames
    if self.input.IsKeyDown(K_LEFTBRACKET, once=True):
      game.future_frames -= 1
      if game.future_frames < 0:
        game.future_frames = 0
      print 'Future Frames adjusted: %s' % game.future_frames
    if self.input.IsKeyDown(K_RIGHTBRACKET, once=True):
      game.future_frames += 1
      if game.future_frames > 20:
        game.future_frames = 20
      print 'Future Frames adjusted: %s' % game.future_frames

  # If only Left CTRL to being held down
  if self.input.IsKeyDown(K_LCTRL) and not self.input.IsKeyDown(K_LSHIFT):
    # Adjust how much to skip between Past frames
    if self.input.IsKeyDown(K_LEFTBRACKET, once=True):
      game.past_frames -= 1
      if game.past_frames < 0:
        game.past_frames = 0
      print 'Past Frames adjusted: %s' % game.past_frames

    if self.input.IsKeyDown(K_RIGHTBRACKET, once=True):
      game.past_frames += 1
      if game.past_frames > 20:
        game.past_frames = 20
      print 'Past Frames adjusted: %s' % game.past_frames

    # If we're told to Save the screenplay
    if self.input.IsKeyDown(K_s, once=True):
      owr_screenplay.SaveScreenplay(game)

    # If we're told to Save the screenplay
    if self.input.IsKeyDown(K_m, once=True):
      #owr_screenplay.SaveScreenplay(game)
      game.ui_select_viewport = {'action':'position camera', 'first':None, 'second':None}

    # Add an Actor
    if self.input.IsKeyDown(K_a, once=True):
      print 'Add an Actor'
      # Clear the string, so we can get it
      game.core.input.ClearAutoString()
      # Create UI Popup information, to create a popup input display
      game.ui_popup_data = {'action':'add actor', 'prompt':'Enter Name:', 'name':None}


  # Start and Stop playing
  if self.input.IsKeyDown(K_SPACE, once=True):
    game.playing = not game.playing
    # Reset time, so we dont jump ahead
    game.time_previous = time.time()
    game.time_current = time.time()


  # If they hit ESC
  if self.input.IsKeyDown(K_ESCAPE, once=True):
    # Save the Screenplay before we quit
    #TODO(g): Check if it changed, make a ".lastquit" version of it, and load that.  Allow loading of
    #   previous versions and do versioning in a backup directory.  Not a lot of data, worth having
    #   continuous Undo log of saved states...
    owr_screenplay.SaveScreenplay(game)

    # Save the UI state, so we can resume editing in the same place we left off on restart
    owr_screenplay.SaveUIState(game)

    game.quitting = True




