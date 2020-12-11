# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2020-12-11 15:56

@author: johannes

"""
from eoana.config import Settings
# from eoana.handler import some_classes, some_funcs


class App:
    """
    Keep it clean, keep it tidy!
    - read
    - validate
    - write
    """
    def __init__(self, *args, **kwargs):
        self.settings = Settings(**kwargs)

    def validate(self, *args, **kwargs):
        """"""
        raise NotImplementedError

    def read(self, *args, **kwargs):
        """"""
        raise NotImplementedError

    def write(self, *args, **kwargs):
        """"""
        raise NotImplementedError


if __name__ == '__main__':
    app = App()
