"""
Screenplay Renderer
"""


import yaml
import time
import math
import pygame

import owr_image
import owr_gfx
import owr_behavior

from owr_screenplay import FRAMES_PER_SECOND
from owr_screenplay import GetImage
import owr_screenplay



# UI Text Globals
ROW_HEIGHT = 40
FONT_SIZE = 25


# Complimentary UI colors - Blue
UI_COLORS = [
  (14, 83, 167),
  (39, 78,125),
  (4, 52, 108),
  (66, 132, 211),
  (104, 153, 211),
]

TEXT_COLORS = [
  (255, 255, 255),
  (154, 203, 251),
]

UI_HIGHTLIGHT_COLORS = [
  (255, 199, 0),
  (255, 92, 0),
  (4, 52, 108),
  (8, 33, 67),
 ]

UI_BACKGROUND_COLORS = [
  (6, 23, 47),
]

def Render_Mouse(game, background):
  """Render the Mouse"""
  mouse_image = GetImage(game, game.core.data['window']['mouse pointer'], force_scale=1.0)
  mouse_offset = game.core.data['window']['mouse pointer offset']
  draw_pos = [game.core.input.mousePos[0] + mouse_offset[0], game.core.input.mousePos[1] + mouse_offset[1]]
  owr_gfx.Draw(mouse_image, background, draw_pos)


def RenderViewportUI(game, background):
  """Render any UI over the Viewport"""
  # If we are doing UI Select Viewport, show the Render the Mouse in the View Port
  if game.ui_select_viewport:
    rect = pygame.Rect([0, 0], game.core.data['window']['viewport size'])
    if rect.collidepoint(game.core.input.mousePos):
      Render_Mouse(game, background)



def RenderSidebarUI(game, background):
  """Render the Sidebar UI"""
  if not hasattr(game, 'sidebar'):
    # Create the Sidebar screen buffer
    game.sidebar = pygame.Surface(game.core.data['window']['sidebar size'])
    game.sidebar = game.sidebar.convert()

  # Clear the UI Area
  owr_gfx.DrawRect([0,0], game.core.data['window']['sidebar size'], UI_BACKGROUND_COLORS[0], game.sidebar)

  # Render the Selected Actor Selection Details
  Render_ActorDetails(game, game.sidebar)

  # Render the Sidebar to the background
  owr_gfx.Draw(game.sidebar, background, [game.core.data['window']['viewport size'][0], 0])

  # Draw the mouse, if it's in our domain
  if game.core.input.mousePos[0] > game.core.data['window']['viewport size'][0]:
    Render_Mouse(game, background)


def RenderBottombarUI(game, background):
  """Render the Bottombar UI"""
  if not hasattr(game, 'bottombar'):
    # Create the Sidebar screen buffer
    game.bottombar = pygame.Surface(game.core.data['window']['bottombar size'])
    game.bottombar = game.bottombar.convert()

  # Clear the UI Area
  owr_gfx.DrawRect([0,0], game.core.data['window']['bottombar size'], UI_BACKGROUND_COLORS[0], game.bottombar)

  # Render the Time Line
  Render_Timeline(game, game.bottombar)

  # Render the Actor Selection Buttons
  Render_ActorButtons(game, game.bottombar)

  # Render the time elapsed
  #TODO(g): Add toggle control for this.  F10?
  text = FormatTimeString(game.time_elapsed)
  owr_image.DrawText(text, 25, (255,255,255), (10, game.bottombar.get_height() - ROW_HEIGHT), game.bottombar, outline=2, outline_color=(0,0,0))

  # Render time remaining
  text = '-%s' % FormatTimeString(game.core.data['game']['total_time'] - game.time_elapsed)
  owr_image.DrawText(text, 25, (255,255,255), (10 + 100, game.bottombar.get_height() - ROW_HEIGHT), game.bottombar, outline=2, outline_color=(0,0,0))

  # If we are doing Viewport Select, give a textual notice of this, so the Mode is Known
  if game.ui_select_viewport:
    text = 'Select From Viewport'
    owr_image.DrawText(text, 25, (255,0,0), (10 + 250, game.bottombar.get_height() - ROW_HEIGHT), game.bottombar, outline=2, outline_color=(0,0,0))


  # Render the Bottombar to the background
  owr_gfx.Draw(game.bottombar, background, [0, game.core.data['window']['viewport size'][1]])

  # Draw the mouse, if it's in our domain
  if game.core.input.mousePos[0] < game.core.data['window']['viewport size'][0] and \
      game.core.input.mousePos[1] > game.core.data['window']['viewport size'][1]:
    Render_Mouse(game, background)


def FormatTimeString(time_elapsed):
  """Formats time into M:SS.mm string"""
  minutes = int(time_elapsed) / 60
  seconds = int(time_elapsed - float(minutes * 60.0))
  subseconds = '%0.1f' % (time_elapsed - float(minutes * 60.0) - float(seconds))
  subseconds = subseconds[2:]
  text = '%d:%02d.%s' % (minutes, seconds, subseconds)

  return text



def RenderPopupUI(game, background):
  """Render the Popup UI"""
  # If we have popup data
  if game.ui_popup_data != None:
    popup_pos = [200, 250]
    popup_size = [400, 300]
    popup_rect = pygame.Rect(popup_pos, popup_size)

    # If this isnt a Viewport Selection key, render the UI
    if game.ui_popup_data['action'] not in ('add goal key', 'edit_goal_key') or game.ui_popup_data['key'] not in owr_behavior.VIEWPORT_SELECT_GOAL_KEYS:
      # Draw popup background
      # owr_gfx.DrawRect(popup_pos, popup_size, [32, 32, 32], background)
      rect = pygame.Rect(popup_pos, popup_size)
      owr_gfx.DrawRoundedRect(background, rect, UI_HIGHTLIGHT_COLORS[-1], radius=0.4)

      # Prompt
      owr_image.DrawText(game.ui_popup_data['prompt'], 25, (255,255,255), [popup_pos[0] + 20, popup_pos[1] + 20], background, outline=2, outline_color=(0,0,0))

    # Else, overload this function and make it create Viewport Select input, if it doesnt exist already
    else:
      # If we dont already have a Viewport Select item specified, use this ui_popup_data
      if game.ui_select_viewport == None:
        game.ui_select_viewport = game.ui_popup_data


    # If we arent doing a button map
    #TODO(g):HARDCODED: Make a data specification system for this later.  Can handle all these different
    #   cases in a generic way then too
    if not (game.ui_popup_data['action'] == 'add goal key' and game.ui_popup_data['key'] == None):
      input_text = game.core.input.GetAutoString()
      owr_image.DrawText(str(input_text), 25, (255,255,255), [popup_pos[0] + 20, popup_pos[1] + 60], background, outline=2, outline_color=(0,0,0))

    # Else, if were trying to get a new goal key
    elif game.ui_popup_data['action'] == 'add goal key' and game.ui_popup_data['key'] == None:
      # Render the Button Map with the Actors
      Render_UI_ButtonMap(game, background, 'add goal key:select:key', owr_behavior.GOAL_KEYS, 
                          popup_size[0] - 10, offset=[popup_pos[0] + 10, popup_pos[1] + 40], input_offset=[0, 0])

      # Draw the mouse, if it's in our domain
      if popup_rect.collidepoint(game.core.input.mousePos):
        Render_Mouse(game, background)

    #TODO(g): Separate input handling back to input class, in generalized data cleaned.  No need for
    #   all these specifics
    # If we got an auto-string, then move forward
    if game.core.input.autoKeyStringLast:
      # Add the new goal and value
      if game.ui_popup_data['action'] == 'add goal key':
        # If we dont have the key yet, set that first
        if game.ui_popup_data['key'] == None:
          pass
          # game.ui_popup_data['key'] = game.core.input.autoKeyStringLast
          # game.ui_popup_data['prompt'] = 'Enter Key Value: %s' % game.ui_popup_data['key']

        # Else, we're filling in the value
        else:
          # Change the Actor data
          current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
          actor_data = current_state['actors'][game.ui_popup_data['actor']]

          # Set the new key value
          actor_data['goal'][game.ui_popup_data['goal_number']][game.ui_popup_data['key']] = game.core.input.autoKeyStringLast

          # Regenerate Timeline
          owr_screenplay.RegenerateTimeline(game)

          # Clear the popup UI
          game.ui_popup_data = None

      # Set the new goal value
      elif game.ui_popup_data['action'] == 'edit goal key':
        # Change the Actor data
        current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
        actor_data = current_state['actors'][game.ui_popup_data['actor']]

        # Set the new key value, if it's an int, ensure it becomes an int or dont set it
        if type(actor_data['goal'][game.ui_popup_data['goal_number']][game.ui_popup_data['key']]) == int:
          try:
            actor_data['goal'][game.ui_popup_data['goal_number']][game.ui_popup_data['key']] = int(game.core.input.autoKeyStringLast)
          except:
            pass

        else:
          actor_data['goal'][game.ui_popup_data['goal_number']][game.ui_popup_data['key']] = game.core.input.autoKeyStringLast

        # Regenerate Timeline
        owr_screenplay.RegenerateTimeline(game)

        # Clear the popup UI
        game.ui_popup_data = None

      # Add an Actor
      elif game.ui_popup_data['action'] == 'add actor':
        actor = game.core.input.autoKeyStringLast

        data = {'data': 'data/actors/alex.yaml', 'goal': [{},], 'handler': 'person', 'pos': [200, 200]}

        # Append this to the list of Selected Actor, as we probably want to edit him now
        game.ui_selected_actors.append(actor)

        # Add the Actor data
        current_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)

        current_state['actors'][actor] = data

        # Regenerate Timeline
        owr_screenplay.RegenerateTimeline(game)

        # Clear the popup UI
        game.ui_popup_data = None

      # Clear the auto string, because we just used it
      game.core.input.ClearAutoString()



    #game.ui_popup_data = {'prompt':'Enter value', 'actor':input_target['data'], 'value':None}
    pass

  
def Render_Timeline(game, background):
  """Render the Time Line"""
  # Render the timeline as a series of rectangle boxes for each Scene
  #TODO(g): Currently scenes are defined when the "background" image changes, later this
  #   will change to proper Scene Breaks, so that all actors are cleared and other state
  #   is reset, as the Scene has changed and new scenes need new settings

  # Get our total duration
  total_duration = len(game.data['timeline_data']) * FRAMES_PER_SECOND

  # Generate a list of scenes with time durations, in order
  scene_durations = []
  current_scene_frames = 0
  current_scene_background = None

  # Find scene changes with current Background method of changing the scene
  for current_frame in range(0, len(game.data['timeline_data'])):
    current_timeline_data = game.data['timeline_data'][current_frame]

    # If the background hasnt changed, increment the current scene frames
    if current_scene_background == current_timeline_data['background']:
      current_scene_frames += 1

    # Else, the scene just changed
    else:
      # If we had something to save (every time but the first time, we will)
      if current_scene_frames > 0:
        current_duration = current_scene_frames * FRAMES_PER_SECOND
        scene_durations.append(current_duration)

      # Make this the new scene, and we're starting from 1
      current_scene_frames = 1
      current_scene_background = current_timeline_data['background']

  # If we have anything, save the last scene too
  if current_scene_frames > 0:
    current_duration = current_scene_frames * FRAMES_PER_SECOND
    scene_durations.append(current_duration)

  # print scene_durations

  MARGIN = 10
  TOP_MARGIN = 5
  HEIGHT = 20

  # Generate a list of ratios/pixel lengths to fill the background horizontally (-borders)
  scene_widths = []
  durations = []
  total_width = background.get_width() - MARGIN*2
  for scene_duration in scene_durations:
    duration_ratio = scene_duration / float(total_duration)
    durations.append(duration_ratio)
    width = total_width * duration_ratio
    scene_widths.append(int(width))

  # Draw the bars in widths
  width_progress = 0
  for scene_count in range(0, len(scene_widths)):
    scene_width = scene_widths[scene_count]
    scene_color = [(200 + scene_count*40) % 255, (100 + scene_count*35) % 255, (0 + scene_count*20) % 255]
    owr_gfx.DrawRect([width_progress + MARGIN, TOP_MARGIN], [scene_width, HEIGHT], scene_color, background)

    # Increment Progress
    width_progress += scene_width

  # Draw the Current Time marker
  current_time_ratio = (game.current_timeline_frame * FRAMES_PER_SECOND) / float(total_duration)
  current_time_x = current_time_ratio * width_progress # Use total progress to account for floating point skew
  owr_gfx.DrawRect([current_time_x + MARGIN - 3, TOP_MARGIN-3], [3, HEIGHT+6], [255,255,255], background)


def Render_ActorButtons(game, background):
  """Render the Actor Selection Buttons"""
  #NOTE(g): We always render the Default Camera as the first button, because there is always a camera
  #TODO(g): Is it a special actor, or normal actor?  Why not just treat it like a normal actor?  YES!!!
  pass

  # Get the current game state
  state = game.data['timeline_data'][game.current_timeline_frame]

  # Ensure at least the first actor is selected in this scene, because its just going to happen
  #   as soon as I want to work anyway
  found_actor_selected_in_this_scene = False
  for actor in state['actors']:
    if actor in game.ui_selected_actors:
      found_actor_selected_in_this_scene = True
      break

  # If we didnt find a selected actor, and we have actors, select the first actor as a time saver
  #TODO(g):PREFERENCE: Can make this an Advanced Option
  if not found_actor_selected_in_this_scene and state['actors']:
    game.ui_selected_actors.append(state['actors'].keys()[0])


  # Render the Button Map with the Actors
  Render_UI_ButtonMap(game, background, 'select actor', state['actors'].keys(), 
                      game.core.data['window']['bottombar size'][0], 
                      selected_keys=game.ui_selected_actors, 
                      offset=[0, 15], input_offset=[0, game.core.data['window']['viewport size'][1]])


def Render_ActorDetails(game, background):
  """Render the Selected Actor Selection Details"""
  pass

  # Get the current game state
  state = game.data['timeline_data'][game.current_timeline_frame]

  MARGIN = 15
  TOP_MARGIN = 15
  row = 0

  ROW_SIZE = ROW_HEIGHT
  FONT_SIZE = 25

  current_time_line_state = owr_screenplay.TimelineState(game, game.data['screenplay_data'], game.time_elapsed)

  # Always show the current Change Point
  text_color = UI_HIGHTLIGHT_COLORS[-3]
  text = 'Change Point: %s + %s' % (FormatTimeString(current_time_line_state['at']), FormatTimeString(game.time_elapsed - current_time_line_state['at']))
  text_pos = [MARGIN, TOP_MARGIN + (row * ROW_SIZE) - 15]
  owr_image.DrawText(text, FONT_SIZE, text_color, text_pos, background, outline=2, outline_color=(0,0,0))
  row += 1


  # Shwo Actor Details
  for actor in game.ui_selected_actors:
    if actor in state['actors']:
      actor_data = state['actors'][actor]

      timeline_actor_data = current_time_line_state['actors'][actor]
      actor_state = actor_data['__state__']

      text_color = UI_HIGHTLIGHT_COLORS[0]

      text = 'Actor: %s' % actor
      text_pos = [MARGIN, TOP_MARGIN + (row * ROW_SIZE)]
      owr_image.DrawText(text, FONT_SIZE, text_color, text_pos, background, outline=2, outline_color=(0,0,0))

      # Render the UI Button - Delete
      button_text = 'X'
      text_prefix_width = owr_image.GetFontWidth(text, FONT_SIZE)
      text_pos = [MARGIN + text_prefix_width, TOP_MARGIN + (row * ROW_SIZE)]
      Render_UI_Button(game, background, 'delete actor', [text_pos[0] + 170, text_pos[1]], button_text, UI_COLORS[0], UI_COLORS[2], 
                       text_color, size=[25, ROW_SIZE-2], input_offset=[game.core.data['window']['viewport size'][0], 0],
                       data=actor)

      row += 1

      text_color = (255, 255, 255)

      text = 'Pos: [%d, %d]' % (actor_data['pos'][0], actor_data['pos'][1])
      text_pos = [MARGIN, TOP_MARGIN + (row * ROW_SIZE)]
      #owr_image.DrawText(text, FONT_SIZE, text_color, text_pos, background, outline=2, outline_color=(0,0,0))
      button_width = Render_UI_Button(game, background, 'select position', text_pos, text, UI_COLORS[0], UI_COLORS[2], 
                       text_color, input_offset=[game.core.data['window']['viewport size'][0], 0],
                       data=[actor, 'pos'])

      text = '%s' % actor_data['action']
      text_pos = [MARGIN + button_width + 10, TOP_MARGIN + (row * ROW_SIZE)]
      owr_image.DrawText(text, FONT_SIZE, text_color, text_pos, background, outline=2, outline_color=(0,0,0))
      row += 1

      for goal_number in range(0, len(timeline_actor_data['goal'])):
        goal_keys = list(timeline_actor_data['goal'][goal_number].keys())
        goal_keys.sort()

        if actor_state['goal_number'] == goal_number:
          text_color = UI_HIGHTLIGHT_COLORS[1]

        # Get the primary Goal Key
        primary_goal_key = None
        for goal_key in goal_keys:
          if goal_key in owr_behavior.GOAL_KEYS:
            primary_goal_key = goal_key

        # If we dont have a Primary Goal key, set the UI mode to collect this Goal's value
        #   and skip this goal
        if not primary_goal_key:
          # If we dont have a require to populate this goal yet, add it now
          if game.ui_popup_data == None:
            game.ui_popup_data = {'action':'add goal key', 'prompt':'Select Goal:', 'actor':actor, 'goal_number':goal_number, 'key':None, 'value':None}

          # Skip this goal number, it needs to be entered still
          #TODO(g): Print out that this is happening, so there is visual information going on...
          continue

        #TODO(g): Turn primary_goal_key into a buttonm but lead in with the "  -", and selection of this
        #   goal key will toggle rendering the non-primary fields
        text = '  - %s' % primary_goal_key
        text_pos = [MARGIN, TOP_MARGIN + (row * ROW_SIZE)]
        owr_image.DrawText(text, FONT_SIZE, text_color, text_pos, background, outline=2, outline_color=(0,0,0))
        
        # Get the text width, so we can indent the button
        text_prefix_width = owr_image.GetFontWidth(text, FONT_SIZE)

        # Render the UI Button - Delete Goal
        button_text = 'X'
        text_pos = [MARGIN + 15 + text_prefix_width, TOP_MARGIN + (row * ROW_SIZE)]
        Render_UI_Button(game, background, 'delete goal', text_pos, button_text, UI_COLORS[0], UI_COLORS[2], 
                         UI_HIGHTLIGHT_COLORS[0], size=[25, ROW_SIZE-2], input_offset=[game.core.data['window']['viewport size'][0], 0],
                         data=[actor, goal_number])

        row += 1

        text_color = (255, 255, 255)

        for goal_key in goal_keys:
          # Skip the Primary Goal key, we already rendered that
          if goal_key == primary_goal_key:
            continue

          text = '    %s: ' % goal_key
          text_pos = [MARGIN, TOP_MARGIN + (row * ROW_SIZE)]
          owr_image.DrawText(text, FONT_SIZE, text_color, text_pos, background, outline=2, outline_color=(0,0,0))

          # Get the text width, so we can indent the button
          text_prefix_width = owr_image.GetFontWidth(text, FONT_SIZE)

          # Render the UI Button
          button_text = '%s' % timeline_actor_data['goal'][goal_number][goal_key]
          text_pos = [MARGIN + text_prefix_width, TOP_MARGIN + (row * ROW_SIZE)]
          button_width = Render_UI_Button(game, background, 'edit goal key', text_pos, button_text, UI_COLORS[0], UI_COLORS[2], 
                           text_color, input_offset=[game.core.data['window']['viewport size'][0], 0],
                           data=[actor, goal_number, goal_key, timeline_actor_data['goal'][goal_number][goal_key]])

          # Render the UI Button - Delete
          button_text = 'X'
          text_pos = [text_pos[0] + 15 + button_width, TOP_MARGIN + (row * ROW_SIZE)]
          Render_UI_Button(game, background, 'delete goal key', text_pos, button_text, UI_COLORS[0], UI_COLORS[2], 
                           UI_HIGHTLIGHT_COLORS[0], size=[25, ROW_SIZE-2], input_offset=[game.core.data['window']['viewport size'][0], 0],
                           data=[actor, goal_number, goal_key])
          row += 1

        # # Render the UI Button
        # text = '  '
        # text_prefix_width = owr_image.GetFontWidth(text, FONT_SIZE)
        # text = 'Add Goal Key'
        # text_pos = [MARGIN + text_prefix_width, TOP_MARGIN + (row * ROW_SIZE)]
        # Render_UI_Button(game, background, 'add goal key', text_pos, text, UI_COLORS[0], UI_COLORS[2], 
        #                  text_color, input_offset=[game.core.data['window']['viewport size'][0], 0],
        #                  data=[actor, goal_number])
        # row += 1

      # Render the UI Button
      text = '    '
      text_prefix_width = owr_image.GetFontWidth(text, FONT_SIZE)
      text = 'Add Goal'
      text_pos = [MARGIN, TOP_MARGIN + (row * ROW_SIZE)]
      Render_UI_Button(game, background, 'add goal', text_pos, text, UI_COLORS[0], UI_COLORS[2], 
                       text_color, input_offset=[game.core.data['window']['viewport size'][0], 0],
                       data=actor)
      row += 1

  # Click on string detail, enter string
  pass

  # Click on position detail, click on viewport and select WORLD position
  pass



def Render_UI_Button(game, background, action, pos, text, background_color, background_outline_color, 
                     text_color, size=None,
                     font_size=FONT_SIZE, offset=None, input_offset=None, data=None, margin=4, 
                     top_margin=-3):
  """Render a button"""

  if offset == None:
    offset = [0, 0]

  if input_offset == None:
    input_offset = [0, 0]

  #TODO(g):MAGICNUMBER: Get rid of this magic number bullshit and design a proper algorithm
  top_margin_offset = ((ROW_HEIGHT - FONT_SIZE) / 3.0) - 2

  width = GetButtonWidth(text, font_size=font_size, margin=margin, top_margin=-top_margin)

  if size == None:
    #size = [width + abs(margin * 2), font_size + abs(top_margin * 2)]
    size = [width + abs(margin * 2), font_size + ((ROW_HEIGHT - font_size) / 2)]

  rect_pos = [pos[0] + offset[0], pos[1] + offset[1] - top_margin_offset]

  rect = pygame.Rect(rect_pos, size)

  # Outline - Bottom shadow, actually...
  outline_offset = 1
  rect_outline = pygame.Rect([rect_pos[0] + outline_offset, rect_pos[1] + outline_offset], [size[0] + outline_offset, size[1] + outline_offset])
  owr_gfx.DrawRoundedRect(background, rect_outline, background_outline_color, radius=0.4)

  # Button background
  #owr_gfx.DrawRect(rect_pos, size, background_color, background)
  owr_gfx.DrawRoundedRect(background, rect, background_color, radius=0.4)

  # Button Text
  #TODO(g): Deal with this hard coded values
  text_pos = [pos[0] + margin + offset[0], pos[1] + top_margin + offset[1]]
  owr_image.DrawText(text, FONT_SIZE, text_color, text_pos, background, outline=2, outline_color=(0,0,0))

  # Register button in available UI buttons
  #TODO(g): Make auto-adjust function for UI panels and positions...
  input_pos = [pos[0] + offset[0] + input_offset[0], pos[1] + offset[1] + input_offset[1]]
  input_target = {'type':'button', 'name':text, 'pos':input_pos, 
                  'size':size, 'action':action, 'data':data}
  game.input_targets.append(input_target)

  # Returns the width, so callers can tell how much space theyre using
  return width


#TODO(g): Make margin/top_margin module global vars for this and Render_UI_Button()
def GetButtonWidth(text, font_size=FONT_SIZE, margin=4, top_margin=-3):
  """Returns int, width of pixels to render a button"""
  # Return the button width, so it can be tracked (caller knows the height (size))
  text_width = owr_image.GetFontWidth(text, font_size)
  button_width = text_width + margin * 2

  return button_width


def Render_UI_ButtonMap(game, background, action, button_list, width, selected_keys=None, 
                        button_key_order=None, offset=None, input_offset=None, margin=20, top_margin=20,
                        spacing=14):
  """Render the Actor Selection Buttons"""
  # If no offset, default
  if offset == None:
    offset = [0, 0]

  # Default selected keys
  if selected_keys == None:
    selected_keys = []

  # If we didnt get an order, use the sorted keys
  if button_key_order == None:
    button_key_order = list(button_list)
    button_key_order.sort()

  # Draw all Actor buttons
  row = 0
  last_button_pos = [margin, top_margin + (ROW_HEIGHT * row)]
  last_button_width = 0
  for count in range(0, len(button_list)):
    button_key = button_key_order[count]
    button_data = button_list[count]

    # Determine Button Position
    button_pos = [last_button_pos[0] + last_button_width, last_button_pos[1]]
    # Space all but the first
    if count > 0:
      button_pos[0] += spacing

    button_width = GetButtonWidth(button_key)
    button_size = [button_width - 4, ROW_HEIGHT - 3]

    # If we went over the edge, go down a row and reset to the margin
    if button_pos[0] + button_size[0] > width - margin:
      row += 1
      button_pos = [margin, top_margin + (ROW_HEIGHT * row)]


    #TODO(G): Add to default args...
    if button_key in selected_keys:
      text_color = UI_HIGHTLIGHT_COLORS[0]
    else:
      text_color = TEXT_COLORS[0]

    # If this button is being hovered over
    if button_key == game.ui_hover_over_button:
      background_color = UI_COLORS[0]
    else:
      background_color = UI_COLORS[1]


    # Render the UI Button
    button_width = Render_UI_Button(game, background, action, button_pos, button_key, 
                                    background_color, UI_COLORS[2], text_color, offset=offset, data=button_key, 
                                    input_offset=input_offset)


    # Store so we can float them left
    last_button_pos = button_pos
    last_button_width = button_width


