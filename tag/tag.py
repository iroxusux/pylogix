#!/usr/bin/env python

""" tag
    derived from cla_logix_object
    this class represents an Allen Bradley tag
    """

# pylogix imports #
from datatype import DataType, DataTypeMember
from l5x import get_text_data, get_first_element, bool_to_l5x, bool_from_l5x
from base import PyLogixDependencies, LogixClass, LogixTagType, TagUsage, PyLogixObject, PylogixList, LogixRadix

# python std lib imports #
from typing import Self
from xml.dom import minidom


class Tag(PyLogixObject):
    """ logix tag
        """

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 logix_class: LogixClass | None = None,
                 tag_type: LogixTagType | None = None,
                 datatype: DataType | None = None,
                 datatype_meta_name: str | None = None,
                 radix: LogixRadix | None = None,
                 constant: bool = False,
                 external_access: str = r'Read/Write',
                 dimensions: int | str | None = None,
                 alias_for: str | Self | None = None,
                 usage: TagUsage | None = None):
        super().__init__(name,
                         description)
        self.logix_class = logix_class
        self.tag_type = tag_type
        self.datatype = datatype
        self.datatype_meta_name = datatype_meta_name
        self.radix = radix
        self.constant = constant
        self.external_access = external_access
        self.dimensions: int | [] | None = self.__get_dimensions_from_str__(dimensions)
        self.alias_for = alias_for
        self.usage: TagUsage = usage
        self.data: {} = None
        self.__construct_data_set__()

    @staticmethod
    def __get_dimensions_from_str__(dim_string: str):
        """ try to parse dimensions from string
        """

        if not dim_string:  # if the string is null or empty, return with no dimensions
            return None

        try:  # assess if we are a single dimension
            return int(dim_string)
        except ValueError:
            pass

        # try to parse up to 3 dimensions
        multi_dim = dim_string.split(' ')
        try:
            if len(multi_dim) == 2:
                return [int(multi_dim[0]), int(multi_dim[1])]
            if len(multi_dim) == 3:
                return [int(multi_dim[0]), int(multi_dim[1]), int(multi_dim[2])]
        except ValueError:
            return None
        return None

    @staticmethod
    def __get_array_dimensions__(array_list) -> int:
        if len(array_list) == 0:
            return 1
        if isinstance(array_list[0], list):
            if isinstance(array_list[0][0], list):
                return 3
            else:
                return 2
        else:
            return 1

    def __str__(self):
        return self.__str_as_base__() if self.tag_type != LogixTagType.alias else self.__str_as_alias__()

    def __str_as_base__(self):
        text = self.name
        text += f' as *{self.datatype.name}*' if self.datatype else ''
        text += f'[{str(self.dimensions)}]' if self.dimensions else ''
        text += f' ({self.logix_class.value})' if self.logix_class else ''
        return text

    def __str_as_alias__(self):
        text = self.name
        text += f' alias of {self.alias_for}'
        text += f' ({self.logix_class.value})' if self.logix_class else ''
        return text

    def __construct_data_set__(self):
        """ construct inner data set of tag based on tag's datatype\n
            if no data type exists, data will be set to None"""
        if not self.datatype:
            self.data = None
            return
        self.data = self.__resolve_data_from_atomic_datatype__() if self.datatype.is_atomic else self.__resolve_data_from_complex_datatype__()

    def __resolve_data_from_atomic_datatype__(self) -> {}:
        """ resolve tag's data-set from tag's atomic datatype
            up to three dimensions are supported by both this code and RSLogix5000
        """
        if not self.dimensions:
            return {'Type': 'DataValue',
                    'DataType': self.datatype.name,
                    'Radix': 'Decimal',
                    'Value': 0,
                    'Members': None}

        if type(self.dimensions) is not list:
            return {'Type': 'Array',
                    'DataType': self.datatype.name,
                    'Radix': 'Decimal',
                    'Dimensions': [0] * self.dimensions}

        if len(self.dimensions) == 1:
            dim = [0] * self.dimensions
        elif len(self.dimensions) == 2:
            dim = [[0 for x in range(self.dimensions[1])] for y in range(self.dimensions[0])]
        elif len(self.dimensions) == 3:
            dim = [[0 for x in range(self.dimensions[1])] for y in range(self.dimensions[0])]
        else:
            raise ValueError('could not resolve dimensions for tag. Cannot resolve datatype structure.')

        return {'Type': 'Array',
                'DataType': self.datatype.name,
                'Radix': 'Decimal',
                'Dimensions': dim}

    def __resolve_data_from_complex_datatype__(self):
        """ resolve tag's data-set from tag's complex datatype
            up to three dimensions are supported by both this code and RSLogix5000
            """
        data = {'Type': 'Structure',
                'DataType': self.datatype.name,
                'Members': []}
        for member in self.datatype.members:
            member_data = self.__resolve_data_from_member__(member)
            if member_data:
                data['Members'].append(member_data)
        return data

    def __resolve_data_from_member__(self, member: DataTypeMember):
        if not member or not member.datatype or member.hidden:
            return None
        return self.__resolve_data_from_atomic_member__(
            member) if member.datatype.is_atomic else self.__resolve_data_from_complex_member__(member)

    @staticmethod
    def __resolve_data_from_atomic_member__(member: DataTypeMember):
        if member.dimensions:
            data = {'Type': 'ArrayMember',
                    'Name': member.name,
                    'DataType': member.datatype_meta_name,
                    'Radix': member.radix.value,
                    'Dimensions': [0] * member.dimensions}
        else:
            data = {'Type': 'DataValueMember',
                    'Name': member.name,
                    'DataType': member.datatype_meta_name,
                    'Radix': member.radix.value if member.radix else None,
                    'Value': 0}
        return data

    def __resolve_data_from_complex_member__(self, member: DataTypeMember):
        if not member.dimensions:
            data = {'Type': 'StructureMember',
                    'Name': member.name,
                    'DataType': member.datatype_meta_name,
                    'Members': []}
        else:
            data = {'Type': 'ArrayMember',
                    'Name': member.name,
                    'DataType': member.datatype_meta_name,
                    'Dimensions': [0] * member.dimensions,
                    'Members': []}

        for sec_member in member.datatype.members:
            member_data = self.__resolve_data_from_member__(sec_member)
            if member_data:
                data['Members'].append(member_data)
        return data

    def __read_structured_l5x_data__(self, data: {}, l5x_node: minidom.Element):
        if data['Type'] == 'DataValueMember':
            nodes = l5x_node.getElementsByTagName('DataValueMember')
            node = next((node for node in nodes if (node.getAttribute('Name') == data['Name']) and (
                    node.getAttribute('DataType') == data['DataType'])), None)
            if not node:
                return
            data['Value'] = node.getAttribute('Value')
            return

        if data['Type'] == 'ArrayMember':
            nodes = l5x_node.getElementsByTagName('ArrayMember')
            node = next((node for node in nodes if
                         node.getAttribute('Name') == data['Name'] and node.getAttribute('DataType') == data[
                             'DataType']), None)
            if not node:
                return
            parsed_nodes = [x for x in node.getElementsByTagName('Element') if
                            (isinstance(x, minidom.Element) and (x.parentNode == node))]
            for index, value_node in enumerate(parsed_nodes):
                data['Dimensions'][index] = value_node.getAttribute('Value')
            return

        if data['Type'] == 'StructureMember':
            nodes = l5x_node.getElementsByTagName('StructureMember')
            node = next((node for node in nodes if
                         node.getAttribute('Name') == data['Name'] and node.getAttribute('DataType') == data[
                             'DataType']), None)
            if not node:
                return
            for member in data['Members']:
                self.__read_structured_l5x_data__(member, node)

    def __read_decorated_xml_node__(self, l5x_node: minidom.Element):
        """ this first section deals with data value only - meaning, it's not part of a UDT and the data is a single value
        """
        if not self.data:
            return

        if self.data['Type'] == 'DataValue':
            data_value_node = get_first_element(l5x_node, 'DataValue')
            if not data_value_node:
                return
            try:
                self.data['Value'] = int(data_value_node.getAttribute('Value'))
            except ValueError:
                pass
            return

        if self.data['Type'] == 'Array':
            array_node = get_first_element(l5x_node, 'Array')
            if not array_node:
                return
            parsed_nodes = [x for x in array_node.getElementsByTagName('Element') if
                            (isinstance(x, minidom.Element) and (x.parentNode == array_node))]
            for index, value_node in enumerate(parsed_nodes):
                filtered_index = value_node.getAttribute('Index').replace('[', '').replace(']', '').split(',')
                match len(filtered_index):
                    case 1:
                        self.data['Dimensions'][index] = value_node.getAttribute('Value')
                    case 2:
                        self.data['Dimensions'][int(filtered_index[0])][
                            int(filtered_index[1])] = value_node.getAttribute('Value')
                    case 3:
                        self.data['Dimensions'][int(filtered_index[0])][int(filtered_index[1])][
                            int(filtered_index[2])] = value_node.getAttribute('Value')
            return

        """ if for some reason we aren't a structure by this point, return
            something weird is going on or i haven't finished... whatever
        """
        if self.data['Type'] != 'Structure':
            return

        structure_node = get_first_element(l5x_node, 'Structure')
        if not structure_node:
            return

        for member in self.data['Members']:
            self.__read_structured_l5x_data__(member, structure_node)

    def __write_structured_l5x_data__(self, data: {}, root: minidom.Document):
        if data['Type'] == 'DataValueMember':
            local_root = root.createElement(data['Type'])
            local_root.setAttribute('Name', data['Name'])
            local_root.setAttribute('DataType', data['DataType'])
            if data['Radix']:
                local_root.setAttribute('Radix', data['Radix'])
            local_root.setAttribute('Value', str(data['Value']) if data['Value'] else "0")
            return local_root

        if data['Type'] == 'ArrayMember':
            local_root = root.createElement(data['Type'])
            local_root.setAttribute('Name', data['Name'])
            local_root.setAttribute('DataType', data['DataType'])
            local_root.setAttribute('Dimensions', str(len(data['Dimensions'])))
            try:
                local_root.setAttribute('Radix', data['Radix'])
            except KeyError:
                pass

            if not isinstance(data['Dimensions'], list):
                for index, value in enumerate(data['Dimensions']):
                    dimension_root = root.createElement('Element')
                    dimension_root.setAttribute('Index', f'[{str(index)}]')
                    dimension_root.setAttribute('Value', str(value) if value else '0')
                    local_root.appendChild(dimension_root)
                return local_root

            match self.__get_array_dimensions__(data['Dimensions']):
                case 1:
                    for index1, value1 in enumerate(data['Dimensions']):
                        dimension_root = root.createElement('Element')
                        dimension_root.setAttribute('Index', f'[{str(index1)}]')
                        dimension_root.setAttribute('Value', str(value1) if value1 else '0')
                        local_root.appendChild(dimension_root)
                        return local_root
                case 2:
                    for index1 in data['Dimensions'][0]:
                        for index2, value2 in enumerate(data['Dimensions'][1]):
                            dimension_root = root.createElement('Element')
                            dimension_root.setAttribute('Index', f'[{str(index1)}, {str(index2)}]')
                            dimension_root.setAttribute('Value', str(value2) if value2 else '0')
                            local_root.appendChild(dimension_root)
                            return local_root
                case 3:
                    for index1 in data['Dimensions'][0]:
                        for index2 in data['Dimensions'][1]:
                            for index3, value3 in enumerate(data['Dimensions'][2]):
                                dimension_root = root.createElement('Element')
                                dimension_root.setAttribute('Index', f'[{str(index1)}, {str(index2)}, {str(index3)}]')
                                dimension_root.setAttribute('Value', str(value3) if value3 else '0')
                                local_root.appendChild(dimension_root)
                                return local_root
                case _:
                    raise Exception('We should not be here.')

        if data['Type'] == 'StructureMember':
            local_root = root.createElement(data['Type'])
            local_root.setAttribute('Name', data['Name'])
            local_root.setAttribute('DataType', data['DataType'])

            for member in data['Members']:
                local_root.appendChild(self.__write_structured_l5x_data__(member, root))

            return local_root

    def __write_l5x_tag_data__(self, root: minidom.Document):
        """ this first section deals with data value only - meaning, it's not part of a UDT and the data is a single value
                """
        if not self.data:
            return
        if self.data['Type'] == 'DataValue':
            local_root = root.createElement(self.data['Type'])
            local_root.setAttribute('DataType', self.data['DataType'])
            local_root.setAttribute('Radix', self.data['Radix'])
            local_root.setAttribute('Value', str(self.data['Value']) if self.data['Value'] else "0")
            return local_root

        if self.data['Type'] == 'Array':
            local_root = root.createElement(self.data['Type'])
            local_root.setAttribute('DataType', self.data['DataType'])
            local_root.setAttribute('Radix', self.data['Radix'])

            if not isinstance(self.data['Dimensions'], list):
                for index, value in enumerate(self.data['Dimensions']):
                    dimension_root = root.createElement('Element')
                    dimension_root.setAttribute('Index', f'[{str(index)}]')
                    dimension_root.setAttribute('Value', str(value) if value else '0')
                    local_root.setAttribute('Dimensions', str(self.data['Dimensions']))
                    local_root.appendChild(dimension_root)
                return local_root

            match self.__get_array_dimensions__(self.data['Dimensions']):
                case 1:
                    for index1, value1 in enumerate(self.data['Dimensions']):
                        dimension_root = root.createElement('Element')
                        dimension_root.setAttribute('Index', f'[{str(index1)}]')
                        dimension_root.setAttribute('Value', str(value1) if value1 else '0')
                        local_root.setAttribute('Dimensions', str(len(self.data['Dimensions'])))
                        local_root.appendChild(dimension_root)
                    return local_root
                case 2:
                    for index1, value1 in enumerate(self.data['Dimensions']):
                        for index2, value2 in enumerate(value1):
                            dimension_root = root.createElement('Element')
                            dimension_root.setAttribute('Index', f'[{str(index1)},{str(index2)}]')
                            dimension_root.setAttribute('Value', str(value2) if value2 else '0')
                            local_root.setAttribute('Dimensions',
                                                    f'{str(len(self.data['Dimensions']))},{str(len(self.data['Dimensions'][0]))}')
                            local_root.appendChild(dimension_root)
                    return local_root
                case 3:
                    for index1, value1 in enumerate(self.data['Dimensions']):
                        for index2, value2 in enumerate(value1):
                            for index3, value3 in enumerate(value2):
                                dimension_root = root.createElement('Element')
                                dimension_root.setAttribute('Index', f'[{str(index1)},{str(index2)},{str(index3)}]')
                                dimension_root.setAttribute('Value', str(value3) if value3 else '0')
                                local_root.setAttribute('Dimensions',
                                                        f'{str(len(self.data['Dimensions']))},{str(len(self.data['Dimensions'][0]))},{str(len(self.data['Dimensions'][1]))}')
                                local_root.appendChild(dimension_root)
                    return local_root
                case _:
                    raise Exception('We should not be here.')

        """ if for some reason we aren't a structure by this point, return
            something weird is going on or i haven't finished... whatever
        """
        if self.data['Type'] != 'Structure':
            return

        local_root = root.createElement(self.data['Type'])
        local_root.setAttribute('DataType', self.data['DataType'])
        for member in self.data['Members']:
            local_root.appendChild(self.__write_structured_l5x_data__(member, root))

        return local_root

    def get_dependencies(self,
                         include_root: bool = False) -> PyLogixDependencies:
        dependencies = PyLogixDependencies()
        if include_root:
            dependencies.safe_add_item(dependencies.tags,
                                       self)
        if self.datatype:
            dependencies.extend(self.datatype.get_dependencies(include_root=True))
        return dependencies

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        if not xml_node:
            return None
        try:
            datatype = kwargs['datatypes'].by_name(xml_node.getAttribute('DataType'))
        except KeyError:
            datatype = None

        tag = cls(xml_node.getAttribute('Name'),
                  get_text_data(xml_node, 'Description'),
                  LogixClass.from_string(xml_node.getAttribute('Class')),
                  LogixTagType.from_string(xml_node.getAttribute('TagType')),
                  datatype,
                  xml_node.getAttribute('DataType'),
                  LogixRadix.from_string(xml_node.getAttribute('Radix')),
                  bool_from_l5x(xml_node.getAttribute('Constant')),
                  xml_node.getAttribute('ExternalAccess'),
                  xml_node.getAttribute('Dimensions'),
                  xml_node.getAttribute('AliasFor'),
                  TagUsage.from_string(xml_node.getAttribute('Usage')))

        """ try to get decorated tag data from node
        """
        data_nodes = xml_node.getElementsByTagName('Data')
        decorated_node = next((x for x in data_nodes if x.getAttribute('Format') == 'Decorated'), None)
        if decorated_node:
            tag.__read_decorated_xml_node__(decorated_node)

        return tag

    def rebind(self,
               *args,
               **kwargs) -> None:
        """ rebind method for tag\n
        """
        super().rebind()
        try:
            if self.alias_for and self.alias_for != '':
                alias_tag = kwargs['tags'].by_name(self.alias_for)
                if alias_tag:
                    self.datatype = alias_tag.datatype
                    self.datatype_meta_name = alias_tag.datatype_meta_name
        except KeyError:
            return

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        super().rename_strings(_old_name, _new_name)
        if self.alias_for:
            self.alias_for = self.alias_for.replace(_old_name, _new_name)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        tag_root = root.createElement('Tag')
        tag_root.setAttribute('Name', self.name)

        if self.logix_class:
            tag_root.setAttribute('Class', self.logix_class.value)

        tag_root.setAttribute('TagType', self.tag_type.value.__str__())

        if self.alias_for:
            tag_root.setAttribute('AliasFor', self.alias_for)
        else:
            tag_root.setAttribute('DataType', self.datatype_meta_name)

            if self.dimensions:
                tag_root.setAttribute('Dimensions', str(self.dimensions).replace('[', '').replace(']', ''))

            if self.radix:
                tag_root.setAttribute('Radix', self.radix.value)

            tag_root.setAttribute('Constant', bool_to_l5x(self.constant))

        if self.usage:
            tag_root.setAttribute('Usage', self.usage.value)

        tag_root.setAttribute('ExternalAccess', self.external_access)

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            tag_root.appendChild(desc_root)

        if self.data:
            data_root = root.createElement('Data')
            data_root.setAttribute('Format', 'Decorated')
            data_child = self.__write_l5x_tag_data__(root)
            if data_child:
                data_root.appendChild(data_child)
            tag_root.appendChild(data_root)

        return tag_root


class TagList(PylogixList):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        return Tag
