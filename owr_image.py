#!/usr/bin/env python

"""
OWR: Image

Functions for dealing with images.
"""


import pygame
from pygame.locals import *
import pygame.surfarray
import os

import owr_log as log
from owr_log import Log


IMAGES = {}
FONTS = {}


# File to get our default font from
UI_DATA_FONT = 'data/ui/ui_font.txt'

# Default font if the data file doesnt exist
DEFAULT_FONT = 'data/fonts/tahoma.ttf'


def InitializeGraphics(core):
  pygame.init()
  
  # Set window title
  pygame.display.set_caption(core.title)
  
  # Create the core screen
  core.screen = pygame.display.set_mode(core.size)
  
  # Turn off mouse, if set
  if core.data['game'].get('hide_mouse', 1):
    pygame.mouse.set_visible(0)
  
  # If we have an icon, set it
  if 'icon' in core.data['window']:
    #NOTE(g): This can and should be set before the mode is set, but image.convert_alpha() needs help because the mode hasnt been set yet, so cant use defaults
    pygame.display.set_icon(Load(core.data['window']['icon']))
  
  # Replace the default font with a specified one from a data file, if it exists
  if os.path.isfile(UI_DATA_FONT):
    log.Log('Testing UI Font data: %s' % UI_DATA_FONT)
    fontfile = open(UI_DATA_FONT).read().strip()
    log.Log('Testing UI Font file: %s' % fontfile)
    # If this is a real file, then set it as the new default
    if os.path.isfile(fontfile):
      global DEFAULT_FONT
      DEFAULT_FONT = fontfile
      log.Log('Swtiching default font: %s' % fontfile)


def Save(surface, filename):
  """Save the surface to the filename"""
  print 'Saving: %s' % filename
  pygame.image.save(surface, filename)


def Load(filename, colorkey=None, convert=True, scale=None, flip_x=False, flip_y=False):
  """Load an image"""
  global IMAGES
  
  if filename not in IMAGES:
    log.Log('Loading: %s' % filename)
    
    try:
      image = pygame.image.load(filename)
    except pygame.error, message:
      print 'Cannot load image:', filename
      raise SystemExit, message
    
    if colorkey is not None:
      if type(colorkey) in (list, tuple):
        colorkey = image.get_at(colorkey)
      print 'Setting color key: %s - %s' % (filename, colorkey)
      image.set_colorkey(colorkey)
      #image.set_colorkey(colorkey, RLEACCEL)
    
    if convert:
      image = image.convert_alpha()
    
    IMAGES[filename] = image
  
  else:
    image = IMAGES[filename]

  # If we have to scale
  if scale != None:
    # (size_x, size_y) = image.get_size()
    # size_x *= scale
    # size_y *= scale

    # # Scale the image
    # #Log('Image: Scaling: %s' % SCALE)
    # #TODO(g): CACHE: Slow!
    # image = pygame.transform.scale(image.copy(), (int(size_x), int(size_y)))

    image = ScaleImage(image, scale)
  
  # If we want to flip the image horizontally or vertically
  if flip_x or flip_y:
    image = pygame.transform.flip(image.copy(), flip_x, flip_y)
  
  return image


def ScaleImage(image, scale):
  """Scales image (pygame.Surcfce), by scale (float)"""
  (size_x, size_y) = image.get_size()
  size_x *= scale
  size_y *= scale

  # Scale the image
  #Log('Image: Scaling: %s' % SCALE)
  #TODO(g): CACHE: Slow!
  image = pygame.transform.scale(image.copy(), (int(size_x), int(size_y)))

  return image


def GetFont():
  if pygame.font:
    font = pygame.font.Font(None, 36)
    return font
  else:
    return None


def GetPixel(image, pos):
  if 1:
    buffer = pygame.surfarray.pixels2d(image)
    
    try:
      pixel = buffer[pos[0]][pos[1]]
    except IndexError, e:
      #TODO(g): Error here?
      pixel = -1
  elif 0:
    buffer = image.get_buffer()
    
    width = image.get_width()
    height = image.get_height()
    bytesize = image.get_bytesize()
    runlength = width * bytesize
    
    pixel = buffer[(pos[1] * runlength) + (pos[0] * bytesize)]
  
  else:
    pixel = image.get_at(pos)
  
  return pixel


def GetImageBuffer(image):
  """Returns an array of the values for this image."""
  buffer = pygame.surfarray.pixels2d(image)
  
  return buffer


def GetFontWidth(text, size, font_filename=None):
  if font_filename == None:
    font_filename = DEFAULT_FONT
  
  font = GetFont(font_filename, size)

  # If there is no font system, return
  if not pygame.font:
    raise Exception('Pygame Fonts not found')

  text_font = font.render(text, 1, (255, 255, 255))

  width = text_font.get_width()

  return width


def GetFont(font_filename, size):
  # Initialize the font for sizes to be saved in it
  if font_filename not in FONTS:
    FONTS[font_filename] = {}
  
  # See if the font we need is in the dictionary
  if size not in FONTS[font_filename]:
    FONTS[font_filename][size] = pygame.font.Font(font_filename, size)
  
  font = FONTS[font_filename][size]

  return font


def DrawText(text, size, color, pos, surface, align_flag=0, outline=0,
             outline_color=0, width=-1, effect=0, effectPer=1.0, rectDim=None,
             font_filename=None):
  """Draw text of a given font size onto a surface"""
  # Initialize the offset
  offset = [0, 0]

  # Initialize counter
  count = 0
  
  if font_filename == None:
    font_filename = DEFAULT_FONT
  
  # If there is no font system, return
  if not pygame.font:
    raise Exception('Pygame Fonts not found')
 
  # If there is no string, return
  if text == '':
    return offset
  
  font = GetFont(font_filename, size)
  
  # Determine the rect size.  May have been passed an argument, otherwise use the surface
  if rectDim is None:
    rectDim = (0, 0, surface.get_width(), surface.get_height())
  
  # Split the text into lines
  if text.find("\n", 0 ) != -1:
    lines = text.split("\n")
  else:
    lines = text.split("\\n")
 
  # There is an effect
  if effect != 0:
    # If effect is vertical stretch
    if effect == 1:
      # If the percentage is over half
      if effectPer > 0.5:
        # Invert effect percentage, so it goes down again
        effectPer = 0.5 - (effectPer - 0.5)
      # Find scale
      scale = 1.0 + (0.17 * effectPer)
  
  # Loop through the lines
  for source_line in lines:
    # Check to see if this line is too long
    wrap_list = []	# Wrapped sentence list
    
    # If the width of this line is too big for our drawing width
    if font.size(source_line)[0] > rectDim[2]:
      # Split the line by spaces, and add a word each time checking if it is now too long
      words = source_line.split(' ')
      last_sentence = test_sentence = last_word = ''
      # Loop until we are out of words
      while len(words) > 0:
        last_sentence = test_sentence		# Save the last sentence
        last_word = words[0]				# Get the first word left in the list
        words.remove (last_word)			# Remove the word we just took from the list
        if test_sentence != '':
          test_sentence += " "			# Add space gap, if this isnt a fresh new sentence
        test_sentence += "%s" % last_word	# Add the word to the test sentence
        # If the test sentence is now too long
        if font.size(test_sentence)[0] > rectDim[2]:
          words.insert(0, last_word)		# Put the last word into the word list again, cause it's over the limit
          wrap_list.append(last_sentence)# Add the last sentence that was under the width to the wrapped sentence list
          last_sentence = test_sentence = last_word = ''
      # If the test sentence isnt blank, add it to the wrap list
      if test_sentence != '':
        wrap_list.append(test_sentence)
    # Else, it fits so just add the source line to our wrapped sentence list and move on
    else:
      wrap_list.append(source_line)
    
    # We now have a list of wrapped sentences.  Cycle through these to print them out
    for line in wrap_list:
      # If this isn't a blank line - No point in drawing blank lines
      if line != '':
        # If the text alignment should be centered
        if align_flag == 1:
          font_size = font.size(line)
          # If the width is not specified, use the Surface width
          if width == -1:
            offset[0] = (rectDim[2] / 2) - (font_size[0] / 2)
          # Else, use the specified width
          else:
            offset[0] = (width / 2) - (font_size[0] / 2)
        
        # If the text should be drawn with a black outline
        if outline == 1 or outline == 2 or outline == 3:
          # Set data_flag_data to black value if not provided
          if outline_color == 0:
            outline_color = (0,0,0,255)
          
          # Render the font
          text_font = font.render(line, 1, outline_color)
          
          
          # If effect is vertical stretch
          if effect == 1:
            text_font = pygame.transform.scale(text_font, (text_font.get_width(), float(text_font.get_height()) * scale))
          
          
          # Blit the font - offset and line number adjusted
          if outline == 1 or outline == 2:
            surface.blit(text_font, (pos[0] + offset[0] + 1, pos[1] + offset[1] + 1 + (size * count * 1.3)))
          if outline == 2:
            surface.blit(text_font, (pos[0] + offset[0] + 2, pos[1] + offset[1] + 2 + (size * count * 1.3)))
          # Thick outline, wastefully rendering 4x...
          if outline == 3:
            surface.blit(text_font, (pos[0] + offset[0] - 2, pos[1] + offset[1] + (size * count * 1.3)))
            surface.blit(text_font, (pos[0] + offset[0] + 2, pos[1] + offset[1] + (size * count * 1.3)))
            surface.blit(text_font, (pos[0] + offset[0], pos[1] + offset[1] - 1 + (size * count * 1.3)))
            surface.blit(text_font, (pos[0] + offset[0], pos[1] + offset[1] + 1 + (size * count * 1.3)))
          
        # Render the font
        text_font = font.render(line, 1, color)
        
        # If effect is vertical stretch
        if effect == 1:
          # If we havent already done this above in the flags
          if outline == 0:
            oldHeight = text_font.get_height()
            newHeight = text_font.get_height()
            offset[1] -= (newHeight-oldHeight) / 2
        
        # Blit the font - offset and line number adjusted - Also add the rectangle size we wanted to use for this writing (since we may want to draw in a portion of the surface, and treat it as a whole surface)
        surface.blit(text_font, (rectDim[0] + pos[0] + offset[0], rectDim[1] + pos[1] + offset[1] + (size * count * 1.2)))
        
      # Increment the counter
      count += 1
   
  # Return the offset and count information
  return (offset, count)


def GetAnimationFrames(info, scale):
  """Get the animation frames, from this animation frame info dictionary."""
    #images: ["data/images/alex.png"]
    #frame_size: [60, 40]
    #frames: [[0,0]]
    #loop: none
    #speed: still
    #movement: still
  
  images = []
  
  SCALE = scale
  
  # If we only have one image, and are cutting frames out of it
  if 'frames' in info:
    master_image = Load(info['images'][0])
    
    if 1:
      # Load each of our frames
      for count in range(0, len(info['frames'])):
        frame = info['frames'][count]
        
        # If we want to crop part of this image
        if 'frame_size' in info:
          area = None
          
          # Set up short variables for the area algorithm
          fsx = info['frame_size'][0]
          fsy = info['frame_size'][1]
          
          fx = frame[0]
          fy = frame[1]
          
          # If we have an offset to use to find the area
          if 'frame_offset_size' in info:
            size = info['frame_offset_size'][count]
            
            # If there is an offset for this frame count
            if size:
              (fsx, fsy) = size
          
          # If we have an offset to use to find the area
          if 'frame_offset' in info:
            offset = info['frame_offset'][count]
            
            # If there is an offset for this frame count
            if offset:
              (offset_x, offset_y) = offset
              
              area = [offset_x, offset_y, offset_x + fsx, offset_y + fsy]
          
          
          # If we havent set area yet, there is no frame offset, use the frame
          #   position info
          if area == None:
            # Calculate the clipping area for this frame
            area = [fx * fsx, fy * fsy, (fx+1) * fsx, (fy+1) * fsy]
          
          # Draw from the master into this image, so we have the frame we need
          image = master_image.subsurface(area)
          image = image.copy()
          
        # Else, there is no frame size, so take the entire master image
        else:
          Log('Image: %s  No frame cutting, taking image from master image' % info['images'][0])
          image = master_image
      
      # Else, there is no frame size, so take the entire master image
      else:
        Log('Image: %s  No frames, taking image from master image' % info['images'][0])
        image = master_image
      
      # If we have to scale
      if SCALE != 1.0:
        (size_x, size_y) = image.get_size()
        size_x *= SCALE
        size_y *= SCALE
        
        # Scale the image
        #Log('Image: Scaling: %s' % SCALE)
        #TODO(g): CACHE: Slow!
        image = pygame.transform.scale(image.copy(), (int(size_x), int(size_y)))
      
      # Add the final image to the images list
      images.append(image)
  
  
  # Else, we are using a different image file per animation
  else:
    for filename in info['images']:
      image = Load(filename)
      image.convert_alpha()
      #Log('Image: %s  No frames.' % filename)
      
      # If we have to scale
      if SCALE != 1.0:
        (size_x, size_y) = image.get_size()
        size_x *= SCALE
        size_y *= SCALE
        
        # Scale the image
        #Log('Image: Scaling: %s' % SCALE)
        #TODO(g): CACHE: Slow!
        image = pygame.transform.scale(image.copy(), (int(size_x), int(size_y)))
      
      # Add the final image to the images list
      images.append(image)
  
  return images



def GetTileFrames(info, scale):
  """Get the animation frames, from this animation frame info dictionary."""
  images = []
  
  SCALE = scale
  
  if 'color_key' in info:
    master_image = Load(info['images'][0], info['color_key'])
  else:
    master_image = Load(info['images'][0])
  
  # Load each of our frames
  for count in range(0, len(info['frames'])):
    frame = info['frames'][count]
    
    # If we want to crop part of this image
    if 'frame_size' in info:
      area = None
      
      # Set up short variables for the area algorithm
      fsx = info['frame_size'][0]
      fsy = info['frame_size'][1]
      
      fx = frame[0]
      fy = frame[1]
      
      area = [fx * fsx, fy * fsy, fsx, fsy]
      
      # Draw from the master into this image, so we have the frame we need
      image = master_image.subsurface(area)
      image = image.copy()
      
    # Else, there is no frame size, so take the entire master image
    else:
      Log('Image: %s  No frame cutting, taking image from master image' % info['images'][0])
      image = master_image
  
    # If we have to scale
    if SCALE != 1.0:
      (size_x, size_y) = image.get_size()
      size_x *= SCALE
      size_y *= SCALE
    
      # Scale the image
      #Log('Image: Scaling: %s' % SCALE)
      #TODO(g): CACHE: Slow!
      image = pygame.transform.scale(image.copy(), (int(size_x), int(size_y)))
  
    # Add the final image to the images list
    images.append(image)
  
  
  return images






if __name__ == '__main__':
  #NOTE(g):BROKEN: This test doesnt work any more.  Will take some minor modifications to fix that.
  
  # Fake up a core object
  class Core:
    """"""
  core = Core()
  core.size = [640, 480]
  core.title = 'Testing image module'
  
  InitializeGraphics(core)
  
  alex = Load('/Users/ghowland/Documents/projects/owr.yaml/data/images/alex.png')
  import owr_gfx
  #owr_gfx.DrawBlack(core.screen, [0,0], core.size)
  owr_gfx.Draw(alex, core.screen, [0,0])
  
  # Make background visible
  pygame.display.flip()
  
  import time
  time.sleep(3)


