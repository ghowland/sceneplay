#!/usr/bin/env python

"""
RPG: Utility functions
"""


import StringIO
import yaml


def YamlOpen(filename):
  data = str(open(filename).read())
  
  data = data.replace('\t', '  ')
  
  return StringIO.StringIO(data)
  

def LoadYaml(filename):
  #data = yaml.load(YamlOpen(filename))
  data = yaml.load(open(filename))
  return data

