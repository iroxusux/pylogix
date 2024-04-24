#!/usr/bin/env python

""" routine
    derived from cla_logix_object
    this class represents an Allen Bradley Routine
    """

# pylogix imports #
from l5x import get_text_data
from base import LogixRoutineType, PyLogixObject, PyLogixDependencies, PylogixList
from rung import Rung, RungList

# python std lib imports #
from xml.dom import minidom


class Routine(PyLogixObject):

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 routine_type: LogixRoutineType | None = None):
        super().__init__(name,
                         description)
        self.routine_type = routine_type
        self.rungs: [Rung] = []

    def get_dependencies(self,
                         include_root: bool = False) -> PyLogixDependencies:
        dependencies = PyLogixDependencies()
        for rung in self.rungs:
            dependencies.extend(rung.get_dependencies())

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
        routine = cls(xml_node.getAttribute('Name'),
                      get_text_data(xml_node, 'Description'),
                      LogixRoutineType.from_string(xml_node.getAttribute('Type')))

        # parse through routines if they exist
        try:
            rungs_list_xml = xml_node.getElementsByTagName('RLLContent')[0]
            if rungs_list_xml:
                rung_nodes = [x for x in rungs_list_xml.childNodes if isinstance(x, minidom.Element)]
                routine.rungs.extend([Rung.from_l5x_xml_node(rung_node,
                                                             **kwargs) for rung_node in rung_nodes])
        except IndexError:
            pass

        return routine

    def rebind(self,
               *args,
               **kwargs) -> None:
        """ rebind method for pylogix_object\n
        make sure to super() call this if it is overridden to get description properties automatically
        """
        super().rebind()
        for rung in self.rungs:
            rung.rebind(*args,
                        **kwargs)

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        super().rename_strings(_old_name, _new_name)
        for _rung in self.rungs:
            _rung.rename_strings(_old_name, _new_name)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        routine_root = root.createElement('Routine')
        routine_root.setAttribute('Name', self.name)
        routine_root.setAttribute('Type', self.routine_type.value.__str__())

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            routine_root.appendChild(desc_root)

        rll_content_root = root.createElement('RLLContent')
        for rung in self.rungs:
            rll_content_root.appendChild(rung.to_l5x(root))
        routine_root.appendChild(rll_content_root)

        return routine_root


class RoutineList(PylogixList[Routine]):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        return Routine
