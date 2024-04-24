#!/usr/bin/env python

""" module
    derived from cla_logix_object
    this class represents an Allen Bradley Module
    """

# pylogix imports #
from l5x import conditional_xml_write, get_text_data, get_first_element, bool_to_l5x, bool_from_l5x
from base import PyLogixObject, EKeyState, ModulePortType, PylogixList

# python std lib imports #
from typing import Self
from xml.dom import minidom


class ModulePort(PyLogixObject):
    def __init__(self,
                 port_id: int | None = 0,
                 address: str | None = None,
                 port_type: ModulePortType | None = None,
                 upstream: bool = True,
                 safety_network_number: str | None = None,
                 bus_size: int | None = None):
        super().__init__('',
                         '')
        self.port_id = port_id
        self.address = address
        self.port_type = port_type
        self.upstream = upstream
        self.safety_network_number = safety_network_number
        self.bus_size = bus_size

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        """ abstract implementation of from_l5x method\n
            to implement, compile cls from passed l5x_node\n
            in the derived class"""
        if not xml_node:
            return None
        bus_xml = xml_node.getElementsByTagName('Bus')
        if bus_xml:
            try:
                bus_size = int(bus_xml[0].getAttribute('Size'))
            except ValueError:
                bus_size = None
        else:
            bus_size = None

        # create port object
        return cls(int(xml_node.getAttribute('Id')),
                   xml_node.getAttribute('Address'),
                   ModulePortType.from_string(xml_node.getAttribute('Type')),
                   bool_from_l5x(xml_node.getAttribute('Upstream')),
                   xml_node.getAttribute('SafetyNetwork'),
                   bus_size)

    def to_l5x(self, root: minidom.Document) -> minidom.Element:
        port_root = root.createElement('Port')
        port_root.setAttribute('Id', str(self.port_id))

        if self.address:
            port_root.setAttribute('Address', str(self.address))

        port_root.setAttribute('Type', self.port_type.value.__str__())
        port_root.setAttribute('Upstream', bool_to_l5x(self.upstream))

        if self.safety_network_number:
            port_root.setAttribute('SafetyNetwork', self.safety_network_number)

        if self.bus_size:
            bus_size_root = root.createElement('Bus')
            bus_size_root.setAttribute('Size', str(self.bus_size))
            port_root.appendChild(bus_size_root)

        return port_root


class Module(PyLogixObject):
    """ logix module
        """

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 catalog_number: str | None = None,
                 vendor: int | None = None,
                 product_type: int | None = None,
                 product_code: int | None = None,
                 major: int | None = None,
                 minor: int | None = None,
                 mod_parent: Self | None = None,
                 mod_parent_name: str | None = None,
                 mod_parent_port_id: int | None = None,
                 inhibited: bool = False,
                 major_fault: bool = False,
                 ekey_state: EKeyState = EKeyState.disabled,
                 safety_network_number: str | None = None,
                 safety_enabled: bool = False,
                 user_defined_vendor: str | None = None,
                 user_defined_product_type: str | None = None,
                 user_defined_product_code: str | None = None,
                 user_defined_major: str | None = None,
                 user_defined_minor: str | None = None):
        super().__init__(name,
                         description)
        self.catalog_number = catalog_number
        self.vendor = vendor
        self.product_type = product_type
        self.product_code = product_code
        self.major = major
        self.minor = minor
        self.mod_parent = mod_parent
        self.parent_name = mod_parent_name
        self.parent_port_id = mod_parent_port_id if mod_parent_port_id else 2
        self.inhibited = inhibited
        self.major_fault = major_fault
        self.ekey_state = ekey_state
        self.safety_network_number = safety_network_number
        self.safety_enabled = safety_enabled
        self.user_defined_vendor = user_defined_vendor
        self.user_defined_product_type = user_defined_product_type
        self.user_defined_product_code = user_defined_product_code
        self.user_defined_major = user_defined_major
        self.user_defined_minor = user_defined_minor
        self.ports: [ModulePort] = []
        self.communications: {} = {}
        self.extended_properties: {} = {}

    @classmethod
    def __build_module_dict_from_l5x__(cls, node: minidom.Element, dictionary_entry: {}):

        key_index = 0  # use a key index to disambiguate keys, L5X (xml, really) files allow duplicate naming for node children
        # key index is really just a throw-away variable, so we can use it across for-loops
        for key, value in node.attributes.items():
            dictionary_entry[(key, key_index)] = value
            key_index += 1

        for child_node in [n for n in node.childNodes if (isinstance(n, minidom.Element)) and (n.parentNode == node)]:
            dictionary_entry[(child_node.localName, key_index)] = {}
            cls.__build_module_dict_from_l5x__(child_node, dictionary_entry[(child_node.localName, key_index)])
            key_index += 1

        if not node.firstChild:
            return
        try:
            if not node.firstChild.wholeText:
                return
            if ((node.firstChild.wholeText == '\n') |
                    (node.firstChild.wholeText == ' ')):
                return

            dictionary_entry['wholeText'] = node.firstChild.wholeText
        except AttributeError:
            return

    @classmethod
    def __write_module_dict_to_l5x__(cls, node: minidom.Element, root: minidom.Document, dictionary_entry: {},
                                     key_name: str) -> minidom.Element:
        this_root = root.createElement(key_name)

        for key, value in dictionary_entry.items():
            if type(value) is dict:
                if type(key) is tuple:
                    key_name = key[0]
                else:
                    key_name = key
                this_root.appendChild(cls.__write_module_dict_to_l5x__(this_root, root, value, key_name))
            else:
                if type(key) is tuple:
                    key_name = key[0]
                else:
                    key_name = key
                """ check if we need to append any 'wholeText' data
                    (data not assigned to an attribute)
                    """
                if key_name == 'wholeText':  # this key is special. It is reserved for wholeText of the node (if applicable)
                    this_root.appendChild(root.createTextNode(dictionary_entry['wholeText']))
                else:
                    this_root.setAttribute(key_name, value)

        return this_root

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        if not xml_node:
            return None
        module = cls(xml_node.getAttribute('Name'),
                     get_text_data(xml_node, 'Description'),
                     xml_node.getAttribute('CatalogNumber'),
                     int(xml_node.getAttribute('Vendor')),
                     int(xml_node.getAttribute('ProductType')),
                     int(xml_node.getAttribute('ProductCode')),
                     int(xml_node.getAttribute('Major')),
                     int(xml_node.getAttribute('Minor')),
                     None,
                     xml_node.getAttribute('ParentModule'),
                     int(xml_node.getAttribute('ParentModPortId')),
                     True if xml_node.getAttribute('Inhibited') == 'true' else False,
                     True if xml_node.getAttribute('MajorFault') == 'true' else False,
                     EKeyState.from_string(
                         xml_node.getElementsByTagName('EKey')[0].getAttribute('State')),
                     xml_node.getAttribute('SafetyNetwork'),
                     True if xml_node.getAttribute('SafetyEnabled') == 'true' else False,
                     xml_node.getAttribute('UserDefinedVendor'),
                     xml_node.getAttribute('UserDefinedProductType'),
                     xml_node.getAttribute('UserDefinedProductCode'),
                     xml_node.getAttribute('UserDefinedMajor'),
                     xml_node.getAttribute('UserDefinedMinor'))

        ports_list_xml = xml_node.getElementsByTagName('Ports')[0]
        if ports_list_xml:
            module.ports.extend([ModulePort.from_l5x_xml_node(port_node) for port_node in
                                 [x for x in ports_list_xml.childNodes if isinstance(x, minidom.Element)]])

        communications_xml = get_first_element(xml_node, 'Communications')
        if communications_xml:
            module.communications['Communications'] = {}
            module.__build_module_dict_from_l5x__(communications_xml,
                                                  module.communications['Communications'])

        extended_properties_xml = get_first_element(xml_node, 'ExtendedProperties')
        if extended_properties_xml:
            module.extended_properties['ExtendedProperties'] = {}
            module.__build_module_dict_from_l5x__(extended_properties_xml,
                                                  module.extended_properties['ExtendedProperties'])

        return module

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        """ abstract implementation of to_l5x_xml_node
            to implement, create and write an xml node and return it
            in the derived class"""
        module_root = root.createElement('Module')

        if self.name:
            module_root.setAttribute('Name', self.name)

        module_root.setAttribute('CatalogNumber', self.catalog_number)
        module_root.setAttribute('Vendor', str(self.vendor))
        module_root.setAttribute('ProductType', str(self.product_type))
        module_root.setAttribute('ProductCode', str(self.product_code))
        module_root.setAttribute('Major', str(self.major))
        module_root.setAttribute('Minor', str(self.minor))

        conditional_xml_write(module_root, 'UserDefinedVendor', self.user_defined_vendor)
        conditional_xml_write(module_root, 'UserDefinedProductType', self.user_defined_product_type)
        conditional_xml_write(module_root, 'UserDefinedProductCode', self.user_defined_product_code)
        conditional_xml_write(module_root, 'UserDefinedMajor', self.user_defined_major)
        conditional_xml_write(module_root, 'UserDefinedMinor', self.user_defined_minor)

        module_root.setAttribute('ParentModule', self.parent_name)
        module_root.setAttribute('ParentModPortId', str(self.parent_port_id))
        module_root.setAttribute('Inhibited', bool_to_l5x(self.inhibited))
        module_root.setAttribute('MajorFault', bool_to_l5x(self.major_fault))

        if self.safety_enabled:
            module_root.setAttribute('SafetyEnabled', bool_to_l5x(self.safety_enabled))

        if self.safety_network_number:
            module_root.setAttribute('SafetyNetwork', self.safety_network_number)

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            module_root.appendChild(desc_root)

        ekey_root = root.createElement('EKey')
        ekey_root.setAttribute('State', self.ekey_state.value)
        module_root.appendChild(ekey_root)

        ports_root = root.createElement('Ports')
        for port in self.ports:
            ports_root.appendChild(port.to_l5x(root))
        module_root.appendChild(ports_root)

        if self.communications:
            module_root.appendChild(self.__write_module_dict_to_l5x__(module_root,
                                                                      root,
                                                                      self.communications['Communications'],
                                                                      'Communications'))

        if self.extended_properties:
            module_root.appendChild(self.__write_module_dict_to_l5x__(module_root,
                                                                      root,
                                                                      self.extended_properties['ExtendedProperties'],
                                                                      'ExtendedProperties'))

        return module_root


class ModuleList(PylogixList):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        return Module
