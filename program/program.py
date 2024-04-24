#!/usr/bin/env python

""" program
    derived from cla_logix_object
    this class represents an Allen Bradley Program
    """

# pylogix imports #
from l5x import get_text_data, bool_to_l5x, bool_from_l5x
from base import PyLogixObject, PyLogixDependencies, LogixClass, PylogixList
from routine import Routine, RoutineList
from tag import Tag, TagList

# python std lib imports #
from copy import deepcopy
from difflib import SequenceMatcher
from typing import Self
from xml.dom import minidom


class Program(PyLogixObject):

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 test_edits: bool = False,
                 main_routine_name: str = None,
                 disabled: bool = False,
                 program_class: LogixClass | None = None,
                 use_as_folder: bool = False):
        super().__init__(name,
                         description)
        self.test_edits = test_edits
        self.main_routine_name = main_routine_name
        self.disabled = disabled
        self.program_class = program_class
        self.use_as_folder = use_as_folder
        self.tags: TagList = TagList()
        self.routines: RoutineList = RoutineList()

    @property
    def driver_routines(self):
        return [routine for routine in self.routines if routine.description_properties.type == 'DRIVER']

    @property
    def internal_routines(self):
        return [routine for routine in self.routines if routine.description_properties.type == 'INTERNAL']

    @property
    def main_routine(self):
        return next((routine for routine in self.routines if routine.description_properties.type == 'MAIN'), None)

    @classmethod
    def __push_driver_routine__(cls,
                                routine: Routine,
                                other_prog: Self) -> PyLogixDependencies:
        dependencies = PyLogixDependencies()
        routine_updates: [{}] = []
        split = routine.name.split('_')
        if len(split) < 3:
            raise ValueError(f'Master Driver Routine Naming Violation: {routine.name}')

        """ gather list of routines that need updating from this driver
        """
        for other_routine in other_prog.routines:
            other_split = other_routine.name.split('_')
            if len(other_split) < 3:
                continue
            if split[2:] == other_split[2:]:
                routine_entry = {
                    'routine': other_routine,
                    'name_split': split,
                    'other_name_split': other_split,
                }
                routine_updates.append(routine_entry)

        """ perform updates to list of dictionary entries
        """
        for entry in routine_updates:
            other_prog.routines.remove(entry['routine'])
            new_routine: Routine = deepcopy(routine)
            new_routine.name = new_routine.name.replace(entry['name_split'][0], entry['other_name_split'][0])
            new_routine.name = new_routine.name.replace(entry['name_split'][1], entry['other_name_split'][1])
            for rung in new_routine.rungs:
                rung.text = rung.text.replace(entry['name_split'][1], entry['other_name_split'][1])
                for tag in rung.tags:
                    tag.name = tag.name.replace(entry['name_split'][1], entry['other_name_split'][1])
            other_prog.routines.append(new_routine)
            dependencies.extend(new_routine.get_dependencies())
        return dependencies

    @classmethod
    def __push_routine__(cls,
                         routine: Routine,
                         other_program: Self,
                         use_similarity_finding: bool = False,
                         similarity_gain: float = 0.95) -> PyLogixDependencies:
        if not routine:
            return PyLogixDependencies()
        dependencies = routine.get_dependencies()

        if use_similarity_finding:
            target_routine = next((r for r in other_program.routines if
                                   SequenceMatcher(None, routine.name, r.name).ratio() >= similarity_gain), None)
        else:
            target_routine = other_program.routines.by_name(routine.name)

        if target_routine in other_program.routines:
            other_program.routines.remove(target_routine)
        other_program.routines.append(routine)
        other_program.tags.extend(dependencies.program_tags)
        return dependencies

    def get_dependencies(self,
                         include_root: bool = False) -> PyLogixDependencies:
        dependencies = PyLogixDependencies()
        if include_root:
            dependencies.safe_add_item(dependencies.programs,
                                       self)
        for routine in self.routines:
            dependencies.extend(routine.get_dependencies())
        for tag in self.tags:
            dependencies.extend(tag.get_dependencies(include_root=False))
        return dependencies

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        """ generate a tag CLA object from l5x
        """
        if not xml_node:
            return None
        program = cls(xml_node.getAttribute('Name'),
                      get_text_data(xml_node, 'Description'),
                      False,
                      xml_node.getAttribute('MainRoutineName'),
                      bool_from_l5x(xml_node.getAttribute('Disabled')),
                      LogixClass.from_string(xml_node.getAttribute('Class')),
                      bool_from_l5x(xml_node.getAttribute('UseAsFolder')))

        # parse through tags if they exist
        tags_list_xml = xml_node.getElementsByTagName('Tags')[0]
        if tags_list_xml:
            tag_nodes = [x for x in tags_list_xml.childNodes if isinstance(x, minidom.Element)]
            program.tags.extend([Tag.from_l5x_xml_node(tag_node,
                                                       **kwargs) for tag_node in tag_nodes])
        kwargs['program_tags'] = program.tags  # assign program tags so routines and rungs can properly get tag datas

        # parse through routines if they exist
        routines_list_xml = xml_node.getElementsByTagName('Routines')[0]
        if routines_list_xml:
            routine_nodes = [x for x in routines_list_xml.childNodes if isinstance(x, minidom.Element)]
            program.routines.extend([Routine.from_l5x_xml_node(routine_node,
                                                               **kwargs) for routine_node in
                                     routine_nodes])
        return program

    def push_updates(self,
                     other_prog: Self,
                     use_similarity_finding: bool = False,
                     similarity_gain: float = 0.95) -> PyLogixDependencies:
        dependencies = self.get_dependencies()

        dependencies.extend(self.__push_routine__(self.main_routine,
                                                  other_prog))
        for driver in self.driver_routines:
            dependencies.extend(self.__push_driver_routine__(driver,
                                                             other_prog))

        if not self.description_properties.type == 'DEVICE':
            for internal in self.internal_routines:
                dependencies.extend(self.__push_routine__(internal,
                                                          other_prog,
                                                          use_similarity_finding,
                                                          similarity_gain))
        return dependencies

    def rebind(self,
               *args,
               **kwargs) -> None:
        """ rebind datatype
        """
        super().rebind()
        for routine in self.routines:
            routine.rebind(*args,
                           **kwargs)
        for tag in self.tags:
            tag.rebind(*args,
                       **kwargs)

        for driver in self.driver_routines:
            self._generator_properties = next((rung.property_list_from_string(rung.comment) for rung in driver.rungs if
                                               '@GENERATOR' in rung.property_list_from_string(rung.comment)), [])
        for x in range(len(self._generator_properties)):
            self._generator_properties[x] = self._generator_properties[x].strip()

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        super().rename_strings(_old_name, _new_name)
        self.tags.rename_strings(_old_name, _new_name)
        self.routines.rename_strings(_old_name, _new_name)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        program_root = root.createElement('Program')
        program_root.setAttribute('Name', self.name)
        program_root.setAttribute('TestEdits', bool_to_l5x(self.test_edits))
        program_root.setAttribute('MainRoutineName', self.main_routine_name)
        program_root.setAttribute('Disabled', bool_to_l5x(self.disabled))
        program_root.setAttribute('Class', self.program_class.value.__str__())
        program_root.setAttribute('UseAsFolder', bool_to_l5x(self.use_as_folder))

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            program_root.appendChild(desc_root)

        tags_root = root.createElement('Tags')
        for tag in self.tags:
            tags_root.appendChild(tag.to_l5x_xml_node(root))

        routines_root = root.createElement('Routines')
        for routine in self.routines:
            routines_root.appendChild(routine.to_l5x_xml_node(root))

        program_root.appendChild(tags_root)
        program_root.appendChild(routines_root)

        return program_root


class ProgramList(PylogixList):
    def __init__(self):
        super().__init__()

    @property
    def l5x_child_keyword(self):
        return 'Program'

    @property
    def l5x_keyword(self):
        return 'Programs'

    @property
    def object_constructor_type(self):
        return Program

    def push_updates(self,
                     other_list: Self) -> PyLogixDependencies:
        dependencies = PyLogixDependencies()
        for prog in self:
            if not prog.description_properties.type:
                continue
            for other_prog in other_list:
                if not other_prog.description_properties.type:
                    continue

                if prog.description_properties.type == other_prog.description_properties.type or (
                        prog.description_properties.type == 'DEVICE'):
                    if prog.description_properties.type == other_prog.description_properties.type:
                        other_prog.description = prog.description
                    dependencies.extend(prog.push_updates(other_prog,
                                                          use_similarity_finding=True,
                                                          similarity_gain=0.95))
        return dependencies

    def rebind(self,
               *args,
               **kwargs):
        """ rebind properties. this method is abstract. override as necessary."""
        try:
            if kwargs['programs'] is None:
                kwargs['programs'] = self
        except KeyError:
            kwargs['programs'] = self
        for x in self:
            x.rebind(*args,
                     **kwargs)
