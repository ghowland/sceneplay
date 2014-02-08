#!/usr/bin/env python

#Import Modules
import os, pygame, string
from pygame.locals import *
from string import *

from owr_log import Log


class InputHandler:
  """Handles input events, holding strings of typed text and current state."""
  
  def __init__(self):
    # Keyboard layout setting default's to dvorak translation being off
    self.CreateDvorak()   # Create the Dvorak keymap
    
    Log('Creating input')
    
    # Setup the keystate and keystateTime initial values
    self.keystate = pygame.key.get_pressed()
    i = 0	# Reset the counter
    self.keystateTime = []
    for key in self.keystate:
      self.keystateTime.insert(0, 0)	# Inserting null values just allows things to be set up for later, so the list is in order
      i += 1
    
    # Variable for Window event close
    self.winClose = 0
    self.winResize = 0
    self.winFullscreenToggle = 0
    self.winFocusGain = 0
    
    
    # Keys currently pressed down making a string.  The idea is that this is normally one, then you can append this string to a name to accept input
    self.keyString = ""
    self.keyStringTime = 0		# ticks when this was last updated
    
    # Automatic string clear
    self.ClearAutoString()
    
    # Default mouse button state.  All off
    self.mouseButtons = [0, 0, 0]
    self.mousePos = [0, 0]
    
    # Joystick
    pygame.joystick.init()		# Initialize the joystick
    self.joyCount = pygame.joystick.get_count()
    if self.joyCount > 0:
      self.joystick = pygame.joystick.Joystick(0)	# Get the first joystick
      self.joystick.init()	
    else:
      self.joystick = None
    self.joyDir = [0, 0]
    self.joyDirTime = [0, 0]
    self.joyButton = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    self.joyButtonTime = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    # Create clock to lock framerate
    self.clock = pygame.time.Clock()
    self.fps = 0
    
    # Set first ticks as 1
    self.ticks = 100
    self.ticksLastInput = 0
    
    # Run update to init all the variables
    self.Update(0)
  
  
  def ClearAutoString(self):
    """Clear the key string, so that we can begin with new characters."""
    # Automatic keystring
    self.autoKeyString = ""
    self.autoKeyStringLast = ""
    self.autoKeyStringTime = 0
    self.autoKeyStringLastTime = 0
  
  
  def ProcessAutoString(self):
    """Process the auto string stuff."""
    # If there are keys now pressed, this frame
    if self.keyString != "" and self.keyStringTime == self.ticks:
      # Add this string to the autostring
      self.autoKeyString += self.keyString
      self.autoKeyStringTime = self.ticks			# Update the time the string changed
    
    # -- Check special keys to handle things
    
    # If the user backspace this frame, and there is 
    if self.keystateTime[K_BACKSPACE] == self.ticks and len(self.autoKeyString) > 0:
      # Remove the last character
      self.autoKeyString = self.autoKeyString[:-1]	# From the beginning, until 1 from the end
      
    # If the user hit return this frame, and there is something to copy
    if self.keystateTime[K_RETURN] == self.ticks and len(self.autoKeyString) > 0:
      # Save the auto string
      self.autoKeyStringLast = self.autoKeyString
      self.autoKeyStringLastTime = self.ticks
      # Clear the current auto string
      self.autoKeyString = ""
      self.autoKeyStringTime = 0
  
  
  def CreateDvorak(self):
    """Create the Dvorak keymap."""
    self.keyMap = {}
    self.keyMap["q"] = "'"
    self.keyMap["w"] = ","
    self.keyMap["e"] = "."
    self.keyMap["r"] = "p"
    self.keyMap["t"] = "y"
    self.keyMap["y"] = "f"
    self.keyMap["u"] = "g"
    self.keyMap["i"] = "c"
    self.keyMap["o"] = "r"
    self.keyMap["p"] = "l"
    self.keyMap["["] = "/"
    self.keyMap["]"] = "="
    self.keyMap["a"] = "a"
    self.keyMap["s"] = "o"
    self.keyMap["d"] = "e"
    self.keyMap["f"] = "u"
    self.keyMap["g"] = "i"
    self.keyMap["h"] = "d"
    self.keyMap["j"] = "h"
    self.keyMap["k"] = "t"
    self.keyMap["l"] = "n"
    self.keyMap[";"] = "s"
    self.keyMap["'"] = "-"
    self.keyMap["z"] = ";"
    self.keyMap["x"] = "q"
    self.keyMap["c"] = "j"
    self.keyMap["v"] = "k"
    self.keyMap["b"] = "x"
    self.keyMap["n"] = "b"
    self.keyMap["m"] = "m"
    self.keyMap[","] = "w"
    self.keyMap["."] = "v"
    self.keyMap["/"] = "z"
    self.keyMap["-"] = "["
    self.keyMap["="] = "]"
  
  
  def TranslateDvorak(self, letter):
    """Translate this character from US101 Keyboard mapping to US Dvorak"""
    if self.keyMap.has_key(letter):
      return self.keyMap[letter]
    else:
      return letter
  
  
  def InputTimeoutReset(self):
    """Reset the inputTimeout"""
    self.ticksLastInput = self.ticks
  
  
  def InputTimeout(self, timeout=15000):
    """Has the input stream timed out?  No more input coming from the player?"""
    if self.ticksLastInput + timeout < self.ticks:
      return 1
    else:
      return 0
  
  
  def Update(self, frameRateLock=0, options={}):
    """Update the input"""
    # Lock the framerate
    self.timeElapse = self.clock.tick(frameRateLock)	# Force at least 60ms to pass between loops, and return the ms since we last called this
    self.fps = self.clock.get_fps()						# Get the frames per second
    if self.timeElapse > 200:
      self.timeElapse = 200							# Lock this as the slowest a frame can process
      
    # Get the time - Time is handled as an input event.  This is the time all elements of the game should use.
    self.ticksLast = self.ticks			# Save the last frame time
    self.ticks = pygame.time.get_ticks()
    
    # Loop through all the events
    for event in pygame.event.get():
      if event.type is QUIT:			# Quit the app
        self.winClose = 1
      elif event.type is VIDEORESIZE:	# Resizing the window
        self.winResize = 1
      elif event.type is VIDEOEXPOSE:	# I assume this means the window is becoming active
        self.winResize = 1			# Treat it like a resize, redraw things
      elif event.type is ACTIVEEVENT:	# ALT-TAB
        self.winFocusGain = 1
      elif event.type is JOYAXISMOTION:	# Joystick - Axis Move
        if event.axis < 2:
          self.joyDir[event.axis] = event.value
          self.joyDirTime[event.axis] = self.ticks
        self.ticksLastInput = self.ticks	# Save the time the user last made an input
      elif event.type is JOYBUTTONUP:		# Joystick - Button Up
        if event.button < 2:
          self.joyButton[event.button] = 0
          self.joyButtonTime[event.button] = 0
        #elif event.button == 9:	# Start button
        #  self.joyButton[2] = 0
        #  self.joyButtonTime[2] = 0
        self.ticksLastInput = self.ticks	# Save the time the user last made an input
      elif event.type is JOYBUTTONDOWN:	# Joystick - Button Down
        if event.button < 2:
          self.joyButton[event.button] = 1
          self.joyButtonTime[event.button] = self.ticks
        #elif event.button == 9:	# Start button
        #  self.joyButton[2] = 1
        #  self.joyButtonTime[2] = self.ticks
        self.ticksLastInput = self.ticks	# Save the time the user last made an input
    
    # Get the key state
    self.keystate = pygame.key.get_pressed()
    
    # Get the mouse data
    self.mousePos = pygame.mouse.get_pos()			# Position
    cur_buttons = pygame.mouse.get_pressed();		# Current button states
    # Update stored states if buttons are down that weren't before
    for button in range (0,2):
      # If the button was pressed, and was not pressed before
      if cur_buttons[button] == 1 and self.mouseButtons[button] == 0:
        self.mouseButtons[button] = self.ticks	# Store the time of this click
        self.ticksLastInput = self.ticks	# Save the time the user last made an input
      elif cur_buttons[button] == 0:
        self.mouseButtons[button] = 0			# Store a zero value, the button is not down
    
    # Get the time of each key states
    i = 0	# Reset the counter
    curKeyString = []
    for key in self.keystate:
      if not key:
        self.keystateTime[i] = 0
      elif self.keystateTime[i] == 0:
        self.keystateTime[i] = self.ticks
        self.ticksLastInput = self.ticks	# Save the time the user last made an input
        
        # Append to key string if its valid
        if i != K_UP and i != K_DOWN and i != K_RIGHT and i != K_LEFT and i != K_ESCAPE and i != K_RETURN and i != K_BACKSPACE and i <= 127:
          curKeyString.append(chr(i))
      
      i += 1	# Increment the counter
    
    # Check for special key combinations
    if self.keystateTime[K_RETURN] == self.ticks and (self.keystateTime[K_LALT] or self.keystateTime[K_RALT]):
      # Set the full screen toggle variable on
      self.winFullscreenToggle = 1
      # Clear the return character.  We dont want to process a normal return
      self.keystateTime[K_RETURN] = 0
    
    # Translate the characters into other key mapping's - If applicable
    if options.has_key('dvorak') and options['dvorak'] == 1 and len(curKeyString) > 0:
      # Convert curKeyString into a string (it was a just a list)
      curKeyString = string.join(curKeyString,"")
      # Init the translated string
      transStr = ""
      # Step through each letter and translate it
      for letter in curKeyString:
        transStr += self.TranslateDvorak(letter)
      
      # Save the converted string
      curKeyString = transStr
    
    # Fix case if shift is being held down
    curKeyString = string.join(curKeyString,"")
    if self.keystate[K_LSHIFT] or self.keystate[K_RSHIFT]:
      curKeyString = curKeyString.upper()
      curKeyString = curKeyString.replace("1", "!")
      curKeyString = curKeyString.replace("2", "@")
      curKeyString = curKeyString.replace("3", "#")
      curKeyString = curKeyString.replace("4", "$")
      curKeyString = curKeyString.replace("5", "%")
      curKeyString = curKeyString.replace("6", "^")
      curKeyString = curKeyString.replace("7", "&")
      curKeyString = curKeyString.replace("8", "*")
      curKeyString = curKeyString.replace("9", "(")
      curKeyString = curKeyString.replace("0", ")")
      curKeyString = curKeyString.replace("[", "{")
      curKeyString = curKeyString.replace("]", "}")
      curKeyString = curKeyString.replace("/", "?")
      curKeyString = curKeyString.replace("=", "+")
      curKeyString = curKeyString.replace("'", "\"")
      curKeyString = curKeyString.replace(",", "<")
      curKeyString = curKeyString.replace(".", ">")
    
    # Compare the keyStrings, if they aren't the same, then its changed and save the new one
    if curKeyString == "":
      self.keyString = ""
      self.keyStringTime = 0
    elif str(self.keyString) != curKeyString:
      self.keyString = curKeyString
      self.keyStringTime = self.ticks
    
    
    # Process the autoString
    self.ProcessAutoString()
    
    return self.timeElapse	# Return the time that passed between the last two frames
  
  
  def ClearInput(self):
    """Clear input such as the autoStrings and the buttons being pressed, so that we don't process them more than once."""
  
  
  def HandleWindowEvents(self, mode, gameScreen):
    """Handle any Windows events that have occurred."""
    # If they want to close the window
    if self.winClose == 1:
      #save_options()
      return								# Exit the game
    # Else, If they want to toggle the screen between fullscreen/windowed
    elif self.winFullscreenToggle == 1:
      self.winFullscreenToggle = 0	# Been handled now
      #gameScreen.fullscreenToggle ()
    # Else, If they have resized the window.  We don't actually allow this, but here it is.
    elif self.winResize == 1:
      self.winResize = 0				# Been handled now (Since we dont allow it)
    # If the user has switched back into focus
    elif self.winFocusGain == 1:
      self.winFocusGain = 0			# Clear it, it's handled
      #gameScreen.updateAll()				# Redraw the whole screen
      # If we're full screen
      #if mode['options']['fullscreen']:
      #  gameScreen.clearFullScreen()	# Draw a black rectangle over the entire screen space, which is larger than the playable area possibly
  
  
  def GetFPS(self):
    """Get the number of Frames Per Second, which is given by the clock."""
    return self.fps


  def IsKeyDown(self, key, once=False):
    if not once and self.keystateTime[key] > 0:
      return True
    elif once and self.keystateTime[key] == self.ticks:
      return True
    else:
      return False


  def GetAutoString(self):
    return self.autoKeyString


  def GetNewEnteredString(self):
    if self.autoKeyStringLastTime == self.ticks:
      return self.autoKeyStringLast
    else:
      return None


