#!/usr/bin/env python

""" pylogix_list
    this file manages list override for pylogix
    """
# pylogix imports #
from l5x import open_l5x_to_controller_node, get_first_element, l5x_content_wrapper, generic_controller_wrapper, \
    write_xml_to_l5x
from base.pylogix_dependencies import PyLogixDependencies
from base.pylogix_object import PyLogixObject

# python std lib imports #
from typing import Any, Self
from xml.dom import minidom


class PylogixList[T](list):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        raise NotImplementedError('object constructor type must be overridden by child class')

    @property
    def l5x_child_keyword(self):
        return self.object_constructor_type.__name__

    @property
    def l5x_keyword(self):
        return self.object_constructor_type.__name__ + 's'

    @staticmethod
    def __to_l5x_xml_node__(node_name: str,
                            object_list: [],
                            root: minidom.Document,
                            as_target: bool = False,
                            include_dependencies: bool = False) -> minidom.Element:
        objects_root = root.createElement(node_name)
        for item in object_list:
            append_obj = item.to_l5x_xml_node(root,
                                              as_target=as_target,
                                              include_dependencies=include_dependencies)
            if append_obj:
                objects_root.appendChild(append_obj)
        return objects_root

    def append(self,
               __object: PyLogixObject,
               __overwrite: bool = False) -> bool:
        """ override to safe append object to list
        """
        if type(__object) is self.object_constructor_type:
            if __object in self and __overwrite:
                super().remove(__object)
                super().append(__object)
                return True
            elif __object not in self:
                super().append(__object)
                return True
        return False

    def by_name(self,
                name: str) -> Any:
        return next((item for item in self if item.name == name), None)

    def extend(self,
               __iterable,
               __overwrite: bool = False):
        """ override to safe append iterable list to self
        """
        [self.append(__iter,
                     __overwrite) for __iter in __iterable]

    def from_l5x(self,
                 l5x_path: str,
                 *args,
                 **kwargs):
        try:
            ctrl_node = kwargs['ctrl_node']
        except KeyError:
            ctrl_node = open_l5x_to_controller_node(l5x_path)

        objects_node = get_first_element(ctrl_node,
                                         self.l5x_keyword)
        if not objects_node:
            return

        for node in [node for node in objects_node.childNodes if isinstance(node, minidom.Element)]:
            self.append(self.object_constructor_type.from_l5x_xml_node(node,
                                                                       *args,
                                                                       **kwargs))

        self.rebind(*args,
                    **kwargs)

    def push_updates(self,
                     other_list: Self):
        raise NotImplementedError('This method must be overridden by the over-riding class')

    def rebind(self,
               *args,
               **kwargs):
        """ rebind properties. this method is abstract. override as necessary."""
        for x in self:
            x.rebind(*args,
                     **kwargs)
        # self.sort(key=lambda obj: obj.name)

    def remove(self,
               __object) -> bool:
        """ override to safe remove object from list
        """
        if __object in self and type(__object) is self.object_constructor_type:
            super().remove(__object)
            return True
        return False

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        for x in self:
            x.rename_strings(_old_name, _new_name)

    def to_l5x(self,
               controller_name: str,
               save_location: str,
               include_dependencies: bool = False) -> None:
        """ abstract implementation of to_l5x
            to implement, create and write an L5X file describing the pylogix object
            in the derived class"""
        if len(self) == 0:
            return
        root, rslogix5000Content = l5x_content_wrapper(self.l5x_child_keyword,
                                                       self[0].name,
                                                       True,
                                                       'References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans')
        root.insertBefore(root.createComment(self[0].description), rslogix5000Content)
        ctrl = generic_controller_wrapper(root,
                                          controller_name,
                                          'Context')
        rslogix5000Content.appendChild(ctrl)

        dependencies = PyLogixDependencies()
        for obj in self:
            dependencies.extend(obj.get_dependencies(include_root=True))
        dependencies.sort()

        dt_root = self.__to_l5x_xml_node__('DataTypes',
                                           dependencies.datatypes,
                                           root,
                                           True if self.l5x_keyword == 'DataTypes' else False,
                                           include_dependencies)
        if dt_root:
            ctrl.appendChild(dt_root)

        aoi_root = self.__to_l5x_xml_node__('AddOnInstructionDefinitions',
                                            dependencies.add_on_instructions,
                                            root,
                                            True if self.l5x_keyword == 'AddOnInstructionDefinitions' else False,
                                            include_dependencies)
        if aoi_root:
            ctrl.appendChild(aoi_root)

        write_xml_to_l5x(root,
                         save_location)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        return self.__to_l5x_xml_node__(self.l5x_keyword,
                                        self,
                                        root,
                                        as_target,
                                        include_dependencies)
