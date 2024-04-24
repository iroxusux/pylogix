#!/usr/bin/env python

""" cla_logix_object
    an object that represents all other logic objects from an allen bradley plc controller
    """

# pylogix imports #
from l5x import write_xml_to_l5x, generic_controller_wrapper, l5x_content_wrapper
from base.pylogix_dependencies import PyLogixDependencies
from base.pylogix_enum import DescriptionPropertyIdentifier

# python std lib imports #
from copy import deepcopy
import re
from typing import Self, Type
from xml.dom import minidom


class DescriptionProperties:
    """ pylogix object description properties\n
        these properties exist in the 'description' of each pylogix_object\n
        this is managed in Allen Bradley's Studio 5000 software as Descriptions as well.
    """
    identifier: str | None = None  # Logic object ID (e.g. 'CONTROLLER' or 'PROGRAM')
    type: str | None = None  # Logic object type (e.g. 'CPU' or 'ZONE')
    version: str | None = None  # Logic object version
    description: str | None = None  # Logic object description
    editable: bool | None = None  # Logic object user editable

    @classmethod
    def get_properties(cls,
                       description_properties: []) -> Self:
        """ get functional description properties from a list of strings.\n
            to properly obtain this list, call -> pylogix_object.property_list_from_string()"""
        props = cls()
        if not description_properties or (len(description_properties) == 0):
            return props
        ident = DescriptionPropertyIdentifier.from_string(description_properties[0])
        props.identifier = ident.value if ident else ''
        props.type = cls.parse_from_property(description_properties, '@TYPE')
        props.version = cls.parse_from_property(description_properties, '@VERSION')
        props.description = cls.parse_from_property(description_properties, '@DESC')
        props.editable = False if '@NOEDITS' in description_properties else True
        return props

    @staticmethod
    def parse_from_property(desc_props: [str],
                            property_to_find: str) -> str:
        """ return a specified property from a description list
        """
        return next(
            (str(prop).replace(property_to_find, '').strip() for prop in desc_props if property_to_find in prop), None)


class PyLogixObject(object):
    """
    base class for CLA logix objects

    call with a name and [optional] description
    this object shall not be used directly and instead, inherited by other classes
    to be used in the pylogix ecosystem
    """

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 *args,
                 **kwargs):
        self._name = name
        self.description = description
        self.description_properties = DescriptionProperties()
        self._generator_properties: [str] = []
        self._data = {}

    def __copy__(self) -> Self:
        """ shallow copy of an object
        """
        _copy = type(self)(self.name,
                           self.description)
        _copy.__dict__.update(self.__dict__)
        return _copy

    def __deepcopy__(self,
                     memo) -> Self:  # memo is a dict of id's to copies
        """ deep copy of an object
        """
        id_self = id(self)  # memoization avoids unnecessary recursion
        _copy = memo.get(id_self)
        if _copy is None:
            _copy = type(self)(
                deepcopy(self.name, memo),
                deepcopy(self.description, memo))
            memo[id_self] = _copy
            for key, value in self.__dict__.items():
                setattr(_copy, key, deepcopy(value, memo))
        return _copy

    def __eq__(self,
               other: Self) -> bool:
        """ test equality

        uses self.name to test
        """
        if not other:
            return False
        return True if self.name == other.name else False

    def __getitem__(self, item):
        return self._data[item]

    @staticmethod
    def __on_new_name__(value) -> bool:
        """ abstract method\n
            override in inherited classes\n
            return value if new name is ok
            """
        if value:
            pass
        return True

    def __resolve_dependencies_to_xml_node__(self,
                                             dependency_list: [],
                                             node_name: str,
                                             root: minidom.Document) -> minidom.Element | None:
        """ resolve a list of dependencies into an xml node
        """
        if len(dependency_list) <= 0:
            return None

        _node = root.createElement(node_name)
        _node.setAttribute('Use', 'Context')
        for depend in dependency_list:
            _node.appendChild(depend.to_l5x_xml_node(root,
                                                     True if depend is self else False,
                                                     True))
        return _node

    def __setitem__(self, key, value):
        self._data[key] = value

    def __str__(self):
        return self.name

    @property
    def generator_properties(self) -> [str]:
        return self._generator_properties

    @property
    def l5x_node_name(self):
        raise NotImplementedError('inheriting class must override this property with reflecting name for l5x files.')

    @property
    def l5x_parent_node_name(self):
        raise NotImplementedError('inheriting class must override this property with reflecting name for l5x files.')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,
             value: str):
        bad_vals = ['.', ',', '-', '/', '\\', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '=', '+', ' ']
        if any(x in value for x in bad_vals):
            raise ValueError("illegal name set!")
        if self.__on_new_name__(value):
            self._name = value

    @classmethod
    def from_l5x(cls,
                 l5x_path: str,
                 *args,
                 **kwargs) -> type[Self] | None:
        """ abstract implementation of from_l5x method\n
            to implement, compile cls from passed l5x_node\n
            in the derived class"""
        raise NotImplementedError(
            'inheriting class must override this property with reflecting function for l5x files.')

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        """ abstract implementation of from_l5x method\n
                    to implement, compile cls from passed l5x_node\n
                    in the derived class"""
        raise NotImplementedError(
            'inheriting class must override this property with reflecting function for l5x files.')

    def get_dependencies(self,
                         include_root: bool = False) -> PyLogixDependencies:
        """ abstract implementation of cla get_dependencies
            to implement, return all logix objects this object relies on
            in the derived class"""
        raise NotImplementedError('inheriting class must override this property')

    def get_schema_options(self) -> {}:
        """ get schema options of object for l5x compilation
            override this method to return a key-value pair (dictionary) of options to be appended to l5x files
            """
        return {}

    @classmethod
    def get_unique_name(cls,
                        named_object: Type[Self],
                        list_to_search: [Self]):
        """ generate unique named based on the name of the object provided.
            useful for creating new pylogix objects from others
            """
        results = re.search(r'\d+$', named_object.name)
        try:
            results_ctr = int(results.group()) if results else None
        except ValueError:
            results_ctr = None

        searching_name_base = named_object.name.replace(results.group(), '') if results_ctr else named_object.name
        counter = results_ctr if results_ctr else 1
        searching_name = f'{searching_name_base}{counter}' if counter >= 10 else f'{searching_name_base}0{counter}'
        while True:
            name_match = next((thing for thing in list_to_search if thing.name == searching_name), None)
            if name_match:
                counter += 1
                searching_name = f'{searching_name_base}{counter}' if counter >= 10 else f'{searching_name_base}0{counter}'
            else:
                break
        return searching_name

    @classmethod
    def property_list_from_string(cls,
                                  string: str,
                                  properties=None,
                                  begin_char: str = '<',
                                  end_char: str = '>') -> [str]:
        """ gather properties from a supplied string by matching begin_char to end_char.
            will search recursively, returning a list of all matches
            """
        if properties is None:
            properties = []
        if not string:
            return properties

        find_begin = string.find(begin_char)
        if find_begin == -1:
            return properties
        begin_anchor = find_begin + len(begin_char)

        find_end = string.find(end_char, begin_anchor)
        if find_end == -1:
            return properties
        end_anchor = begin_anchor + (find_end - len(end_char))

        if not properties:
            properties = []
        properties.append(string[begin_anchor:end_anchor].lstrip(begin_char).rstrip(end_char))

        return cls.property_list_from_string(string[(begin_anchor + find_end):].lstrip(),
                                             properties,
                                             begin_char,
                                             end_char)

    def push_updates(self,
                     other_obj: Self,
                     *args,
                     **kwargs) -> PyLogixDependencies:
        raise NotImplementedError('This method must be overridden by the over-riding class')

    def rebind(self,
               *args,
               **kwargs) -> None:
        """ rebind method for pylogix_object\n
        make sure to super() call this if it is overridden to get description properties automatically
        """
        self.description_properties = DescriptionProperties.get_properties(
            self.property_list_from_string(self.description))

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        if self.name:
            self.name = self.name.replace(_old_name, _new_name)
        if self.description:
            self.description = self.description.replace(_old_name, _new_name)

    def resolve_generator(self,
                          _generator_texts: [{}]):
        for _text in _generator_texts:
            self.rename_strings(_text['GeneratorText'],
                                _text['NewText'])

    def to_l5x(self,
               controller_name: str,
               save_location: str) -> None:
        export_options = self.get_schema_options()
        root, rslogix5000Content = l5x_content_wrapper(self.l5x_node_name,
                                                       self.name,
                                                       True,
                                                       'References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans',
                                                       **export_options)
        if self.description:
            root.insertBefore(root.createComment(self.description), rslogix5000Content)

        ctrl = generic_controller_wrapper(root,
                                          controller_name,
                                          'Context')
        rslogix5000Content.appendChild(ctrl)

        dependencies = PyLogixDependencies()
        dependencies.extend(self.get_dependencies(include_root=True))
        dependencies.sort()

        dt_node = self.__resolve_dependencies_to_xml_node__(dependencies.datatypes,
                                                            'DataTypes',
                                                            root)
        if dt_node:
            ctrl.appendChild(dt_node)

        mod_node = self.__resolve_dependencies_to_xml_node__(dependencies.modules,
                                                             'Modules',
                                                             root)
        if mod_node:
            ctrl.appendChild(mod_node)

        aoi_node = self.__resolve_dependencies_to_xml_node__(dependencies.add_on_instructions,
                                                             'AddOnInstructionDefinitions',
                                                             root)
        if aoi_node:
            ctrl.appendChild(aoi_node)

        tags_node = self.__resolve_dependencies_to_xml_node__(dependencies.tags,
                                                              'Tags',
                                                              root)
        if tags_node:
            ctrl.appendChild(tags_node)

        programs_node = self.__resolve_dependencies_to_xml_node__(dependencies.programs,
                                                                  'Programs',
                                                                  root)
        if programs_node:
            ctrl.appendChild(programs_node)

        tasks_node = self.__resolve_dependencies_to_xml_node__(dependencies.tasks,
                                                               'Tasks',
                                                               root)
        if tasks_node:
            ctrl.appendChild(tasks_node)

        write_xml_to_l5x(root,
                         save_location)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        """ abstract implementation of to_l5x_xml_node
            to implement, create and write an xml node and return it
            in the derived class"""
        raise NotImplementedError()
