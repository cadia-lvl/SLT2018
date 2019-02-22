#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creates the configuration file needed by g2p_experiment.py



"""

import configparser

config = configparser.ConfigParser()
config['pythonpath'] = {'path_export': 'export PYTHONPATH=/Users/anna/Ossian/tools/bin/../lib/python2.7/site-packages:/Users/anna/Ossian/tools/bin/../g2p ;'}
config['g2p_tool'] = {'g2p': '/Users/anna/Ossian/tools/bin/g2p.py'}

with open('g2p.conf', 'w') as configfile:
    config.write(configfile)
