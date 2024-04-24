#!/usr/bin/env python

""" pylogix_dependencies
    this file manages pylogix_dependencies for pylogix
    """

# pylogix imports #
# ---

# python std lib imports #
from typing import Self


class PyLogixDependencies:
    def __init__(self):
        self.add_on_instructions: [] = []
        self.datatypes: [] = []
        self.modules: [] = []
        self.programs: [] = []
        self.tags: [] = []
        self.program_tags: [] = []
        self.tasks: [] = []

    def extend(self, other: Self):
        if not other:
            return
        self.__safe_add__(self.add_on_instructions, other.add_on_instructions)
        self.__safe_add__(self.datatypes, other.datatypes)
        self.__safe_add__(self.modules, other.modules)
        self.__safe_add__(self.programs, other.programs)
        self.__safe_add__(self.tags, other.tags)
        self.__safe_add__(self.program_tags, other.program_tags)
        self.__safe_add__(self.tasks, other.tasks)

    @staticmethod
    def __safe_add__(list1: [], list2: []):
        for item in list2:
            if item not in list1:
                list1.append(item)

    @staticmethod
    def safe_add_item(my_list: [], item):
        if item not in my_list:
            my_list.append(item)

    def sort(self):
        self.add_on_instructions = sorted(self.add_on_instructions, key=lambda x: x.name.lower())
        self.datatypes = sorted(self.datatypes, key=lambda x: x.name.lower())
        self.modules = sorted(self.modules, key=lambda x: x.name.lower())
        self.programs = sorted(self.programs, key=lambda x: x.name.lower())
        self.tags = sorted(self.tags, key=lambda x: x.name.lower())
        self.tasks = sorted(self.tasks, key=lambda x: x.name.lower())
