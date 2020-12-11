# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-12-11 16:26

@author: johannes

"""
from abc import ABC


class WriterBase(ABC):
    """
    """
    def __init__(self, *args, **kwargs):
        super(WriterBase, self).__init__()
        self.attribute_constants = None
        self.attribute_mapping = None
        self.default_file_name = None
        self.header = None
        self.meta_header = None
        self.map_settings = None
        self.marker_tag_attributes = None
        self.station_radius = False

    def write(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def _write(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError
