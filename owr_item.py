#!/usr/bin/env python

"""
RPG: Item
"""


import copy

from owr_log import Log


class Item:
  """All things that are heald, worn, used, drank, eaten or otherwise utilized
  in some way are items.
  """
  
  def __init__(self, game, actor, data):
    """Get all our data from the data dictionary, templates and master item.
    (In forward order: 1) master item  2) templates  3) current data dict
    """
    self.game = game
    self.actor = actor
    self.original_item_data = copy.deepcopy(data)
    
    # This will be where all the data for the item goes after Initialize()
    self.data = None
    
    # Multiple stages of preparing our items, which inherit from a Master
    #   Item and potentially many templates...
    self.Initialize()
    
    if actor:
      Log('New Item for %s: %s' % (actor.name, self.data['name']))
    else:
      Log('Barter item:\n%s' % str(self))
  
  
  def __repr__(self):
    output = ''
    
    output += 'Name: %s\n' % self.data.get('name', '*Unknown*')
    
    keys = self.data.keys()
    keys.sort()
    for key in keys:
      if key not in ('name', ):
        output += '  %s: %s\n' % (key, self.data[key])
    
    return output
  
  
  
  def Initialize(self):
    # Initialize our data with Master Item
    self.data = self.InitializeMasterItem()
    
    # If we have a template in our instance data, load it
    if 'template' in self.original_item_data:
      template_data = self.LoadTemplate(self.original_item_data['template'])
      self.data.update(template_data)
    
    # Now update our data with the Instance data
    self.data.update(self.original_item_data)
  
  
  def InitializeMasterItem(self):
    """Every item hails from the Master Item.  Load this information first."""
    data = copy.deepcopy(self.game.data['game']['master_item'])
    
    return data
  
  
  def LoadTemplate(self, template):
    """Load a template"""
    #Log('LoadTemplate: template: %s' % template)
    #Log('LoadTemplate: items: %s' % self.game.data['items'])
    config_data = self.game.data['items'][template]
    data = copy.deepcopy(config_data)
    
    if 'template' in data:
      # Load the template data
      template_data = self.LoadTemplate(data['template'])
      
      # Update the template data with our current data
      template_data.update(data)
      
      # Re-save the actual data
      data = template_data
    
    return data


