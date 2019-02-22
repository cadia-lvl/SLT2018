#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creates the configuration file needed by g2p_experiment.py

Extend the file with the necessary paths for the Sequitur g2p

"""

import configparser

config = configparser.ConfigParser()

# value should be: 'export PYTHONPATH=/path/to/python/site-packages_for_sequitur:/path/to/g2p ;'
config['pythonpath'] = {'path_export': ''}
# value should be: 'path/to/g2p.py'
config['g2p_tool'] = {'g2p': ''}

with open('g2p.conf', 'w') as configfile:
    config.write(configfile)
