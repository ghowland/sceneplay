#!/usr/bin/env python


from owr_log import Log
import owr_gfx
import owr_image
import owr_player

#TODO(g): May want to remove these on refactor
import time
import math
from owr_util import LoadYaml
from thirdparty import AStar


ICONS = None

##def GetMapOffsetTilePos(game):
##  tile_x_offset = game.map.offset[0] / TILE_SIZE
##  tile_y_offset = game.map.offset[1] / TILE_SIZE
##  
##  return [tile_x_offset, tile_y_offset]


class LocationChange(Exception):
  """Location has changed, so need to stop rendering in this method."""


def RenderMap(game, background):
  """Render the map"""
  TILE_SIZE = [game.location_data['tile_size'][0] * game.data['window']['scale'], game.location_data['tile_size'][1] * game.data['window']['scale']]
 
  # Load the map data, if this is the first time
  if not game.location_data['map_data']:
    game.location_data['map_data'] = LoadYaml(game.location_data['map'])
 
  # Load the frames for all the tiles
  if not game.location_data['tile_data']:
    game.location_data['tile_data'] = owr_image.GetTileFrames(game.location_data['assets']['background'], game.data['window']['scale'])
    print 'Loaded tiles: %s' % len(game.location_data['tile_data'])
    
    
  MAP_SCREEN_WIDTH = (game.core.size[0] / TILE_SIZE[0]) + 1
  MAP_SCREEN_HEIGHT = (game.core.size[1] / TILE_SIZE[1]) + 1
 
  # tile_x_offset = game.map.offset[0]
  # tile_y_offset = game.map.offset[1]
  tile_x_offset = 0
  tile_y_offset = 0
 
  #Log('Render map offset: %s, %s'  % (tile_x_offset, tile_y_offset))
 
  #TODO(g): Make screen drawing dynamic based on core.size and scrolling offsets
  for y in range(0, MAP_SCREEN_HEIGHT):
    for x in range(0, MAP_SCREEN_WIDTH):
      tile_x = tile_x_offset + x
      tile_y = tile_y_offset + y
     
      # Get frame [x,y] from the map, or use the default
      if len(game.location_data['map_data']) > tile_y and len(game.location_data['map_data'][tile_y]) > tile_x:
        frame = game.location_data['map_data'][tile_y][tile_x]
      else:
        frame = game.location_data['tile_default']['frame']
      
      # filename = game.map.GetPaletteImage(index)
      # image = owr_image.Load(filename)
      pos = (x * TILE_SIZE[0], y * TILE_SIZE[1])
      image = game.location_data['tile_data'][frame]
     
      # Drap the tile
      owr_gfx.Draw(image, background, pos)


# Global for updating the path finding
UPDATE_PATH_FINDING = True


def RenderMouseObstacle(game, background):
  """Render the tile under the MOUSE_STATE button pointer"""
  global UPDATE_PATH_FINDING
  global MOUSE_STATE
  
  # Skip if there is on mouse state or we are hovering over a button
  if MOUSE_STATE == None or BUTTON_OVER:
    return
  
  # Nothing to draw  
  if MOUSE_STATE not in game.location_data['buttons']:
    MOUSE_STATE = None
    return
  
  button = game.location_data['buttons'][MOUSE_STATE]
  if 'obstacle' not in button:
    return
  
  TILE_SIZE = [game.location_data['tile_size'][0] * game.data['window']['scale'], game.location_data['tile_size'][1] * game.data['window']['scale']]
  
  MOUSE_X = (game.core.input.mousePos[0] / TILE_SIZE[0])
  MOUSE_Y = (game.core.input.mousePos[1] / TILE_SIZE[1])
  
  # Get a copy of the obstacle's data
  obstacle_id = button['obstacle']
  obstacle_data = dict(game.location_data['obstacles'][obstacle_id])
  obstacle_data['pos'] = [MOUSE_X, MOUSE_Y]
  obstacle_data['obstacle'] = obstacle_id
  
  
  TILE_MAP_REALLY_STARTS_Y = 2
  
  # Check against the path finding map, if you cant walk here, you cant place here
  if game.location_data['map_walkable_data'][MOUSE_Y][MOUSE_X] == -1:
    return
  
  # Ensure no Actors are standing on this tile
  global TEMP_ACTORS
  actors = TEMP_ACTORS
  for (actor_key, actor) in actors.items():
    for count in range(0, obstacle_data['footprint']):
      if int(actor['pos'][0]) == MOUSE_X + count and int(actor['pos'][1]) == MOUSE_Y:
        return
  
  # Draw the Rect -- DEBUG
  #owr_gfx.DrawRect([MOUSE_X * TILE_SIZE[0], MOUSE_Y * TILE_SIZE[1]], TILE_SIZE, [100, 100, 100, 50], background)
  
  # Draw the obstacle base (no turret)
  image = obstacle_data['image_data']
  pos = (MOUSE_X * TILE_SIZE[0] + obstacle_data['offset'][0], (MOUSE_Y * TILE_SIZE[1]) - image.get_size()[1] + obstacle_data['offset'][1])
  owr_gfx.Draw(image, background, pos)
  
  
  # If this is a tile selection...
  #TODO(g): Ignore whole function if hovering over a button currently
  if game.core.input.mouseButtons[0] == game.core.input.ticks:
    #if MOUSE_Y > TILE_MAP_REALLY_STARTS_Y:
    if 1:
      
      # Pay for the obstacle
      if game.data['game']['money'] >= obstacle_data['cost']:
    
        print 'Obstacle: %s' % obstacle_data
        
        # Add the obsctacle
        game.location_data['obstacle_placement'].append(obstacle_data)
        
        # Update the path finding map
        for count in range(0, obstacle_data['footprint']):
          if MOUSE_X + count < len(game.location_data['map_walkable_data'][MOUSE_Y]):
            #game.location_data['map_walkable_data'][MOUSE_Y][MOUSE_X + count] = -1
            game.location_data['map_walkable_path_finder'].setValue(MOUSE_X + count, MOUSE_Y, -1)
        
        # Update the global path finding map
        UPDATE_PATH_FINDING = True
        
        # Only pay for it after placing it
        game.data['game']['money'] -= obstacle_data['cost']
      
      # Clear the mouse, whether it was purchased or not
      #MOUSE_STATE = None




def RenderMapObstacles(game, background):
  """Render the map obstacles"""
  TILE_SIZE = [game.location_data['tile_size'][0] * game.data['window']['scale'], game.location_data['tile_size'][1] * game.data['window']['scale']]
  
  MAP_SCREEN_WIDTH = (game.core.size[0] / TILE_SIZE[0]) + 1
  MAP_SCREEN_HEIGHT = (game.core.size[1] / TILE_SIZE[1]) + 1
 
  # tile_x_offset = game.map.offset[0]
  # tile_y_offset = game.map.offset[1]
  tile_x_offset = 0
  tile_y_offset = 0
 
  #Log('Render map offset: %s, %s'  % (tile_x_offset, tile_y_offset))
 
  #TODO(g): Make screen drawing dynamic based on core.size and scrolling offsets
  for y in range(0, MAP_SCREEN_HEIGHT):
    for x in range(0, MAP_SCREEN_WIDTH):
      tile_x = tile_x_offset + x
      tile_y = tile_y_offset + y
      
      for obstacle in game.location_data['obstacle_placement']:
        if obstacle['pos'][0] == x and obstacle['pos'][1] == y:
          obstacle_data = game.location_data['obstacles'][obstacle['obstacle']]
          image = obstacle_data['image_data']
          pos = (x * TILE_SIZE[0] + obstacle_data['offset'][0], (y * TILE_SIZE[1]) - image.get_size()[1] + obstacle_data['offset'][1])
          
          # Draw the obstacle
          owr_gfx.Draw(image, background, pos)
          
          # Animate the turret all the time.  Just cause we have the assets.
          if 'turret' in obstacle_data:
            frame = int(time.time()*9.0 + x + y) % 8
            turret_image = game.location_data['assets'][obstacle_data['turret']]['angles'][292][frame]
            turret_offset = game.location_data['assets'][obstacle_data['turret']]['offset']
            pos = (x * TILE_SIZE[0] + turret_offset[0], (y * TILE_SIZE[1]) + turret_offset[1])
            owr_gfx.Draw(turret_image, background, pos)


def RenderBackground(game, surface):
  """Render the background."""
  # # If this is using a background scene, not a tilemap
  # if game.location_data['type'] != 'tilemap':
  #   #TODO(g): Add scrolling...
  if 1:
    owr_gfx.Draw(game.location_data['image'], surface, game.camera_offset)
  
  # # Else, render a tile map
  # else:
  #   RenderMap(game, surface)


def RenderMainMenu(game, surface):
  """Render the background."""
  owr_gfx.Draw(game.location_data['image'], surface, game.camera_offset)
  
  # Load title animation, if we dont have it
  if 'title_anim' not in game.location_data:
    game.location_data['title_anim'] = []
    for image in game.location_data['assets']['title_penguin']['images']:
      game.location_data['title_anim'].append(owr_image.Load(image, scale=game.data['window']['scale']))

  
  # Draw animation
  frame = int(time.time() * 3.0) % len(game.location_data['title_anim'])
  image = game.location_data['title_anim'][frame]
  owr_gfx.Draw(image, surface, [550, 120])
  
  owr_image.DrawText('Zombie Penguin Igloo Defense', 80, game.data['window']['ui_font_color'], [0, 50], surface, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
  
  # Buttons
  RenderButtons(game, surface)


def RenderLeaderBoard(game, surface):
  """Render the background."""
  owr_gfx.Draw(game.location_data['image'], surface, game.camera_offset)
  
  owr_image.DrawText('High Scores', 70, game.data['window']['ui_font_color'], [0, 50], surface, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)

  # Fake some leaders
  leaders = [
    'Zombie Ben',
    'Zombie Paul',
    'Zombie Serv',
    'Zombie Jackie',
    'Zombie Alex',
    'Zombie Laura',
    'Zombie Chris',
    'Zombie Damien',
    'Zombie Geoff',
  ]
  leaders.sort()
    
  # Render scores
  for count in range(0, len(leaders)):
    score_text = '%-20s %15d' % (leaders[count], 10110 - (count * 1000))
    owr_image.DrawText(score_text, 30, game.data['window']['ui_font_color'], [300, 150 + (count*45)], surface, align_flag=0, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
    
    # If this position has a medal
    if count < len(game.location_data['assets']['medals']['images']):
      image_name = game.location_data['assets']['medals']['images'][count]
      if 'images_loaded' not in game.location_data['assets']['medals']:
        game.location_data['assets']['medals']['images_loaded'] = {}
      if count not in game.location_data['assets']['medals']['images_loaded']:
        game.location_data['assets']['medals']['images_loaded'][count] = owr_image.Load(image_name, game.data['window']['scale'])
      
      image = game.location_data['assets']['medals']['images_loaded'][count]
      owr_gfx.Draw(image, surface, [300-75, 150 + (count*45)])
  
  # Buttons
  RenderButtons(game, surface)


def RenderWinGame(game, surface):
  """Render the background."""
  # Draw animation
  frame = int(time.time() * 3.0) % len(game.location_data['image_series'])
  image = game.location_data['image_series'][frame]
  owr_gfx.Draw(image, surface, game.camera_offset)
  
  owr_image.DrawText('Victory!', 60, [255,255,255], [0, 15], surface, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
  
  # Buttons
  RenderButtons(game, surface)
  
  # Timeout to Leaderboards
  if 'timeout' not in game.location_data:
    game.location_data['timeout'] = time.time() + 7
  else:
    if time.time() > game.location_data['timeout']:
      game.SelectLocation('enter_name')


def RenderLoseGame(game, surface):
  """Render the background."""
  # Draw animation
  frame = int(time.time() * 3.0) % len(game.location_data['image_series'])
  image = game.location_data['image_series'][frame]
  owr_gfx.Draw(image, surface, game.camera_offset)
  
  owr_image.DrawText('Defeat!', 60, [255,255,255], [0, 40], surface, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
  
  # Buttons
  RenderButtons(game, surface)
  
  # Timeout to Leaderboards
  if 'timeout' not in game.location_data:
    game.location_data['timeout'] = time.time() + 7
  else:
    if time.time() > game.location_data['timeout']:
      game.SelectLocation('enter_name')


def RenderEnterName(game, surface):
  """Render the background."""
  owr_gfx.Draw(game.location_data['image'], surface, game.camera_offset)
  
  owr_image.DrawText('Enter Your Name', 40, game.data['window']['ui_font_color'], [0, 125], surface, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
  
  # Timeout to Leaderboards
  if 'timeout' not in game.location_data:
    game.location_data['timeout'] = time.time() + 3
  else:
    if time.time() > game.location_data['timeout']:
      game.SelectLocation('credits')


def RenderIntro(game, surface):
  """Render the background."""
  if not 'cur_frame' in game.location_data:
    game.location_data['cur_frame'] = 0
    game.location_data['start_frame'] = time.time()
  
  frame_time = 3.2
  
  # Increment frames
  if time.time() > game.location_data['start_frame'] + frame_time:
    game.location_data['cur_frame'] += 1
    game.location_data['start_frame'] = time.time()
    if game.location_data['cur_frame'] >= len(game.location_data['image_series']):
      image = game.location_data['image_series'][-1]
      game.SelectLocation('play')
      return
      
  # Draw animation
  image = game.location_data['image_series'][game.location_data['cur_frame']]
  owr_gfx.Draw(image, surface, game.camera_offset)
  

def RenderCredits(game, surface):
  """Render the background."""
  owr_gfx.Draw(game.location_data['image'], surface, game.camera_offset)
  
  line = 0
  line_height = 50
  
  if 'scroll_pos' not in game.location_data:
    game.location_data['scroll_pos'] = 720
  
  lines = [
    'Ben Seto           Team Lead and 2D Artist',
    'Paul Tanompong     3D Artist',
    'Serv LaMer         3D Artist',
    'Jackie Wu          UI Design',
    'Alex Kim           UI Graphics',
    'Laura Yip          UI Graphics',
    'Chris Kusaba       Title and UI Graphics',
    'Damien Silkensen   Audio',
    'Geoff Howland      Programming',
  ]
  
  
  owr_image.DrawText('Team Zombie Penguin', 70, game.data['window']['ui_font_color'], [0, game.location_data['scroll_pos']  - line_height*2], surface, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
  
  for line in range(0, len(lines)):
    line_text = lines[line]
    owr_image.DrawText(line_text, 40, game.data['window']['ui_font_color'], [0, game.location_data['scroll_pos']  + (line * line_height)], surface, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
  
  # Scroll the credits
  game.location_data['scroll_pos'] -= 1
  
  # Switch to Leader Board once they have scrolled by
  if game.location_data['scroll_pos'] < -(len(lines)*line_height):
    game.SelectLocation('leader_board')


def RenderParticles(game, surface):
  """Render the particles (missiles)"""
  # Set local operating vars
  tile_size = [game.location_data['tile_size'][0] * game.data['window']['scale'], game.location_data['tile_size'][1] * game.data['window']['scale']]
  
  #TODO(g): Global actors
  global TEMP_ACTORS
  actors = TEMP_ACTORS
  
  #DEBUG(g): Initialize a missile if we dont have one, make one
  #TODO(g): Per obstacle that can shoot...
  #if not game.location_data['missiles']:
  for turret_data in game.location_data['obstacle_placement']:
    # If we dont know this bullet type, ignore this turret
    if turret_data['fire_type'] not in ('bullet',):
      continue
    
    # Process all the actors, find the actor in range closest to the goal
    closest_actor = None
    closest_distance = None
    #debug_dists = {}
    for (actor_key, actor_data) in actors.items():
      #turret_data = game.location_data['obstacle_placement'][0]
      
      # Determine distance from obstacle
      x_dist = abs(turret_data['pos'][0] - actor_data['pos'][0])
      y_dist = abs(turret_data['pos'][1] - actor_data['pos'][1])
      distance = math.sqrt(x_dist*x_dist+y_dist*y_dist)
      
      #debug_dists[actor_key] = {'dist':int(distance), 'node':len(actor_data['path'].nodes)}
      
      # If the actors is close enough to the obstacle, create missile
      if distance < turret_data['range'] and turret_data['next_fire_time'] < time.time():
        # If this is the closest actor to the goal
        if closest_distance == None and actor_data['path'] != None:
          #print 'First: %s: %s' % (actor_key, len(actor_data['path'].nodes))
          closest_distance = len(actor_data['path'].nodes)
          closest_actor = actor_data
        elif actor_data['path'] != None and len(actor_data['path'].nodes) < closest_distance:
          #print '%s: %s < %s' % (actor_key, len(actor_data['path'].nodes), closest_distance)
          closest_distance = len(actor_data['path'].nodes)
          closest_actor = actor_data
          
    
    # import pprint
    # pprint.pprint(debug_dists)
    
    # If we found a closest actor to the goal
    if closest_actor:
      actor_data = closest_actor
      actor_key = actor_data['key']
      
      # Create one from the first obstacle/turret
      missile = {'type':'bullet', 
                 'pos_from':list(game.location_data['obstacle_placement'][0]['pos']), 
                 'actor_to':actor_key, 
                 'pos':list(turret_data['pos']),
                 'velocity': 0.18,
                 'traveled': 0.0,
                 'damage': turret_data['fire_power'],
                 }
      
      # Set the fire_type specific missile information
      #TODO(g): Move this into defense.yaml...
      if turret_data['fire_type'] == 'bullet':
        missile['velocity'] = 0.10
        missile['damage'] = turret_data['fire_power']
      
      # Add the missile
      print 'Adding missile: %s - %s - %s' % (missile['actor_to'], len(actors[missile['actor_to']]['path'].nodes), turret_data['fire_period'])
      game.location_data['missiles'].append(missile)
      
      # Set when this turret last fired
      turret_data['next_fire_time'] = time.time() + turret_data['fire_period']
      
      #TEST(g): Create the missile from the first obstacle to the pig/penguin actor
      # type: round
      # # Tile position missile was initiated from
      # pos_from: null
      # # Actor the missile is targetting
      # actor_to: null
      # # Current tile position of the missile
      # pos: [null, null]
      # velocity: 0.06
      # traveled: null
  
  #TODO(g): Global actors
  actors = TEMP_ACTORS
  
  # Update the positions of the missiles
  for missile in list(game.location_data['missiles']):
    # If the actor is gone now
    if missile['actor_to'] not in actors:
      # Destroy the missile
      game.location_data['missiles'].remove(missile)
      # Skip processing
      continue
    
    # Track missile movement
    x = 0
    y = 0
    #TODO(g): Calculate slope and use that, instead of just adding velocity each time, speed will take care of collision, or max distance travelled will end the bullet before collision
    if missile['pos'][0] < actors[missile['actor_to']]['pos'][0]-0.25:
      missile['pos'][0] += missile['velocity']
      x = 1
    elif missile['pos'][0] > actors[missile['actor_to']]['pos'][0]+0.25:
      missile['pos'][0] -= missile['velocity']
      x = -1
    
    if missile['pos'][1] < actors[missile['actor_to']]['pos'][1]-0.25:
      missile['pos'][1] += missile['velocity']
      y = 1
    elif missile['pos'][1] > actors[missile['actor_to']]['pos'][1]+0.25:
      missile['pos'][1] -= missile['velocity']
      y = -1
    
    #print 'Missile Move: %s, %s -- %s -- %s' % (x, y, missile['pos'], actors[missile['actor_to']]['pos'])
    
    # If the missile hit
    if x == 0 and y == 0:
      #TODO(g): Play Sound
      #SetGameplayText(game, 'Hit %s' % actors[missile['actor_to']]['key'], 1.5)
      
      game.data['game']['score'] += 10
      # Destroy the missile
      game.location_data['missiles'].remove(missile)
      
      # Reduce health of the actor target
      actors[missile['actor_to']]['health'] -= missile['damage']
      if actors[missile['actor_to']]['health'] < 0:
        # Give the Money to the player for the kill
        #print actors[missile['actor_to']]
        #print '%s - %s' % (actors[missile['actor_to']]['actor'], game.location_data['actors'][actors[missile['actor_to']]['actor']])
        game.data['game']['money'] += game.location_data['actors'][actors[missile['actor_to']]['actor']]['money']
        
        del actors[missile['actor_to']]
      
    
  
  global ICONS
  if ICONS == None:
    LoadGlobalIcons(game)
  
  # Draw all the missiles
  for missile in game.location_data['missiles']:
    #TODO(g): Scaling
    #TODO(g): Add scale=# param to owr_gfx.Draw(), so this can be dealt with automatically, and selectively
    owr_gfx.Draw(ICONS['bullet'], surface, [missile['pos'][0] * tile_size[0], missile['pos'][1] * tile_size[1]])


TEMP_ACTORS={}
def RenderActors(game, surface):
  """Render the map"""
  # Draw all the actors
  #for name in game.map.actors:
  #  actor = game.map.actors[name]
  #  if game.map.CheckVisibility(actor.pos.x, actor.pos.y):
  #    owr_gfx.Draw(actor.image, background, actor.GetScreenPos())
  
  print 'RenderActor: %s' % game.data['game']['player_actor']

  # If the player is in the game yet...
  if game.data['game']['player_actor'] and game.player:
    #colorkey = game.player.data.get('image_color_key', None)
    #
    ##Log('Player: %s - %s' % (game.player.data['image'], colorkey))
    #player = owr_image.Load(game.player.data['image'], colorkey=colorkey)
    
    #Log('Rending Player Actor: %s -- %s' % (str(game.player.GetScreenPos()), str(game.player.pos)))
    pos = list(game.player.GetScreenPos())
    pos[0] += game.player.image_offset[0]
    pos[1] += game.player.image_offset[1]
    pos[1] -= game.player.vertical_height # Raise in the sky, for jumps/etc
    
    print 'Render Actor: %s: %s' % (game.data['game']['player_actor'], pos)

    if game.player.look_direction in (0, 1):
      owr_gfx.Draw(game.player.image, surface, pos)
    else:
      owr_gfx.Draw(game.player.image_flip, surface, pos)
  

  # Render some actors for Tower Defense
  global TEMP_ACTORS
  actors = TEMP_ACTORS

  if False:
    # Update the path finding, if required
    global UPDATE_PATH_FINDING
    if 'map_walkable' in game.location_data and game.location_data['map_walkable_data'] == None:
      UPDATE_PATH_FINDING = False
      # If we have to do an initial load of the original map data
      if game.location_data['map_walkable_data'] == None:
        game.location_data['map_walkable_data'] = LoadYaml(game.location_data['map_walkable'])
      
      
      # Get the verticle dimensions of the map
      game.location_data['map_path_finding_size'] = [None, len(game.location_data['map_walkable_data'])]
      
      # Update the sequential map
      game.location_data['map_path_finding'] = []
      for row in game.location_data['map_walkable_data']:
        # Populate the width of columns the first time
        if game.location_data['map_path_finding_size'][0] == None:
          game.location_data['map_path_finding_size'][0] = len(row)
      
        # Add all the tiles in a sequence
        for col_item in row:
          game.location_data['map_path_finding'].append(col_item)
      
      
      # Create the AStar map
      game.location_data['map_walkable_data_map'] = AStar.SQ_MapHandler(game.location_data['map_path_finding'], game.location_data['map_path_finding_size'][0], game.location_data['map_path_finding_size'][1])
      
      # Find paths for the actors
      print 'Map: %s' % game.location_data['map_path_finding']
      print 'Map size: %s' % game.location_data['map_path_finding_size']
      game.location_data['map_walkable_path_finder'] = AStar.AStar(game.location_data['map_walkable_data_map'])
    

    # Set the local path_finder var
    path_finder = game.location_data['map_walkable_path_finder']
    
    # If we need to update our actors
    if UPDATE_PATH_FINDING:
      UPDATE_PATH_FINDING = False
      # tile_start = AStar.SQ_Location(5, 5)
      # tile_end = AStar.SQ_Location(10, 10)
      # path = path_finder.findPath(tile_start, tile_end)
      # print path.nodes
      
      # Update all existing actor's maps
      for (actor_key, actor) in actors.items():
        #print 'Updated actor map: %s' % actor_key
        tile_start = AStar.SQ_Location(int(math.floor(actor['pos'][0])), int(math.floor(actor['pos'][1])))
        tile_end = AStar.SQ_Location(game.location_data['actor_end_tile'][0], game.location_data['actor_end_tile'][1])
        try:
          actor['path'] = path_finder.findPath(tile_start, tile_end)
        except AttributeError, e:
          actor['path'] = None
          print 'Failed to create path for actor: %s: %s' % (actor, path_finder.getValue(int(actor['pos'][0]), int(actor['pos'][1])))
    
    # Else, set the path_finder var from our previously created path finder
    else:
      path_finder = game.location_data['map_walkable_path_finder']
    
    #print 'Path Finder: %s' % path_finder
    
    # Release actors for Igloo Defense based on defense.yaml data
    import time
    #TODO(g): Release based on time, not just 1 per render frame, so we can always properly group per specification
    wave_data = game.location_data['waves'][game.location_data['wave']]
    if len(wave_data['actor_sets']) > game.location_data['current_actor_set']:
      current_actor_set_data = wave_data['actor_sets'][game.location_data['current_actor_set']]
    else:
      print 'Couldnt get current_actor_set_data: %s - %s: %s' % (game.location_data['current_actor_set'], game.location_data['actor_set_released'], len(wave_data['actor_sets']))
      current_actor_set_data = None
    
    # If we are just starting this level and no more actors (all killed for that wave)
    if game.location_data['next_actor_time'] == 0 and current_actor_set_data != None and len(actors) == 0:
      # Convert actors_data to a list, of actor dicts
      game.location_data['actors_data'] = []
      
      # Set the level text
      SetGameplayText(game, wave_data['name'], 4)
      
      # Set the next actor time
      #TODO(g): Wait for the player to start this...  For the final version, but for demo, just a delay is better.
      game.location_data['next_actor_time'] = time.time() + current_actor_set_data['start_delay']
      game.location_data['actor_set_released'] = 0
    
    
    # If we have a current actor set, and it's time to release another actor
    if current_actor_set_data != None and game.location_data['next_actor_time'] < time.time() and game.location_data['next_actor_time'] != 0:
      #if current_actor_set_data > game.location_data['actor_set_released']:
      key = '%s_%s_%s' % (current_actor_set_data['actor'], game.location_data['current_actor_set'], game.location_data['actor_set_released'])
      # Create the Actor from the actor specification
      actor = dict(game.location_data['actors'][current_actor_set_data['actor']])
      # Append additional information
      actor['key'] = key
      actor['actor'] = current_actor_set_data['actor']
      actor['asset_key'] = 'actor.%s' % current_actor_set_data['actor']
      actor['pos'] = list(game.location_data['actor_start_tile'])
      actor['anim'] = 4
      actor['direction'] = 'east'
      actor['anim_current'] = actor['anim']
      
      # Apply difficulty settings
      actor['health'] = int(actor['health'] * game.location_data['wave_difficulty'])
      actor['velocity'] = actor['velocity'] * game.location_data['wave_difficulty']

      
      # Generate the path for this new actor
      tile_start = AStar.SQ_Location(int(math.floor(actor['pos'][0])), int(math.floor(actor['pos'][1])))
      tile_end = AStar.SQ_Location(game.location_data['actor_end_tile'][0], game.location_data['actor_end_tile'][1])
      actor['path'] = path_finder.findPath(tile_start, tile_end)
      #print 'Created actor: %s' % actor
      
      # Add to actors
      actors[key] = actor
      
      # Increment how many actors we have released
      game.location_data['actor_set_released'] += 1
      if game.location_data['actor_set_released'] >= current_actor_set_data['count']:
        game.location_data['current_actor_set'] += 1
        game.location_data['actor_set_released'] = 0
        
        # If we are out of actor_sets for this wave, go to the Next wave
        if game.location_data['current_actor_set'] >= len(wave_data['actor_sets']):
          # Cash Bonus for completing wave
          print 'Finish wave: Bonus: %s' % wave_data['completion_money']
          game.data['game']['money'] += wave_data['completion_money']
          
          game.location_data['wave'] += 1
          game.location_data['next_actor_time'] = 0
          game.location_data['current_actor_set'] = 0
          
          # If you passed all waves...  Get harder and repeat (TODO)
          if game.location_data['wave'] >= len(game.location_data['waves']):
            # End the game
            game.SelectLocation('win_game')
            raise LocationChange('win')
            
            # SetGameplayText(game, "All waves cleared!", 5)
            # game.location_data['wave'] = 0
            # # Increase difficulty
            # game.location_data['wave_difficulty'] += game.location_data['wave_difficulty_increment_per_post_waves']
            # print 'Flipped waves...'
        
        # Else, we are delaying for the next actor set
        else:
          current_actor_set_data = wave_data['actor_sets'][game.location_data['current_actor_set']]
          game.location_data['next_actor_time'] = time.time() + current_actor_set_data['delay']
      
      # More actors to release in this actor_set
      else:
        # Update the next actor time
        game.location_data['next_actor_time'] = time.time() + current_actor_set_data['delay']


    # Set local operating vars
    tile_size = [game.location_data['tile_size'][0] * game.data['window']['scale'], game.location_data['tile_size'][1] * game.data['window']['scale']]
    
    #TODO(g): Get this time from the game input...
    import time
    secs = int(time.time()*5)

    # Track actors to delete
    delete_actor_list = []

    # Move the actors
    for (actor_key, actor_data) in actors.items():
      #DEBUG(g): Skip path-finding dead actors
      if actor_data['path'] == None:
        continue
      
      # Get the next tile node
      next_node = actor_data['path'].nodes[0]
      
      #print 'pig move: %s: %s' % (next_node, actors['pig']['pos'])
      
      # Remove current nodes
      while next_node != None and next_node.location.x == int(actor_data['pos'][0]) and next_node.location.y == int(actor_data['pos'][1]):
        # Remove the first node, that we are already on
        del actor_data['path'].nodes[0]
        if len(actor_data['path'].nodes) > 0:
          next_node = actor_data['path'].nodes[0]
          #print 'Next node - pig: %s, %s' % (next_node.location.x, next_node.location.y)
        else:
          #print 'Next node - pig: None'
          next_node = None
      
      # If there is somewhere to go, go there
      if next_node != None:
        next_tile = next_node.location
      
        #TODO(g): Normalize vector for proper velocity in each direction
        # X movement
        if next_tile.x < int(actor_data['pos'][0]):
          actor_data['pos'][0] -= actor_data['velocity']
          actor_data['anim'] = 4 # Left
          actor_data['direction'] = 'west'
        elif next_tile.x > int(actor_data['pos'][0]):
          actor_data['pos'][0] += actor_data['velocity']
          actor_data['anim'] = 6 # Right
          actor_data['direction'] = 'east'
      
        # Y movement
        if next_tile.y < int(actor_data['pos'][1]):
          actor_data['pos'][1] -= actor_data['velocity']
          actor_data['anim'] = 0 # Up
          actor_data['direction'] = 'north'
        elif next_tile.y > int(actor_data['pos'][1]):
          actor_data['pos'][1] += actor_data['velocity']
          actor_data['anim'] = 2 # Down
          actor_data['direction'] = 'south'
      
        # Only animate when moving
        #actor_data['anim_current'] = actor_data['anim'] + secs%2
        dir_images = game.data[actor_data['asset_key']]['assets']['walk'][actor_data['direction']]['images_data']
        actor_data['anim_current'] = secs % len(dir_images)
        
      # Else, delete the actor
      else:
        delete_actor_list.append(actor_data['key'])
        game.data['game']['ice_cream'] -= 1
        if game.data['game']['ice_cream'] > 0:
          SetGameplayText(game, 'You lost more ice cream!')
        else:
          #TODO(g): Switch to Lose Game mode
          SetGameplayText(game, 'You are out of ice cream!')
          
          # End the game
          #TODO(g): Go to Lose screen
          game.SelectLocation('lose_game')
          raise LocationChange('lose')
      
    # Delete any actors that have been removed from play
    if delete_actor_list:
      for actor_name in delete_actor_list:
        del actors[actor_name]
    
    
    # Draw the Actors
    for (actor_key, actor_data) in actors.items():
      offset = actor_data['offset']
      dir_images = game.data[actor_data['asset_key']]['assets']['walk'][actor_data['direction']]['images_data']
      image = dir_images[int(actor_data['anim_current'])]
      owr_gfx.Draw(image, surface, [actor_data['pos'][0] * tile_size[0] + offset[0], actor_data['pos'][1] * tile_size[1] + offset[1] - image.get_height()])

      # actor.penguin_small:
      # offset: [0, 0]
        
      # Draw the Rect -- DEBUG
      #owr_gfx.DrawRect([int(actor_data['pos'][0]) * tile_size[0], int(actor_data['pos'][1]) * tile_size[1]], tile_size, [100, 100, 100, 50], surface)
  


def RenderActorsSpeech(game, background):
  """Render the speech bubbles"""



def SetGameplayText(game, text, timeout=4):
  """Set the main UI game play text with timeout.
  TODO(g): Move this somewhere better."""
  print 'Setting text: %s' % text
  game.location_data['gameplay_text'] = text
  game.location_data['gameplay_timeout'] = timeout
  
  # Reset timer
  game.location_data['gameplay_timer'] = None


def ClearGameplayText(game):
  """Clear the gameplay text
  TODO(g): Move this somewhere better."""
  print 'Clearing text'
  game.location_data['gameplay_text'] = None
  game.location_data['gameplay_timeout'] = None
  game.location_data['gameplay_timer'] = None



#GLOBAL(g): The button key (string) the mouse is working on
MOUSE_STATE = None
BUTTON_OVER = []

def ProcessButtonEvent(game, button, button_ticks):
  """Process the button event."""
  button_data = game.location_data['buttons'].get(button, None)
  print 'Button event: %s - %s: %s' % (button, button_ticks, button_data)
  
  global MOUSE_STATE
  
  # Only keep the MOUSE_STATE set to the button if this is an obstacle
  #TODO(g): Terrible UI code, in terms of flexibility...
  if button_data == None or 'obstacle' in button_data:
    MOUSE_STATE = button
  
  # Set the location, as specified
  if button_data and 'set_location' in button_data:
    print 'Setting location: %s' % button_data['set_location']
    game.SelectLocation(button_data['set_location'])


def RenderButtons(game, background):
  # Clear the global button over, we're about to set it again
  global BUTTON_OVER
  BUTTON_OVER = []

  #TODO(g): Remove once things have been worked out...
  global ICONS
  if ICONS == None:
    LoadGlobalIcons(game)

  if 'buttons' not in game.location_data:
    return

  # Draw all buttons
  for (button_key, button_data) in game.location_data['buttons'].items():
    button_over_key = '%s_hover' % button_key
    
    # # Skip hidden buttons
    # if button_data.get('hide', False):
    #   continue
    
    if button_key not in ICONS:
      ICONS[button_key] = owr_image.Load(button_data['image'], scale=game.data['window']['scale'])
    if button_over_key not in ICONS and 'image_hover' in button_data:
      ICONS[button_over_key] = owr_image.Load(button_data['image_hover'], scale=game.data['window']['scale'])
    
    # Is the mouse over this image?
    is_mouse_over = False
    if game.core.input.mousePos[0] >= button_data['pos'][0] * game.data['window']['scale'] and game.core.input.mousePos[0] < button_data['pos'][0] + ICONS[button_key].get_size()[0] * game.data['window']['scale'] and \
        game.core.input.mousePos[1] >= button_data['pos'][1] * game.data['window']['scale'] and game.core.input.mousePos[1] < button_data['pos'][1] + ICONS[button_key].get_size()[1] * game.data['window']['scale']:
      is_mouse_over = True
      BUTTON_OVER.append(button_key)
    
    # Draw the button
    global MOUSE_STATE
    # If the mouse is not hoving
    if not is_mouse_over:
      # If not selected, draw normal button
      if MOUSE_STATE != button_key or 'active_cancel_image' not in button_data:
        owr_gfx.Draw(ICONS[button_key], background, button_data['pos'])
      
      # Else, if available and button was selected, offer cancel icon 
      else:
        # Load image if needed
        if button_data['active_cancel_image'] not in ICONS:
          ICONS[button_data['active_cancel_image']] = owr_image.Load(button_data['active_cancel_image'], scale=game.data['window']['scale'])
        
        # Move to offset, if specified
        if 'active_cancel_image_offset' not in button_data:
          pos = button_data['pos']
        else:

          pos = [button_data['pos'][0] + button_data['active_cancel_image_offset'][0], button_data['pos'][1] + button_data['active_cancel_image_offset'][1]]
        
        owr_gfx.Draw(ICONS[button_data['active_cancel_image']], background, pos)
    
    # Else, mouse is hovering
    else:
      # Render hover image or under-circle
      if 'image_hover' in button_data:
        # If not selected, draw normal button
        owr_gfx.Draw(ICONS[button_over_key], background, button_data['pos'])
      
      # Draw hover-under circle to show option for selection
      else:
        circle_pos = [button_data['pos'][0] + ICONS[button_key].get_size()[0] / 2, button_data['pos'][1] + ICONS[button_key].get_size()[1] / 2]
        owr_gfx.DrawCircle(circle_pos, button_data.get('radius', ICONS[button_key].get_size()[0] / 2), [255, 255, 255, 100], background)
        owr_gfx.Draw(ICONS[button_key], background, button_data['pos'])
      
      # Send event
      #TODO(g): Move into a better place than this
      if game.core.input.mouseButtons[0] == game.core.input.ticks:
        if MOUSE_STATE != button_key:
          ProcessButtonEvent(game, button_key, game.core.input.mouseButtons[0])
        else:
          ProcessButtonEvent(game, None, game.core.input.mouseButtons[0])
    
    # If this has an Obstacle, look for "cost" and render that cost as money
    if 'obstacle' in button_data:
      obstacle = game.location_data['obstacles'][button_data['obstacle']]
      text = '$%d' % obstacle['cost']
      #print '%s - %s' % (button_key, text)
      pos = [button_data['pos'][0] + button_data['cost_offset'][0], button_data['pos'][1] + button_data['cost_offset'][1]]
      owr_image.DrawText(text, 16, game.data['window']['ui_font_color'], pos, background, outline=1,
             outline_color=game.data['window']['ui_font_outline'], font_filename=game.data['window']['ui_font'])
      #owr_image.DrawText(text, 16, game.data['window']['ui_font_color'], pos, background)


def RenderUI(game, background):
  """Render the map"""
  #TILE_SIZE = [game.location_data['tile_size'][0] * game.data['window']['scale'], game.location_data['tile_size'][1] * game.data['window']['scale']]

  #TODO(g): Remove once things have been worked out...
  global ICONS
  if ICONS == None:
    LoadGlobalIcons(game)
  
  #owr_gfx.Draw(ICONS['panel'], background, [game.data['window']['size'][0]-(114*game.data['window']['scale']), 0])
  
  # # Ring for icon selection
  # pos = [game.data['window']['size'][0]/2 - ICONS['gameplay_ring'].get_size()[0]/2, game.data['window']['size'][1] - ICONS['gameplay_ring'].get_size()[1]]
  # owr_gfx.Draw(ICONS['gameplay_ring'], background, pos)
  #  
  # # Icons
  # pos = [720, game.data['window']['size'][1] - 50]
  # owr_gfx.Draw(ICONS['gameplay_sound'], background, pos)
  # 
  # pos = [780, game.data['window']['size'][1] - 50]
  # owr_gfx.Draw(ICONS['gameplay_pause'], background, pos)
  # 
  # pos = [840, game.data['window']['size'][1] - 50]
  # owr_gfx.Draw(ICONS['gameplay_faster'], background, pos)
  # 
  # pos = [900, game.data['window']['size'][1] - 50]
  # owr_gfx.Draw(ICONS['gameplay_fullscreen'], background, pos)
  
  
  # HUD
  pos = [840, -5]
  owr_gfx.Draw(ICONS['gameplay_icecream'], background, pos)


  # Render the buttons for this location
  RenderButtons(game, background)
      
  
  if 0:
    # Wave count
    text = 'Wave %s' % (game.location_data['wave'] + 1)
    owr_image.DrawText(text, 30, game.data['window']['ui_font_color'], [50, game.data['window']['size'][1]-50], background, align_flag=0, outline=3,
               outline_color=game.data['window']['ui_font_outline'], width=-1, effect=0, effectPer=1.0, rectDim=None,
               font_filename=game.data['window']['ui_font'])
    
    # Money
    text = '$%s' % game.data['game']['money']
    owr_image.DrawText(text, 30, game.data['window']['ui_font_color'], [0, game.data['window']['size'][1]-40], background, align_flag=1, outline=3,
               outline_color=game.data['window']['ui_font_outline'], width=-1, effect=0, effectPer=1.0, rectDim=None,
               font_filename=game.data['window']['ui_font'])
    
    # Score
    text = '%s' % game.data['game']['score']
    owr_image.DrawText(text, 40, game.data['window']['ui_font_color'], [0, 15], background, align_flag=1, outline=3,
               outline_color=game.data['window']['ui_font_outline'], width=-1, effect=0, effectPer=1.0, rectDim=None,
               font_filename=game.data['window']['ui_font'])
    
    # Ice Cream
    text = '%s' % game.data['game']['ice_cream']
    owr_image.DrawText(text, 40, game.data['window']['ui_font_color'], [900, 15], background, align_flag=0, outline=3,
               outline_color=game.data['window']['ui_font_outline'], width=-1, effect=0, effectPer=1.0, rectDim=None,
               font_filename=game.data['window']['ui_font'])
    
    
    # If we have text we want to draw
    if game.location_data['gameplay_text']:
      # If we havent started the timer yet
      if game.location_data['gameplay_timer'] == None:
        game.location_data['gameplay_timer'] = time.time() + game.location_data['gameplay_timeout']
      
      # Clear if the timer has expired, or keep going
      if game.location_data['gameplay_timer'] < time.time():
        ClearGameplayText(game)
      else:
        owr_image.DrawText(game.location_data['gameplay_text'], 40, game.data['window']['ui_font_color'], [0, 125], background, align_flag=1, outline=0,outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None, font_filename=None)
  
  
  # If we dont have a Player yet, get their name
  if game.player == None:
    
    if 0:
      ui_back = owr_image.Load('data/ui/board_500.png')
      owr_gfx.Draw(ui_back, background, (70,55))
      
      ui_back_slot = owr_image.Load('data/ui/board_500_slot_61.png')
      ui_back_slot_small = owr_image.Load('data/ui/board_500_slot_35.png')
      ##owr_gfx.Draw(ui_back_slot, background, (70+30,55+75))
      owr_gfx.Draw(ui_back_slot, background, (70+30,55+145))
      ##owr_gfx.Draw(ui_back_slot, background, (70+30,55+215))
      ##owr_gfx.Draw(ui_back_slot, background, (70+30,55+285))
    
      
      owr_image.DrawText('Whats yo name, bitch?', 35, (255, 255, 255), (100,80), background,
                         outline=1)
      
      owr_image.DrawText(game.core.input.GetAutoString() + '|', 35, (255, 255, 255),
                         (70+30+15, 55+145+15), background, outline=1)
      
      # If we have a name entered
      if game.core.input.GetNewEnteredString():
        name = game.core.input.GetNewEnteredString()
        
        # Create the player
        game.player = owr_player.Player(game, name)
        ## The player is here, update visibility
        #game.map.UpdateVisibility()
    else:
      game.player = owr_player.Player(game, 'Alex')

  # If we have a player
  if game.data['game']['player_actor'] and game.player:
    # Get the kind of terrain being touched now
    color = game.location_data['mask'].get_at((int(game.player.pos.x/3), int(game.player.pos.y/3)))
    index = game.location_data['mask'].map_rgb(color)
    #Log('Pos: %s  Color: %s  Index: %s' % (game.player.pos, color, index))
    #terrain = game.location_data['assets']['background']['masks']['walkable']['palette'][index]
    
    direction = str(game.player.look_direction)
    
    #owr_image.DrawText(game.core.input_text + ' - ' + game.player.action + ' - ' + terrain + ' - ' + direction, 35, (0, 0, 0), (50,390), background,
    #               outline=1)
    
    #TODO(g): Remove once things have been worked out...
    if ICONS == None:
      LoadGlobalIcons(game)
    
    # Draw the input history icons
    for count in range(0, len(game.player.input_history)):
      input_text = game.player.input_history[count]
      if 'right+up' in input_text:
        owr_gfx.Draw(ICONS['right+up'], background, (50+count*40, 445))
      elif 'right+down' in input_text:
        owr_gfx.Draw(ICONS['right+down'], background, (50+count*40, 445))
      elif 'left+up' in input_text:
        owr_gfx.Draw(ICONS['left+up'], background, (50+count*40, 445))
      elif 'left+down' in input_text:
        owr_gfx.Draw(ICONS['left+down'], background, (50+count*40, 445))
      elif 'right' in input_text:
        owr_gfx.Draw(ICONS['right'], background, (50+count*40, 445))
      elif 'left' in input_text:
        owr_gfx.Draw(ICONS['left'], background, (50+count*40, 445))
      elif 'up' in input_text:
        owr_gfx.Draw(ICONS['up'], background, (50+count*40, 445))
      elif 'down' in input_text:
        owr_gfx.Draw(ICONS['down'], background, (50+count*40, 445))

      if 'button1' in input_text:
        owr_gfx.Draw(ICONS['button1'], background, (50+count*40, 405))
      if 'button2' in input_text:
        owr_gfx.Draw(ICONS['button2'], background, (50+count*40, 365))
  
  
  # If there is a dialobue going on, render it
  if game.dialogue:
    game.dialogue.Render(background)
  
  #if 0:
  #  # Get the cursor tile position
  #  pos = GetMapOffsetTilePos(game)
  #  pos[0] += game.mouse.pos[0] / TILE_SIZE
  #  pos[1] += game.mouse.pos[1] / TILE_SIZE
  #  
  #  cursor_pos = ((game.mouse.pos[0] - game.mouse.pos[0] % TILE_SIZE),
  #                (game.mouse.pos[1] - game.mouse.pos[1] % TILE_SIZE))
  #  
  #  Log('Map Pos: %s = %s.  %s' % (str(pos), game.map.GetPosData(pos), str(cursor_pos)))
  #  
  #  # Draw the tile cursor
  #  cursor = owr_image.Load(owr_data.UI['cursor_tile'], colorkey=(0,255,0))
  #  owr_gfx.Draw(cursor, background, cursor_pos)


def RenderPointer(game, background):
  """Render the mouse pointer"""
  #TODO(g): Remove once things have been worked out...
  global ICONS
  if ICONS == None:
    LoadGlobalIcons(game)
  
  global MOUSE_STATE
  if MOUSE_STATE != None:
    if 'buttons' in game.location_data:
      # Draw a button active mouse image pointer, if specified
      found_active_mouse_image = False
      for (button_key, button) in game.location_data['buttons'].items():
        # If we have an active mouse image
        if 'active_mouse_image' in button and button['active_mouse_image'] not in ICONS:
          ICONS[button['active_mouse_image']] = owr_image.Load(button['active_mouse_image'], scale=game.data['window']['scale'])
    
          owr_gfx.Draw(ICONS[button['active_mouse_image']], background, game.core.input.mousePos)
          found_active_mouse_image = True
        
      # If no active mouse image was found, render the normal mouse
      if not found_active_mouse_image:
        owr_gfx.Draw(ICONS['mouse'], background, game.core.input.mousePos)
    
    # Else, draw normal mouse
    else:
      owr_gfx.Draw(ICONS['mouse'], background, game.core.input.mousePos)
  else:
    owr_gfx.Draw(ICONS['mouse'], background, game.core.input.mousePos)
  

def LoadGlobalIcons(game):
  global ICONS
  ICONS = {
    # 'right+up':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_up_right_blue.png'),
    # 'left+up':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_up_left_blue.png'),
    # 'right+down':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_down_right_blue.png'),
    # 'left+down':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_down_left_blue.png'),
    # 'right':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_right_blue.png'),
    # 'left':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_left_blue.png'),
    # 'up':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_up_blue.png'),
    # 'down':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/arrow_down_blue.png'),
    # 'button1':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/bullet_ball_green.png'),
    # 'button2':owr_image.Load('/Users/ghowland/Documents/projects/rob/data/ui/input/bullet_square_blue.png'),
    'mouse':owr_image.Load('data/defense/cursor_s.png', scale=game.data['window']['scale']),
    'bullet':owr_image.Load('data/defense/actors/bullet_00.png', scale=game.data['window']['scale']),
    'gameplay_ring':owr_image.Load('data/defense/ui/gameplay/ui_background_arc.png', scale=game.data['window']['scale']),
    # 'gameplay_sound':owr_image.Load('data/defense/ui/gameplay/icon_sound.png', scale=game.data['window']['scale']),
    # 'gameplay_pause':owr_image.Load('data/defense/ui/gameplay/icon_pause.png', scale=game.data['window']['scale']),
    # 'gameplay_faster':owr_image.Load('data/defense/ui/gameplay/icon_fastforward.png', scale=game.data['window']['scale']),
    # 'gameplay_fullscreen':owr_image.Load('data/defense/ui/gameplay/icon_expand.png', scale=game.data['window']['scale']),
    'gameplay_icecream':owr_image.Load('data/defense/ui/gameplay/icon_ice_cream.png', scale=game.data['window']['scale']),
    # 'purchase_snowball':owr_image.Load('data/defense/ui/purchase/btn_weapon_1.png', scale=game.data['window']['scale']),
    # 'purchase_harpoon':owr_image.Load('data/defense/ui/purchase/btn_weapon_2.png', scale=game.data['window']['scale']),
    # 'purchase_turret':owr_image.Load('data/defense/ui/purchase/btn_weapon_3.png', scale=game.data['window']['scale']),
    # 'purchase_wall':owr_image.Load('data/defense/ui/purchase/btn_wall.png', scale=game.data['window']['scale']),
  }

