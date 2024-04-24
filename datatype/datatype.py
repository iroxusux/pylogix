#!/usr/bin/env python

""" datatype
    derived from cla_logix_object
    this class represents an Allen Bradley DataType
    """

# pylogix imports #
from l5x import get_text_data, bool_to_l5x, get_first_element, l5x_content_wrapper, \
    generic_controller_wrapper, write_xml_to_l5x
from base import PyLogixDependencies, LogixRadix, LogixFamily, LogixDataTypeClass, PylogixList, PyLogixObject

# python std lib imports #
from copy import deepcopy
from typing import Self
from xml.dom import minidom


class DataTypeMember(PyLogixObject):
    """ Data type member

        This class acts as a container for datatype information for elements (or members) of a datatype.
        """

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 datatype_meta_name: str | None = None,
                 dimensions: int = 0,
                 radix: LogixRadix | None = None,
                 hidden: bool = False,
                 target: str | None = None,
                 bit_number: int | str | None = None):
        super().__init__(name,
                         description)
        self.datatype: DataType | None = None
        self.datatype_meta_name = datatype_meta_name

        """ due to the way l5x files are parsed
            BITs and BOOLs are not interchangeable. So after reading the L5X in, change BITs to BOOLs. If we need to change this again, it'll happen at L5X compilation time
            """
        if self.datatype_meta_name == 'BIT':
            self.datatype_meta_name = 'BOOL'

        self.dimensions = dimensions
        self.radix = radix
        self.hidden = hidden
        self.external_access = 'Read/Write'
        self.target = target
        self.bit_number = bit_number

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        """ resolve datatype member from l5x xml node
        """
        if not xml_node:
            return None
        return cls(xml_node.getAttribute('Name'),
                   get_text_data(xml_node, 'Description'),
                   xml_node.getAttribute('DataType'),
                   int(xml_node.getAttribute('Dimension')),
                   LogixRadix.from_string(xml_node.getAttribute('Radix')),
                   True if (xml_node.getAttribute('Hidden') == 'true') else False,
                   xml_node.getAttribute('Target'),
                   xml_node.getAttribute('BitNumber'))

    def rebind(self,
               *args,
               **kwargs) -> None:
        """ rebind datatype
        """
        if not self.datatype:
            self.datatype = kwargs['datatypes'].by_name(self.datatype_meta_name)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        member_root = root.createElement('Member')
        member_root.setAttribute('Name', self.name)
        member_root.setAttribute('DataType', self.datatype_meta_name if self.datatype_meta_name != 'BOOL' else (
            'BIT' if self.dimensions == 0 else 'BOOL'))
        member_root.setAttribute('Dimension', self.dimensions.__str__())
        if self.radix:
            member_root.setAttribute('Radix', self.radix.value)
        member_root.setAttribute('Hidden', bool_to_l5x(self.hidden))
        if self.target:
            member_root.setAttribute('Target', self.target)
        if self.bit_number:
            member_root.setAttribute('BitNumber', self.bit_number.__str__())
        member_root.setAttribute('ExternalAccess', self.external_access)
        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            desc_root.appendChild(root.createTextNode(''))
            member_root.appendChild(desc_root)
        return member_root


class DataTypeMemberList(PylogixList[DataTypeMember]):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        return DataTypeMember

    @property
    def l5x_keyword(self):
        return 'Members'


class DataType(PyLogixObject):

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 family: LogixFamily | None = None,
                 datatype_class: LogixDataTypeClass | None = None,
                 is_atomic: bool = False,
                 is_base_logix_instruction: bool = False):
        super().__init__(name,
                         description)
        self.family: LogixFamily = family if family else LogixFamily.no_family
        self.datatype_class: LogixDataTypeClass = datatype_class if datatype_class else LogixDataTypeClass.User
        self.is_atomic = is_atomic
        self.is_base_logix_instruction = is_base_logix_instruction
        self.members: DataTypeMemberList = DataTypeMemberList()

    def get_dependencies(self,
                         include_root: bool = False) -> PyLogixDependencies:
        """ get a list of all datatypes this datatype depends on
        """
        dependencies = PyLogixDependencies()
        if self.is_atomic or self.is_base_logix_instruction:
            return dependencies
        if include_root:
            dependencies.safe_add_item(dependencies.datatypes,
                                       self)
        for member in [mem for mem in self.members if
                       mem.datatype and (not mem.datatype.is_atomic) and (not mem.datatype.is_base_logix_instruction)]:
            if member.datatype not in dependencies.datatypes:
                dependencies.datatypes.append(member.datatype)
            dependencies.extend(member.datatype.get_dependencies())
        return dependencies

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        """ resolve datatype object from l5x xml node
        """
        if not xml_node:
            return None
        datatype = cls(xml_node.getAttribute('Name'),
                       get_text_data(xml_node, 'Description'),
                       LogixFamily.from_string(xml_node.getAttribute('Family')),
                       LogixDataTypeClass.from_string(xml_node.getAttribute('Class')))

        # parse through members if they exist
        members_list_xml = get_first_element(xml_node,
                                             'Members')

        if members_list_xml:
            datatype.members.extend([DataTypeMember.from_l5x_xml_node(member_node) for member_node in
                                     [x for x in members_list_xml.childNodes if isinstance(x, minidom.Element)]])

        return datatype

    def rebind(self,
               *args,
               **kwargs) -> None:
        """ rebind datatype
        """
        super().rebind()
        self.members.rebind(*args,
                            **kwargs)

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        super().rename_strings(_old_name,
                               _new_name)
        self.members.rename_strings(_old_name,
                                    _new_name)

    def to_l5x(self,
               controller_name: str,
               save_location: str) -> None:
        root, rslogix5000Content = l5x_content_wrapper('DataType',
                                                       self.name,
                                                       True,
                                                       'References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans')
        root.insertBefore(root.createComment(self.description), rslogix5000Content)
        ctrl = generic_controller_wrapper(root,
                                          controller_name,
                                          'Context')
        rslogix5000Content.appendChild(ctrl)

        dts = root.createElement('DataTypes')
        dts.setAttribute('Use', 'Context')

        dependencies = PyLogixDependencies()
        dependencies.extend(self.get_dependencies(include_root=True))
        dependencies.sort()
        for dt in dependencies.datatypes:
            dts.appendChild(dt.to_l5x_xml_node(root,
                                               as_target=True if dt is self else False,
                                               include_dependencies=True))
        ctrl.appendChild(dts)
        write_xml_to_l5x(root,
                         save_location)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element | None:
        if self.is_atomic or self.is_base_logix_instruction:
            return None
        dt_root = root.createElement('DataType')

        if as_target:
            dt_root.setAttribute('Use', 'Target')

        dt_root.setAttribute('Name', self.name)
        dt_root.setAttribute('Family', self.family.value)

        if self.datatype_class is not LogixDataTypeClass.standard:
            dt_root.setAttribute('Class', self.datatype_class.value)

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            desc_root.appendChild(root.createTextNode(''))
            dt_root.appendChild(desc_root)

        if len(self.members) > 0:
            members_root = root.createElement("Members")
            dependant_members = []
            for member in self.members:
                members_root.appendChild(member.to_l5x_xml_node(root))
                if include_dependencies and member.datatype is not None:
                    if member.datatype.is_base_logix_instruction or member.datatype.is_atomic:
                        continue
                    dependant_members.append(member)
            dt_root.appendChild(members_root)

            if include_dependencies and len(dependant_members) > 0:
                dependencies_root = root.createElement('Dependencies')
                for member in dependant_members:
                    dependency_node = root.createElement('Dependency')
                    dependency_node.setAttribute('Type', 'DataType')
                    dependency_node.setAttribute('Name', member.datatype.name)
                    dependencies_root.appendChild(dependency_node)
                dt_root.appendChild(dependencies_root)

        return dt_root


class DataTypeList(PylogixList):
    def __init__(self,
                 create_empty: bool = False):
        super().__init__()
        if not create_empty:
            for dt in ATOMIC_DATA_TYPES:
                self.append(dt)

    @property
    def object_constructor_type(self):
        return DataType

    def push_updates(self,
                     other_list: Self):
        for obj in self:
            if obj in other_list:
                other_list.remove(obj)
                other_list.append(deepcopy(obj))
                for d in obj.get_dependencies().datatypes:
                    if d in other_list:
                        other_list.remove(d)
                        other_list.append(d)
                    elif d not in other_list:
                        other_list.append(d)

    def rebind(self,
               parent: PyLogixObject | None = None,
               *args,
               **kwargs):
        """ rebind properties. this method is abstract. override as necessary."""
        try:
            if not kwargs['datatypes']:
                kwargs['datatypes'] = self
        except KeyError:
            kwargs['datatypes'] = self
        super().rebind(*args,
                       **kwargs)


""" Create Logix version of the timer datatype
"""
LOGIX_TIMER = DataType('TIMER',
                       '',
                       LogixFamily.none,
                       LogixDataTypeClass.standard,
                       False,
                       True)
LOGIX_TIMER.members.append(DataTypeMember('PRE',
                                          '',
                                          'DINT',
                                          0,
                                          LogixRadix.Decimal,
                                          False,
                                          '',
                                          None))
LOGIX_TIMER.members.append(DataTypeMember('ACC',
                                          '',
                                          'DINT',
                                          0,
                                          LogixRadix.Decimal,
                                          False,
                                          '',
                                          None))
LOGIX_TIMER.members.append(DataTypeMember('EN',
                                          '',
                                          'BOOL',
                                          0,
                                          None,
                                          False,
                                          '',
                                          None))
LOGIX_TIMER.members.append(DataTypeMember('TT',
                                          '',
                                          'BOOL',
                                          0,
                                          None,
                                          False,
                                          '',
                                          None))
LOGIX_TIMER.members.append(DataTypeMember('DN',
                                          '',
                                          'BOOL',
                                          0,
                                          None,
                                          False,
                                          '',
                                          None))

""" Create Logix version of the timer datatype
"""
LOGIX_CONTROL = DataType('CONTROL',
                         '',
                         LogixFamily.none,
                         LogixDataTypeClass.standard,
                         False,
                         True)
LOGIX_CONTROL.members.append(DataTypeMember('LEN',
                                            '',
                                            'DINT',
                                            0,
                                            LogixRadix.Decimal,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('POS',
                                            '',
                                            'DINT',
                                            0,
                                            LogixRadix.Decimal,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('EN',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('EU',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('DN',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('EM',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('ER',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('UL',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('IN',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))
LOGIX_CONTROL.members.append(DataTypeMember('FD',
                                            '',
                                            'BOOL',
                                            0,
                                            None,
                                            False,
                                            '',
                                            None))

ATOMIC_DATA_TYPES = [
    DataType('BOOL', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('BIT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('SINT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('USINT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('INT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('UINT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('DINT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('UDINT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('LINT', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    DataType('REAL', '', LogixFamily.none, LogixDataTypeClass.standard, True),
    LOGIX_TIMER,
    LOGIX_CONTROL
]
