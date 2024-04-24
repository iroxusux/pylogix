#!/usr/bin/env python

""" add_on_instruction
    derived from pylogix_object
    this class represents an Allen Bradley AddOnInstructionDefinition
    """

# pylogix imports #
from base import ExtendedEnum, LogixRadix, LogixTagType, LogixClass, PyLogixObject, PylogixList, PyLogixDependencies
from datatype import DataType
from l5x import get_text_data, bool_from_l5x, bool_to_l5x, get_first_element
from routine import Routine
from tag import Tag

# python std lib imports #
from typing import Self
from xml.dom import minidom


class AddOnInstructionTag(Tag):
    def __init__(self,
                 name: str,
                 description: str | None = None,
                 datatype: DataType | None = None,
                 datatype_meta_name: str | None = None,
                 radix: LogixRadix | None = None,
                 external_access: str | None = None):
        super().__init__(name,
                         description,
                         LogixClass.no_class,
                         LogixTagType.add_on_instruction,
                         datatype,
                         datatype_meta_name,
                         radix,
                         external_access=external_access)

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        """ generate a tag CLA object from l5x
        """
        if not xml_node:
            return None

        try:
            datatype = kwargs['datatypes'].by_name(xml_node.getAttribute('DataType'))
        except KeyError:
            datatype = None
        return cls(xml_node.getAttribute('Name'),
                   get_text_data(xml_node, 'Description'),
                   datatype,
                   xml_node.getAttribute('DataType'),
                   LogixRadix.from_string(xml_node.getAttribute('Radix')),
                   xml_node.getAttribute('ExternalAccess'))

    def get_dependencies(self,
                         include_root: bool = False) -> [PyLogixObject]:
        """ get a list of all datatypes this add-on instruction depends on
        """
        if not self.datatype:
            raise ValueError(f'no datatype associated with add-on instruction tag: {self.name}')
        return self.datatype.get_dependencies(include_root)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        local_tag_root = root.createElement('LocalTag')
        local_tag_root.setAttribute('Name', self.name)
        local_tag_root.setAttribute('DataType', self.datatype_meta_name)
        local_tag_root.setAttribute('Radix', str(self.radix.value))
        local_tag_root.setAttribute('ExternalAccess', self.external_access)

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            desc_root.appendChild(root.createTextNode(''))
            local_tag_root.appendChild(desc_root)

        return local_tag_root


class AddOnInstructionParameter(PyLogixObject):
    """ logix add on instruction parameter
    """

    class AddOnInstructionParameterUsage(ExtendedEnum):
        input = 'Input'
        output = 'Output'
        inout = 'InOut'

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 tag_type: LogixTagType | None = None,
                 datatype: DataType | None = None,
                 datatype_meta_name: str | None = None,
                 usage: AddOnInstructionParameterUsage | None = None,
                 radix: LogixRadix | None = None,
                 required: bool = False,
                 visible: bool = False,
                 external_access: str | None = None,
                 constant: bool | None = None,
                 dimensions: int | str | None = None):
        super().__init__(name,
                         description)
        self.tag_type = tag_type
        self.datatype = datatype
        self.datatype_meta_name = datatype_meta_name
        self.usage = usage
        self.radix = radix
        self.required = required
        self.visible = visible
        self.constant = constant
        try:
            self.dimensions = int(dimensions)
        except ValueError:
            self.dimensions = None
        except TypeError:
            self.dimensions = None
        self.external_access = external_access

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          class_constructor: type[Self] | None = None,
                          *args,
                          **kwargs):
        if not xml_node:
            return None

        try:
            datatype = next((datatype for datatype in kwargs['controller'].datatypes if
                             datatype.name == xml_node.getAttribute('DataType')), None)
        except KeyError:
            datatype = None

        constructor = class_constructor if class_constructor else cls
        return constructor(xml_node.getAttribute('Name'),
                           get_text_data(xml_node, 'Description'),
                           LogixTagType.from_string(xml_node.getAttribute('TagType')),
                           datatype,
                           xml_node.getAttribute('DataType'),
                           AddOnInstructionParameter.AddOnInstructionParameterUsage.from_string(
                               xml_node.getAttribute('Usage')),
                           LogixRadix.from_string(xml_node.getAttribute('Radix')),
                           True if xml_node.getAttribute('Required') == 'true' else False,
                           True if xml_node.getAttribute('Visible') == 'true' else False,
                           xml_node.getAttribute('ExternalAccess'),
                           bool_from_l5x(xml_node.getAttribute('Constant')),
                           xml_node.getAttribute('Dimensions'))

    def get_dependencies(self,
                         include_root: bool = False) -> [PyLogixObject]:
        if not self.datatype:
            raise ValueError(f'no datatype associated with add-on instruction parameter: {self.name}')
        return self.datatype.get_dependencies(include_root=include_root)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        param_root = root.createElement('Parameter')
        param_root.setAttribute('Name', self.name)
        param_root.setAttribute('TagType', self.tag_type.value.__str__())
        param_root.setAttribute('DataType', self.datatype_meta_name)

        if self.dimensions:
            param_root.setAttribute('Dimensions', str(self.dimensions))

        param_root.setAttribute('Usage', self.usage.value.__str__())
        if self.radix:
            param_root.setAttribute('Radix', self.radix.value)
        param_root.setAttribute('Required', bool_to_l5x(self.required))
        param_root.setAttribute('Visible', bool_to_l5x(self.visible))

        if self.external_access:
            param_root.setAttribute('ExternalAccess', self.external_access)

        if self.constant:
            param_root.setAttribute('Constant', bool_to_l5x(self.constant))

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            desc_root.appendChild(root.createTextNode(''))
            param_root.appendChild(desc_root)

        return param_root


class AddOnInstructionDefinition(PyLogixObject):
    """ logix add on instruction
        """

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 logix_class: LogixClass | None = None,
                 revision: str | None = None,
                 vendor: str | None = None,
                 execute_prescan: bool = False,
                 execute_postscan: bool = False,
                 execute_enable_in_false: bool = False,
                 created_date: str | None = None,
                 created_by: str | None = None,
                 edited_date: str | None = None,
                 edited_by: str | None = None,
                 software_revision: str | None = None,
                 revision_note: str | None = None):
        super().__init__(name,
                         description)
        self.logix_class = logix_class
        self.revision = revision
        self.vendor = vendor
        self.execute_prescan = execute_prescan
        self.execute_postscan = execute_postscan
        self.execute_enable_in_false = execute_enable_in_false
        self.created_date = created_date
        self.created_by = created_by
        self.edited_date = edited_date
        self.edited_by = edited_by
        self.software_revision = software_revision
        self.revision_note = revision_note
        self.parameters: [AddOnInstructionParameter] = []
        self.tags: [AddOnInstructionTag] = []
        self.routines: [Routine] = []

    @property
    def l5x_node_name(self):
        return 'AddOnInstructionDefinition'

    @property
    def l5x_parent_node_name(self):
        return self.l5x_node_name + 's'

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        if not xml_node:
            return None
        aoi = cls(xml_node.getAttribute('Name'),
                  get_text_data(xml_node, 'Description'),
                  LogixClass.from_string(xml_node.getAttribute('Class')),
                  xml_node.getAttribute('Revision'),
                  xml_node.getAttribute('Vendor'),
                  bool_from_l5x(xml_node.getAttribute('ExecutePrescan')),
                  bool_from_l5x(xml_node.getAttribute('ExecutePostscan')),
                  bool_from_l5x(xml_node.getAttribute('ExecuteEnableInFalse')),
                  xml_node.getAttribute('CreatedDate'),
                  xml_node.getAttribute('CreatedBy'),
                  xml_node.getAttribute('EditedDate'),
                  xml_node.getAttribute('EditedBy'),
                  xml_node.getAttribute('SoftwareRevision'),
                  get_text_data(xml_node, 'RevisionNote'))

        parameters_list_xml = get_first_element(xml_node, 'Parameters')
        if parameters_list_xml:
            aoi.parameters.extend([AddOnInstructionParameter.from_l5x_xml_node(member_node,
                                                                               **kwargs) for member_node in
                                   [x for x in parameters_list_xml.childNodes if isinstance(x, minidom.Element)]])

        tags_list_xml = get_first_element(xml_node, 'LocalTags')
        if tags_list_xml:
            aoi.tags.extend([AddOnInstructionTag.from_l5x_xml_node(tag_node,
                                                                   **kwargs) for tag_node in
                             [x for x in tags_list_xml.childNodes if isinstance(x, minidom.Element)]])

        routines_list_xml = get_first_element(xml_node, 'Routines')
        if routines_list_xml:
            aoi.routines.extend([Routine.from_l5x_xml_node(routine_node,
                                                           **kwargs) for routine_node in
                                 [x for x in routines_list_xml.childNodes if isinstance(x, minidom.Element)]])

        return aoi

    def get_dependencies(self,
                         include_root: bool = False) -> [PyLogixObject]:
        """ get a list of all objects this add-on instruction depends on
        """
        dependencies = PyLogixDependencies()
        if include_root:
            dependencies.safe_add_item(dependencies.add_on_instructions,
                                       self)
        for tag in self.tags:
            dependencies.extend(tag.get_dependencies(include_root=include_root))

        for param in self.parameters:
            dependencies.extend(param.get_dependencies(include_root=include_root))

        return dependencies

    def get_schema_options(self):
        """ get schema options of object for l5x compilation
            override this method to return a key-value pair (dictionary) of options to be appended to l5x files
            """
        return {
            'TargetClass': self.logix_class.value,
            'TargetRevision': self.revision,
            'TargetLastEdited': self.edited_date
        }

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        super().rename_strings(_old_name, _new_name)
        self.name = self.name.replace(_old_name, _new_name)
        self.description = self.description.replace(_old_name, _new_name)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        aoi_root = root.createElement('AddOnInstructionDefinition')

        if as_target:
            aoi_root.setAttribute('Use', 'Target')

        aoi_root.setAttribute('Name', self.name)
        aoi_root.setAttribute('Class', self.logix_class.value.__str__())
        aoi_root.setAttribute('Revision', self.revision)
        aoi_root.setAttribute('Vendor', self.vendor)
        aoi_root.setAttribute('ExecutePrescan', bool_to_l5x(self.execute_prescan))
        aoi_root.setAttribute('ExecutePostscan', bool_to_l5x(self.execute_postscan))
        aoi_root.setAttribute('ExecuteEnableInFalse', bool_to_l5x(self.execute_enable_in_false))
        aoi_root.setAttribute('CreatedDate', self.created_date if self.created_date else "2023-04-13T12:30:52.518Z")
        aoi_root.setAttribute('CreatedBy', self.created_by)
        aoi_root.setAttribute('EditedDate', self.edited_date if self.edited_date else "2023-12-26T18:39:04.664Z")
        aoi_root.setAttribute('EditedBy', self.edited_by)
        aoi_root.setAttribute('SoftwareRevision', self.software_revision)

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            desc_root.appendChild(root.createTextNode(''))
            aoi_root.appendChild(desc_root)

        if self.revision_note:
            rev_root = root.createElement('RevisionNote')
            rev_root.appendChild(root.createCDATASection(self.revision_note))
            rev_root.appendChild(root.createTextNode(''))
            aoi_root.appendChild(rev_root)

        parameters_root = root.createElement('Parameters')
        for param in self.parameters:
            parameters_root.appendChild(param.to_l5x_xml_node(root))
        aoi_root.appendChild(parameters_root)

        local_tags_root = root.createElement('LocalTags')
        for tag in self.tags:
            local_tags_root.appendChild(tag.to_l5x_xml_node(root))
        aoi_root.appendChild(local_tags_root)

        routines_root = root.createElement('Routines')
        for routine in self.routines:
            routines_root.appendChild(routine.to_l5x_xml_node(root))
        aoi_root.appendChild(routines_root)

        return aoi_root


class AddOnInstructionList(PylogixList):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        return AddOnInstructionDefinition
