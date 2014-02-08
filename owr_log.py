#!/usr/bin/env python

LEVEL_DEBUG = 0
LEVEL_WARN = 25
LEVEL_ERROR = 75
LEVEL_CRITICAL = 100


LEVEL_TEXT = {
  LEVEL_DEBUG:'DEBUG',
  LEVEL_WARN:'WARN',
  LEVEL_ERROR:'ERROR',
  LEVEL_CRITICAL:'CRITICAL',
}


LAST_LOGGED = None


def Log(text, status=LEVEL_DEBUG):
  global LAST_LOGGED
  
  # If we just printed this last text item, dont print it again to save on
  #   repeats
  if text != LAST_LOGGED:
    print '%s: %s' % (LEVEL_TEXT[status], text)
    
    # Save the text we last logged...
    LAST_LOGGED = text

