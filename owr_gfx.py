#!/usr/bin/env python


import pygame

import owr_image


def Draw(source, target, pos, opacity=255, opacity_fill=(255, 255, 255), scale=1.0):
  """Draw the source image onto the target at pos position."""
  if scale != 1.0:
    source = owr_image.ScaleImage(source, scale)

  # Clear opacity, or set it
  if opacity == 255:
    #source.set_alpha(None)
    pass
  else:
    # Bounds force
    if opacity < 0:
      opacity = 0

    #source.set_alpha(opacity)
    new_source = source.copy()
    new_source.fill((opacity_fill[0], opacity_fill[1], opacity_fill[2], opacity), None, pygame.BLEND_RGBA_MULT)
    source = new_source

  target.blit(source, pos)


def DrawBlack(target, pos, size):
  """Draw a black rectangle."""
  target.fill((0,0,0), (pos[0], pos[1], pos[0] + size[0], pos[1] + size[1]))


def Flip(source, xbool=True, ybool=False):
  target = pygame.transform.flip(source, xbool, ybool)
  
  return target


def DrawCircle(pos, radius, color, surface):
  """Draw a circle"""
  canvas = pygame.Surface([radius*2, radius*2], pygame.SRCALPHA)
  
  #pygame.draw.circle(surface, color, pos, radius)
  pygame.draw.circle(canvas, color, [radius, radius], radius)
  
  surface.blit(canvas, [pos[0]-radius, pos[1]-radius])


def DrawRect(pos, size, color, surface, filled=True):
  """Draw a rect"""
  # Draw to the canvas
  if filled:
    # Create the rendering canvas, for alpha effects (which is almost always what we want)
    #print 'DrawRect: %s - %s - %s' % (size, color, pos)
    canvas = pygame.Surface(size, pygame.SRCALPHA)
    #canvas = pygame.Surface(size)
    #canvas.convert_alpha()
    #canvas.fill([0, 255, 255, 255])
    #canvas.fill([0, 0, 0, 0])
    
    pygame.draw.rect(canvas, color, [0, 0, size[0], size[1]])
    #pygame.draw.rect(surface, color, [pos[0], pos[1], size[0], size[1]])
  
    # Draw the canvas to the target surface
    surface.blit(canvas, pos)
  else:
    # Top-Left to Bottom-Left
    width = 2
    pygame.draw.line(surface, color, pos, (pos[0], pos[1] + size[1]), width)
    #print 'Bottom-Left: %s -- %s' % (pos, (pos[0], pos[1] + size[1]))
    # Top-Left to Top-Right
    pygame.draw.line(surface, color, pos, (pos[0] + size[0], pos[1]), width)
    #print 'Top-Right: %s -- %s' % (pos, (pos[0] + size[0], pos[1]))
    # Top-Right to Bottom-Right
    pygame.draw.line(surface, color, (pos[0] + size[0], pos[1]), (pos[0] + size[0], pos[1] + size[1]), width)
    #print 'Bottom-Right: %s -- %s ' % ((pos[0] + size[0], pos[1]), (pos[0] + size[0], pos[1] + size[1]))
    # Bottom-Left to Bottom-Right
    pygame.draw.line(surface, color, (pos[0], pos[1] + size[1]), (pos[0] + size[0], pos[1] + size[1]), width)
    #print 'Bottom-Right2: %s -- %s' % ((pos[0], pos[1] + size[1]), (pos[0] + size[0], pos[1] + size[1]))


def DrawEllipse(pos, size, color, surface, width=0):
  """Draw an ellipse.  width is outline width, 0 is filled"""
  # Create the rendering canvas, for alpha effects (which is almost always what we want)
  canvas = pygame.Surface(size, pygame.SRCALPHA)
  
  # Draw to the canvas
  pygame.draw.ellipse(canvas, color, [0, 0, size[0], size[1]], width)
  
  # Draw the canvas to the target surface
  surface.blit(canvas, pos)



def DrawRoundedRect(surface, rect, color, radius=0.4):
    """
    AAfilledRoundedRect(surface,rect,color,radius=0.4)

    From: http://www.pygame.org/project-AAfilledRoundedRect-2349-.html

    surface : destination
    rect    : rectangle
    color   : rgb or rgba
    radius  : 0 <= radius <= 1
    """
    rect         = pygame.Rect(rect)
    color        = pygame.Color(*color)
    alpha        = color.a
    color.a      = 0
    pos          = rect.topleft
    rect.topleft = (0, 0)
    rectangle    = pygame.Surface(rect.size, pygame.SRCALPHA)

    circle       = pygame.Surface([min(rect.size)*3]*2, pygame.SRCALPHA)
    pygame.draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)

    circle       = pygame.transform.smoothscale(circle, [int(min(rect.size)*radius)]*2)

    radius              = rectangle.blit(circle, (0, 0))
    radius.bottomright  = rect.bottomright
    rectangle.blit(circle,radius)

    radius.topright     = rect.topright
    rectangle.blit(circle,radius)

    radius.bottomleft   = rect.bottomleft
    rectangle.blit(circle,radius)

    rectangle.fill((0, 0, 0), rect.inflate(-radius.w, 0))
    rectangle.fill((0, 0, 0), rect.inflate(0, -radius.h))

    rectangle.fill(color, special_flags=pygame.BLEND_RGBA_MAX)
    rectangle.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)

    return surface.blit(rectangle, pos)
