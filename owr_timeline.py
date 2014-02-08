"""
Timeline Data

Generic container for manipulating Timeline Data.
"""


import os
import yaml


# This holds default data for items, so creating new ones can use these.  Doesnt include start/duration.
DEFAULTS = {
  # Camera Default Data
  'camera': {
    'type':None, # Normal type
    'mode':None, # Normal mode
  },

  # Dialog Default Data
  'dialog': {
    'text':'',
    'font':None,
    'size':None,
    'offset':None,
    'alignment':None,
  },
}


class TimelineData:
  """Load, Save, Get Data for a Specific time."""

  def __init__(self, path, create=True):
    self.path = path

    self.data = None

    # Load our data
    self.Load(create=create)



  def __repr__(self):
    """Text Representation"""
    output = 'TimelineData: %s' % self.path
    if data:
      output += '  Items: %s' % len(data)
    output += '\n'

    return output


  def Load(self, path=None, create=False):
    """Load the specified data

    Args:
      path: string, if None then uses self.path
      create: boolean, if True will create Empty List and save to path
    """
    # Clear the data, since we want to load new data, this ensures we dont see the wrong
    #   data/path combination in case of an exception on load
    self.data = None

    # If we didnt get it as an arg, use our stored path
    if not path:
      path = self.path
    # Else, store the path so we know where the data came from.  Destroying previous data info
    else:
      self.path = path


    # If path not a valid file
    if not os.path.isfile(path):
      # If we want to create missing data, create an Empty List and save it
      if create:
        self.data = []
        self.Save()

      # Else, no creation so Raise an error
      else:
        raise Exception('Couldnt load Timeline Data object, path is not a file: %s' % path)

    # Else, load the data
    else:
      self.data = yaml.load(open(path))

    return self.data


  def Save(self, path=None):
    """Save the data"""
    # If we didnt get it as an arg, use our stored path
    if not path:
      path = self.path

    # Save the data to our path
    yaml.dump(self.data, open(path, 'w'))

    # Ensure the path is always correct, since we saved it
    self.path = path


  def GetItemsAtTime(self, time_elapsed):
    """Returns a dictionary of all timeline state items whose start/duration
    includes time_elapsed.
    """
    items = []

    if self.data == None:
      raise Exception('TimelineData: Trying to GetState when data==None')

    # Go through each of our items
    for item in self.data:
      # Ignore items that cant be retrieved by time_elapsed
      if 'start' not in item or 'duration' not in item:
        #print 'TimelineData: Skipping Item: %s: %s' % (self.path, item)
        continue

      # If time_elapsed is between start and end of this item
      if time_elapsed >= item['start'] and time_elapsed < item['start'] + item['duration']:
        print 'TimelineData: Found Item: %s: %s' % (self.path, item)
        items.append(item)
      else:
        #print 'TimelineData: Unmatched Item: %s: %s' % (self.path, item)
        pass

    return items

