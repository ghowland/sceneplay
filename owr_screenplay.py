"""
Screenplay Renderer
"""


import yaml
import time
import pygame
import random
import copy
import os

import owr_image
import owr_gfx
import owr_behavior
import owr_timeline


# Frames per second we will be calculating.  Determines the time-slices for all the animation
#   actions
FRAMES_PER_SECOND = 10


# Number of seconds to calculate into the future, handles future notifications and also doesnt have to
#   pre-calculate everything thats going to happen in the entire screenplay.  Can stop at scene changes
#   as well.
CALCULATE_FUTURE_SECONDS = 3.0


# Image cache for the Screenplay
IMAGES = {}


# YAML data cache, animation data
DATA_CACHE = {}


def SaveScreenplay(game):
  """Save the current screenplay"""
  print 'Saving: %s' % game.data['screenplay']
  os.rename(game.data['screenplay'], game.data['screenplay'] + '.previous')
  yaml.dump(game.data['screenplay_data'], open(game.data['screenplay'], 'w'))

  # Save all our timeline data
  for timeline_key in game.timeline_data:
    game.timeline_data[timeline_key].Save()



def SaveUIState(game):
  """Save the basic UI state, so we can quit and reload without finding the last place and setup.

  This should massively aid development and testing speed.
  """
  state = {}
  state['time_elapsed'] = game.time_elapsed
  state['time_current'] = game.time_current
  state['music'] = game.music
  state['current_timeline_frame'] = game.current_timeline_frame
  state['music'] = game.music
  state['future_frames'] = game.future_frames
  state['ui_selected_actors'] = game.ui_selected_actors
  state['use_camera_view'] = game.use_camera_view

  print 'Saving UI State: %s' % state

  filename = game.data['screenplay'].replace('.yaml', '_ui_state.yaml') 
  yaml.dump(state, open(filename, 'w'))


def LoadUIState(game):
  """Load and set the UI state, so we can resume work without finding our last place in things.
  """
  filename = game.data['screenplay'].replace('.yaml', '_ui_state.yaml') 

  # If the save file exists, load it
  if os.path.exists(filename):
    state = yaml.load(open(filename, 'r'))

    print 'Loading UI State: %s' % state

    # Set all the loaded values into our game state
    #TODO(g): Maybe these should be separated out into their own dict?  Seems like a lot of work for 
    #   now, changing everywhere they are accessed, but in a re-write I think this is a better
    #   place for these long-lived values
    for (key, value) in state.items():
      setattr(game, key, value)


def RegenerateTimeline(game):
  """Helper to regenerate"""
  # Generate the Timeline
  game.data['timeline_data'] = GenerateTimeline(game, game.data['screenplay_data'])

  # Clear behavior cache
  owr_behavior.ClearCache()


def GenerateTimeline(game, data):
  """Returns list of timeline states (scene frames) generated for an entire timeline.

  A scene frame is a dict that describes the position/state of all assets for rendering.

  This can include music/sound play positions and visual assets.
  """
  timeline = []

  import pprint
  pprint.pprint(data)

  # Set the Random Seed, so that all randomness is the same
  random.seed(game.core.data['game']['random_seed'])
  

  #TODO(g): Get this from the music, or other source that sets the total duration
  total_time = game.core.data['game']['total_time']

  # Total frames is time * FPS.  Current frame is the last frame that happened with the same calculation
  total_frames = total_time * game.data.get('fps', FRAMES_PER_SECOND)

  # Time interval in seconds based on FPS, for each scene frame
  interval = 1 / float(FRAMES_PER_SECOND)

  # This is the current state of all things, all data needs to be unique non-referencing data, as it
  #   changes each frame, and shouldnt change any previous data.
  current_state = {}

  print '--- Starting ---'

  # Generate all the Scene Frames
  for current_frame in range(0, total_frames):
    current_time = interval * float(current_frame)
    print 'Generating Time: %0.3f' % current_time
    scene_frame = GenerateSceneFrame(current_state, current_time, interval, game, data)
    timeline.append(scene_frame)

  print '--- Ending ---'

  return timeline


def GetCurrentTimelineSceneFrameNumber(timeline, time_elapsed):
  """Get the last frame that has occurred"""
  current_frame = int(time_elapsed * FRAMES_PER_SECOND)

  # If its over the timeline, return the last frame
  if current_frame >= len(timeline):
    return len(timeline) - 1
  else:
    return current_frame


def GenerateSceneFrame(current_state, current_time, interval, game, data):
  """Returns dict with scene graph information that changes the current_state for all actors 
  by the interval, based on their current state.  

  Determine the current state based on the current_time, update each of the AI states
  by the interval.

  TODO: Cache the progress through the timeline in some conveniently passed in way, so we dont have to
  sweep through all the data each time. 
      We need the control statement for each actor (visual/audio/whatever) that was the last one.

  TODO: When the world scene is going to change, add this notice to the sceme frame so it can be
      rendered if desired.
  """
  #scene_frame = {}

  #TOOD(g): Save last state, and just walk through it, so that each time I do this I dont have
  #   to do all the work over from scratch again.  These processes need to be integrated here so
  #   that its fast to generate more time, and it only has to regenerate everything when the
  #   screenplay data changes, which means things are going to change.  Further optimizations can
  #   be done later to help with very large screen plays.  Scene Changes will be modules, and only
  #   have to generate from that time on
  #TODO(g): Scene Changes are the beginning of state, so each one is like a module, and has a given
  #   time to run, all data can be considered running from the last scene, so only determining
  #   the current scene will be required for initial data.  
  #TODO(g): FASTEST: Remove image maniuplations and GetAnimation() calls, because these make this
  #   slow and should be done with the render portion of the code, not the data analysis portion of
  #   the code, which will probably make this fast enough...
  current_time_line_state = TimelineState(game, data, current_time)

  # Copy first level of dictionary, we will be replacing actors and leaving other things
  scene_frame = copy.deepcopy(current_time_line_state)

  if not hasattr(game, 'last_state_count'):
    game.last_state_count = 0

  # If the Scene has changed
  if current_time_line_state['state_count'] != game.last_state_count:
    # Clear the Actor behavior cache, which will reset any state from the previous scene
    owr_behavior.ClearCache()

    # Set the last state count, so when we do the next interval we know when the Scene changes
    game.last_state_count = current_time_line_state['state_count']

  # Ensure there is an actor dict
  if 'actors' not in scene_frame:
    scene_frame['actors'] = {}

  # Update the actors from 
  for (actor, actor_data) in scene_frame['actors'].items():
    # print 'Actor: %s  Data: %s' % (actor, actor_data)
    scene_frame['actors'][actor] = owr_behavior.Update(game, data, current_time, actor, actor_data, interval)
    # print '  After: %s' % scene_frame['actors'][actor]

  # Get the Cameras and Dialog for this scene frame as well
  scene_frame['cameras'] = game.timeline_data['camera'].GetItemsAtTime(current_time)
  scene_frame['dialog'] = game.timeline_data['dialog'].GetItemsAtTime(current_time)

  # # Replace scene_frame actor data with our new actor data
  # for (actor, actor_data) in actors.items():
  #   scene_frame['actors'][actor] = actor_data
  #   # if '__state__' in scene_frame['actors'][actor]:
  #   #   print 'Has __state__'
  #   # else:
  #   #   print 'No __state__'


  #TODO: Any actor can have multiple time line states being applied at any time, they start and stop
  #   as they are specified, and can conflict or whatever.  Each of them is applied in the order they
  #   were received, to be deterministic, and can be ended and started again to application order.
  # 
  #   Actor state is passed through each effect, and it makes the determination on whats going on.
  #
  #   What animation is occcurring is based on a priority that can be set as animation_priority.  The
  #   highest priority will be the animation, so that any animations can be given priority.
  #
  #   movement_priority can also say which movements will occur, if it is set.  If it isnt set, then
  #   a vector normal of all distances based on velocity are set.
  #
  #   Animation and movement shouldnt be handled by an Actor Controller?  This would solve all those
  #   problems at one time, just like I would for a video game...  I think this is better...
  #
  #   Easiest to let code handle this, and be able to change the Actor Controller any time in the
  #   time_line_state, so that someone can be flipped around easily.
  #
  #   Yes, ActionController handles assigning movement changes and animation selection and current
  #   frame based on the time line state.  Multiple statements can be applied to a given actor.
  #  
  #   A clear-states flag can be set on a time to clear any prior states, to start things fresh.
  #   Using the GUI to specify this should make this easier, but theres a data hammer to make it always
  #   correct.
  #   
  #   Can use the multiple states on a single actor as attractors, so that some are set by time,
  #   and must occur, and others simply modify how that is performed, such as saying things should
  #   be done while jumping continuously or walking towards a spot and then another.  Can dramatically
  #   increase the novelty of the scene animations based on all the factors combined, which would take
  #   too much time to move around individually, or would be like standard animation instead of my
  #   goal-based animation.
  #
  #   Start out with basics, how to select a background, add an actor, and move them around.
  #
  #   Draw up UI outlines, and selection criteria for selecting scenes or actors, or choosing
  #   frames for actors.
  #
  #   Allow adjument for moving things around.  This is a UI based program.
  #
  #   Can also record movements from joystick, so that we have detailed input given.  So that each 
  #   actor is controlled by me, and I can time out movements frame per frame, based on input
  #   changes that I record from a joystick.  This really adds detailed game control, if I play back 
  #   and forth
  #
  #   Can take it in slow motion, and move less than real-time to accept more detailed input.  Moving
  #   between actors, and playing out each ones movements.
  #
  #   Can select what the input means at any given time as well, with an input map.
  #
  #   This is mine, I can do anything I want with it, as many input sources as possible.  This is really
  #   the way to make innovations, make it for yourself, and take it to the limit you can think of how
  #   you can be creative and make things you want.
  #
  #   Think of this program as interactive as a multi-purpose editor, not as a game engine or video
  #   engine, so that it is interactive in all the ways that help me control the state over time, and
  #   select assets, and modify their values and such.
  #
  pass

  return scene_frame


def TimelineState(game, data, time_elapsed, get_next_state=False, get_previous_state=False):
  """Returns a dictionary of all timeline state"""
  # Go through each of our items
  for count in range(0, len(data)):
    # If there is no next state, this is the last state: this is the state, so break
    if count + 1 >= len(data):
      break

    # Else, get the next state
    else:
      # If the next state is past our elapsed time, this is the state, so break
      if data[count + 1]['at'] > time_elapsed:
        break

  # If we wanted the previous state, get that
  if get_previous_state:
    if count - 1 >= 0:
      count = count - 1
      state = data[count]
    else:
      state = data[count]

  # Else, if we wanted the next state, try to get that
  elif get_next_state and count + 1 < len(data):
    count = count + 1
    state = data[count]

  # Else, current state
  else:
    state = data[count]

  # Ensure Actors container always exists
  if 'actors' not in state:
    state['actors'] = {}

  if 'state_count' not in state:
    state['state_count'] = count

  return state


def GetImage(game, filename, force_scale=None):
  """Returns an image, whether cached or not"""
  global IMAGES

  if filename not in IMAGES:
    if force_scale == None:
      IMAGES[filename] = owr_image.Load(filename, scale=game.data['window']['scale'])
    else:
      IMAGES[filename] = owr_image.Load(filename, scale=force_scale)

  return IMAGES[filename]


def Render(game, background):
  """Render the current Scene"""
  #print 'Screen Play: Render'

  # Initialize game if we havent loaded the screenplay data yet
  if 'screenplay_data' not in game.data:
    game.data['screenplay_data'] = yaml.load(open(game.data['screenplay']))

    # Create all the TimeLine Data sets
    game.timeline_data = {}
    game.timeline_data['camera'] = owr_timeline.TimelineData(game.data['screenplay'].replace('.yaml', '_camera.yaml'))
    game.timeline_data['dialog'] = owr_timeline.TimelineData(game.data['screenplay'].replace('.yaml', '_dialog.yaml'))

    # Time that has elapsed so far
    game.time_elapsed = 0.0
    game.time_started = time.time()
    game.time_previous = time.time()
    game.time_current = time.time()
    game.time_reset = False

    game.music = None

    game.playing = False

    # Used for rendering all frames iteratively
    game.current_timeline_frame = 0

    # Future/Past view
    game.future_frames = 0
    game.past_frames = 0
    game.future_past_skip = 7

    # Create the View Port screen buffer
    game.viewport = pygame.Surface(game.core.data['window']['viewport size'])
    game.viewport = game.viewport.convert()

    # Create UI variables here, just to keep them all in one place
    # List of selected actors in our UI
    game.ui_selected_actors = []
    game.ui_popup_data = None
    game.ui_select_viewport = None
    game.ui_hover_over_button = None

    # Assume False initially
    game.use_camera_view = False

    # Load any saved UI state to overwrite these defaults
    LoadUIState(game)

    # Reset the time elapsed, if we are rendering
    if game.options['render']:
      game.time_reset = True
      game.current_timeline_frame = 0
      game.use_camera_view = True



  # Get the current time, and increment the elapsed time
  if game.playing == True:
    game.time_previous = game.time_current
    game.time_current = time.time()
    time_advance = game.time_current - game.time_previous
    #time_advance = 1.0 / FRAMES_PER_SECOND
    game.time_elapsed += time_advance

  # reset_this_frame = False
  if game.time_reset:
    game.time_started = time.time()
    game.time_previous = time.time()
    game.time_elapsed = 0.0
    game.time_reset = False

    if game.options['music']:
      pygame.mixer.music.rewind()
    print '-- RESET TIMELINE --'
    # reset_this_frame = True


  # If we need to Generate the Time Line (first time or on reset)
  if 'timeline_data' not in game.data:
    game.data['timeline_data'] = GenerateTimeline(game, game.data['screenplay_data'])


  # Limit how far our time goes based on how many frames there are
  max_time = len(game.data['timeline_data']) / float(FRAMES_PER_SECOND)
  if game.time_elapsed > max_time:
    game.time_elapsed = max_time


  # Get the timeline state
  if not game.options['render']:
    game.current_timeline_frame = GetCurrentTimelineSceneFrameNumber(game.data['timeline_data'], game.time_elapsed)
    state = game.data['timeline_data'][game.current_timeline_frame]

  else:
    # If we have processed all the frames, quit
    if game.current_timeline_frame >= len(game.data['timeline_data']):
      game.quitting = True
      return

    # Else, process the current frame
    else:
      state = game.data['timeline_data'][game.current_timeline_frame]
      game.current_timeline_frame += 1
      game.time_elapsed = game.current_timeline_frame / float(FRAMES_PER_SECOND)


  # Clear UI targets, every frame.  Will be processed by InputHandler() before next render
  game.input_targets = []


  #if reset_this_frame:
  if 0:
    import pprint
    pprint.pprint(state)

  # If we have a Camera View, then set the Offset and calculate the Scale
  #TODO(g): Use separate cache for images for all scales.  Add ClearCache as well...
  if state['cameras'] and game.use_camera_view:
    camera = state['cameras'][0]
    camera_offset = camera['rect'][:2]
    camera_viewport_size = camera['rect'][2:]
    
    #TODO(g): Do full viewport scale calculations, using both width/height of camera viewport size
    camera_scale = game.viewport.get_width() / float(camera_viewport_size[0])
  
  # Else, no Camera Offset or Scale
  else:
    camera_offset = [0, 0]
    camera_scale = 1.0


  # Render the state
  #TODO(g): Update the camera position too
  image = GetImage(game, state['background'])
  owr_gfx.Draw(image, game.viewport, [-camera_offset[0] * camera_scale, -camera_offset[1] * camera_scale], scale=camera_scale)
 
  # Render time-forward actors
  for count in range(1, game.future_frames + 1):
    frame_forward = count * game.future_past_skip
    if game.current_timeline_frame + frame_forward < len(game.data['timeline_data']):
      forward_state = game.data['timeline_data'][game.current_timeline_frame + frame_forward]
      # Render the Actors
      for (actor, actor_data) in forward_state['actors'].items():
        # Skip any actors that arent selected in UI.  Adds control.
        if actor not in game.ui_selected_actors:
          continue

        #print('Rendering Future Actor: %s - %s' % (actor, game.current_timeline_frame + count))
        RenderActor(game, game.viewport, actor, actor_data, opacity=230 - frame_forward*1.7, opacity_fill=(255, 100, 100), camera_offset=camera_offset, camera_scale=camera_scale)
 
  # Render time-backward actors
  for count in range(1, game.past_frames + 1):
    frame_reverse = count * game.future_past_skip
    if game.current_timeline_frame - frame_reverse >= 0:
      forward_state = game.data['timeline_data'][game.current_timeline_frame - frame_reverse]
      # Render the Actors
      for (actor, actor_data) in forward_state['actors'].items():
        # Skip any actors that arent selected in UI.  Adds control.
        if actor not in game.ui_selected_actors:
          continue

        #print('Rendering Future Actor: %s - %s' % (actor, game.current_timeline_frame + count))
        RenderActor(game, game.viewport, actor, actor_data, opacity=200 - frame_reverse*1.9, opacity_fill=(100, 100, 255), camera_offset=camera_offset, camera_scale=camera_scale)

  # Sort actors using Y position
  actor_sorted = {}
  for (actor, actor_data) in state['actors'].items():
    y = actor_data['pos'][1]
    if y not in actor_sorted:
      actor_sorted[y] = []
    
    if actor_data.get('render', True):
      actor_sorted[y].append(actor)

  # Render the Actors, in sorted order
  y_pos_keys = list(actor_sorted.keys())
  y_pos_keys.sort()
  for y_pos in y_pos_keys:
    for actor in actor_sorted[y_pos]:
      RenderActor(game, game.viewport, actor, state['actors'][actor], camera_offset=camera_offset, camera_scale=camera_scale)


  # Render any Dialog
  if state['dialog']:
    dialog = state['dialog'][0]
    owr_image.DrawText(dialog['text'], 35, (255,255,255), (10, game.viewport.get_height() - 50), game.viewport, align_flag=1, outline=3, outline_color=(0,0,0))


  # Render any Camera Rects, if we arent using the camera view
  if state['cameras'] and not game.use_camera_view:
    camera = state['cameras'][0]
    owr_gfx.DrawRect(camera['rect'][:2], camera['rect'][2:], (0, 255, 0, 128), game.viewport, filled=False)



  # Music and Sound
  #TODO(g): Move this to its own module, its specific and important enough to need it.
  if game.music == None and game.options['music']:
    game.music = True
    pygame.mixer.init()
    pygame.mixer.music.load('data/music/music.mp3')
    pygame.mixer.music.play()

  # If were not playing, start playing from our current time
  if game.options['music'] and not pygame.mixer.music.get_busy():
    pygame.mixer.music.play(0, game.time_elapsed)


  # If we are rendering, then save each file
  if game.options['render']:
    path = 'output/output_%06d.png' % (game.current_timeline_frame - 1)
    owr_image.Save(game.viewport, path)

  # Render the View Port to the background
  owr_gfx.Draw(game.viewport, background, [0, 0])



def RenderActor(game, background, actor, actor_data, opacity=255, opacity_fill=(255, 255, 255), shadow=True, camera_offset=None, camera_scale=1.0):
  """Render an actor"""
  global DATA_CACHE

  # Default Camera Offset, if not passed in
  if camera_offset == None:
    camera_offset = (0, 0)

  # Retrieve the animation data from Data Cache
  if actor_data['data'] not in DATA_CACHE:
    animation_data = yaml.load(open(actor_data['data']))
    DATA_CACHE[actor_data['data']] = animation_data
  else:
    animation_data = DATA_CACHE[actor_data['data']]

  offset = animation_data[actor_data['action']]['offset']

  # Get the animation images for this action
  dir_images = owr_image.GetAnimationFrames(animation_data[actor_data['action']], game.data['window']['scale'])

  # Get the current animation frame number
  frame_number = actor_data['animation_counter'] % len(dir_images)

  image = dir_images[actor_data.get('frame', frame_number)]

  # Start Actor Position at World Pos
  actor_pos = [actor_data['pos'][0] * camera_scale, 
               actor_data['pos'][1] * camera_scale]

  # Offset the Actor by any Animation Frame Offsets/Corrections, Height (Jumping) scaled by the Camera Scale
  actor_pos[0] += offset[0] * camera_scale
  actor_pos[1] += ((offset[1] - image.get_height() - actor_data['pos'].height) * camera_scale)

  # Perform Scaled Camera Offset
  actor_pos[0] += -camera_offset[0] * camera_scale
  actor_pos[1] += -camera_offset[1] * camera_scale


  if shadow:
    shadow_size = (int(image.get_width() * 0.4 * camera_scale), int(image.get_height() * 0.15 * camera_scale))
    shadow_magic_offset = [31, -24]
    shadow_pos = [(actor_data['pos'][0] + offset[0] + shadow_magic_offset[0]) * camera_scale, 
                  (actor_data['pos'][1] + offset[1] + shadow_magic_offset[1]) * camera_scale]
    shadow_pos[0] += -camera_offset[0] * camera_scale
    shadow_pos[1] += -camera_offset[1] * camera_scale
    owr_gfx.DrawEllipse(shadow_pos, shadow_size, (0, 0, 0, 18), background)


  if actor_data['pos'].direction_x < 0:
    #TODO: Cache results
    image = owr_gfx.Flip(image)

  #print('Actor: %s - %s' % (actor, opacity))

  #TODO: Cache opacity changes too.  
  owr_gfx.Draw(image, background, actor_pos, opacity=opacity, opacity_fill=opacity_fill, scale=camera_scale)



def SelectNextActor(game, reverse=False):
  """Selects the Next Actor"""
  current_state = TimelineState(game, game.data['screenplay_data'], game.time_elapsed)
  actors = list(current_state['actors'].keys())
  actors.sort()
  temp_actors = list(actors)


  # If we have selected actors
  if game.ui_selected_actors:
    scene_selected_actors = []

    # Remove any actors that are selected
    for current_selected_actor in game.ui_selected_actors:
      if current_selected_actor in temp_actors:
        print temp_actors
        temp_actors.remove(current_selected_actor)
        scene_selected_actors.append(current_selected_actor)

    # If we still have temp actors, set the first one as selected
    if temp_actors:
      next_actor_index = actors.index(scene_selected_actors[0])

      # If we're going Forward
      if not reverse:
        # If we have the next actor in the 
        if next_actor_index + 1 < len(actors):
          next_actor_index += 1
        else:
          next_actor_index = 0

      # Else, going in Reverse
      else:
        # If we have the next actor in the 
        if next_actor_index - 1 < 0:
          next_actor_index = len(actors) - 1
        else:
          next_actor_index -= 1

      next_unselected_actor = actors[next_actor_index]

      # If the next actor to the first selected one is in our unselected actors, choose it
      if next_unselected_actor in temp_actors:
        selected_actor = next_unselected_actor
      else:
        selected_actor = temp_actors[0]
    # Else, we have no temp actors but do have some scene actors, so just take the first actor in our list
    elif actors:
      selected_actor = actors[0]
    else:
      selected_actor = None

  # Else, if we have some actors
  elif actors:
    selected_actor = actors[0]

  # Else, no selection
  else:
    selected_actor = None

  # Set the Select Actors to this selected actor
  if selected_actor:
    game.ui_selected_actors = [selected_actor]

  return selected_actor
