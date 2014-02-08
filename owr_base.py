#!/usr/bin/env python


import math


class PositionInertia():
  """Movement physics information for controlling a Position."""
  def __init__(self, x=0, y=0, height=0):
    self.Reset(x, y, height)


  def Reset(self, x=0, y=0, height=0):
    """Reset all our values: Inertia"""
    self.is_reset = True

    self.x = x
    self.y = y
    #TODO(G): Convert this to 3D XZ/Y when I switch to 3D.  I dont want to change everything now.
    self.height = height


  def IsReset(self):
    """Returns True if it is 0,0,0"""
    return self.is_reset


  def ApplyForce(self, x, y, height):
    """Apply an Acceleration."""
    self.is_reset = False

    self.x += x
    self.y += y
    self.height += height


  def UpdatePosition(self, position):
    """Takes a Position object to update.  This allows one force to be applied to many Positions. (Why?)"""
    position.Move(self.x, self.y, self.height)


  def Duplicate(self):
    """Return a new PositionInertia that duplicates this one"""
    duplicate = PositionInertia(self.x, self.y, self.height)
    return duplicate



class Position:
  """x, y, height.  2D Position information"""
  
  def __init__(self, x=0, y=0, height=0, inertia=None):
    self.x = x
    self.y = y

    #TODO(g): Not aligned in XYZ format, fix
    self.height = height

    # If we dont already have inertia, create a new one
    if inertia == None:
      self.inertia = PositionInertia()

    # Else, duplicate the one passed in.  We dont want its values to change, because this is a 
    #   new position and needs its own physics
    else:
      self.inertia = inertia.Duplicate()

    # Unit direction vector for when Move() commands are used
    self.direction_x = 0
    self.direction_y = 0

    # Save total distance traveled from Move() commands, for animation purposes
    self.traveled = 0


  def __repr__(self):
    output = '(%0.2f, %0.2f)' % (self.x, self.y)
    return output


  def __getitem__(self, item):
    if item == 0:
      return self.x
    elif item == 1:
      return self.y
    else:
      raise IndexError('Position only has 0,1 indexes (x,y): %s' % item)


  def __setitem__(self, item, value):
    if item == 0:
      self.x = value
    elif item == 1:
      self.y = value
    else:
      raise IndexError('Position only has 0,1 indexes (x,y): %s' % item)


  def IsSame(self, pos):
    if type(pos) in (tuple, list):
      if self.x == pos[0] and self.y == pos[1]:
        return True
      else:
        return False
    else:
      if self.x == pos.x and self.y == pos.y and self.height == pos.height:
        return True
      else:
        return False


  def ToList(self):
    return [self.x, self.y]

  
  def Duplicate(self):
    clone = Position(self.x, self.y, self.height, self.inertia)

    clone.traveled = self.traveled
    clone.direction_x = self.direction_x
    clone.direction_y = self.direction_y

    return clone


  def Move(self, x, y, height):
    """Move this position by specified amounts"""
    self.x += x
    self.y += y
    self.height += height


  def MoveTowardPos(self, target, distance):
    """Travel towards a position by the specified distance, from current position."""
    dx = target[0] - self.x
    dy = target[1] - self.y

    total_distance = math.sqrt(dx*dx + dy*dy)

    if total_distance != 0.0:
      unit_dx = dx / total_distance
      unit_dy = dy / total_distance
    else:
      unit_dx = 0.0
      unit_dy = 0.0


    # Remember direction of movement, so that animation positioning can be done
    self.direction_x = unit_dx
    self.direction_y = unit_dy

    move_x = unit_dx * distance
    move_y = unit_dy * distance

    self.x += move_x
    self.y += move_y

    # We have traveled further
    self.traveled += distance

    # print 'Move: %0.2f %0.2f  -- %0.2f -- %0.2f %0.2f -- %0.2f' % \
    #       (dx, dy, total_distance, move_x, move_y, self.GetDistance(target))



  def GetDistance(self, target):
    """Pythagorean theorum."""
    dx = abs(target[0] - self.x)
    dy = abs(target[1] - self.y)
    
    distance = math.sqrt(dx*dx + dy*dy)
    
    return distance


def GetLineBetweenPositions(source, target):
  """Get all the positional points between source and target."""
  source = list(source)
  target = list(target)
  
  points = []
  
  dx = float(target[0] - source[0])
  dy = float(target[1] - source[1])

  points.append(list(source))
  
  # If more horizontal
  if abs(dx) > abs(dy):
    slope = dy / dx
    b = source[1] - slope * source[0]
    
    if dx < 0:
      dx = -1
    else:
      dx = 1
    
    while source[0] != target[0]:
      source[0] += dx;
      y = int(slope * source[0] + b)
      points.append([source[0], y])
  
  # Else, more vertical
  else:
    slope = dx / dy
    b = source[0] - slope * source[1]
    
    if dy < 0:
      dy = -1
    else:
      dy = 1
    
    while source[1] != target[1]:
      source[1] += dy;
      x = int(slope * source[1] + b)
      points.append([x, source[1]])

  return points


def GetDistance(source, target):
  """Pythagorean theorum."""
  dx = abs(target[0] - source[0])
  dy = abs(target[1] - source[1])
  
  distance = math.sqrt(dx*dx + dy*dy)
  
  return distance


if __name__ == '__main__':
  # Test line drawing
  source = [5, 5]
  target = [10, 5] # Horizontal line
  #target = [0, 5] # Horizontal line: Reverse
  #target = [5, 0] # Vertical line
  #target = [5, 10] # Vertical line: Reverse
  #target = [10, 10] # Diagonal
  target = [0, 0] # Diagonal: Reverse
  #target = [7, 13] # Odd 1
  #target = [7, 17] # Odd 2
  target = [13, 7] # Odd 3
  target = [17, 7] # Odd 4
  
  source = [42 ,17]
  target = [44, 24]
  
  if 1:
    points = GetLineBetweenPositions(source, target)
    print points
  elif 1:
    print '%s -> %s' % (source, target)
    print GetDistance(source, target)
  
