# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-12-11 16:32

@author: johannes

"""
from abc import ABC


class Validator(ABC):
    """
    Base class for validators.
    """
    def __init__(self, *args, **kwargs):
        super(Validator, self).__init__()
        self.name = None
        self.id_key = None
        self.lat_key = None
        self.lon_key = None
        self.fill_in_new_values = None
        self.attributes = None

    def validate(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def message(*args):
        """
        :param args: tuple of strings
        :return: print to console
        """
        # FIXME We intend to introduce logging..
        print(' - '.join(args))
        # print('SHOULD print: %s' % ' - '.join(args))
        # logging.info(' - '.join(args))
