#!/usr/bin/env python

""" l5x
    this file manages pylogix creating and exporting to/from .L5X files (XML, honestly)
    """
from typing import Any, Callable
from xml.dom import minidom


def conditional_xml_write(element: minidom.Element,
                          attribute_name: str,
                          attribute: Any):
    """ if a passed attribute is NOT none, write the attribute to the element's attribute list
    """
    if attribute:
        element.setAttribute(attribute_name, attribute.__str__())


def generic_controller_wrapper(doc: minidom.Document,
                               name: str,
                               use: str | None = None) -> minidom.Element:
    ctrl = doc.createElement('Controller')
    if use:
        ctrl.setAttribute('Use', use)
    ctrl.setAttribute('Name', name)
    return ctrl


def get_first_element(element: minidom.Element | minidom.Document,
                      element_name: str) -> minidom.Element | None:
    """ helper function to get the first element of a minidom document's children
    :param element: minidom.Element
    :param element_name: name of element to find
    :param is_controller_child: boolean to indicate element to look for is a child of controller element
    :returns: minidom.Element"""
    nodes = element.getElementsByTagName(element_name)
    return nodes[0] if len(nodes) > 0 else None


def get_text_data(element: minidom.Element,
                  text_to_find: str):
    """ helper function to get specified text data from an element node\n
        this helps with parsing l5x files
        :param element: element from minidom to inspect for text data
        :param text_to_find: text to find in nodes
        """
    node_list = element.getElementsByTagName(text_to_find)
    return node_list[0].firstChild.wholeText.strip() if len(node_list) > 0 else None


def bool_from_l5x(l5x_bool_str: str) -> bool:
    return True if l5x_bool_str == 'true' else False


def bool_to_l5x(my_bool: bool) -> str:
    return 'true' if my_bool is True else 'false'


def l5x_content_wrapper(target_type: str,
                        target_name: str | None = None,
                        contains_context: bool = False,
                        export_options: str = '',
                        **kwargs) -> (minidom.Document, minidom.Element):
    # create root information for xml doc
    root = minidom.Document()
    root.encoding = 'UTF-8'
    root.standalone = True
    root.createAttribute('encoding')

    # create rslogix5000 content section
    rslogix5000Content = root.createElement('RSLogix5000Content')
    rslogix5000Content.setAttribute('SchemaRevision', '1.0')
    rslogix5000Content.setAttribute('SoftwareRevision', '32.04')
    if target_name:
        rslogix5000Content.setAttribute('TargetName', target_name)
    rslogix5000Content.setAttribute('TargetType', target_type)

    if len(kwargs.items()) > 0:
        for k, v in kwargs.items():
            rslogix5000Content.setAttribute(k, v)

    rslogix5000Content.setAttribute('ContainsContext', 'true' if contains_context else 'false')
    rslogix5000Content.setAttribute('ExportDate', 'Sat Jan 13 12:30:38 2024')
    rslogix5000Content.setAttribute('ExportOptions', export_options)
    root.appendChild(rslogix5000Content)
    return root, rslogix5000Content


def open_l5x_to_controller_node(l5x_path: str) -> minidom.Element:
    xml_doc = minidom.parse(l5x_path)

    logixContent = xml_doc.getElementsByTagName('RSLogix5000Content')
    if not logixContent:
        raise ValueError('incorrect file received. Could not located RSLogix5000Content')

    controller_xml = get_first_element(xml_doc, 'Controller')
    if not controller_xml:
        raise ValueError(f'could not locate controller node. incorrect file received.')

    return controller_xml


def write_xml_to_l5x(doc: minidom.Document,
                     save_location: str):
    if not save_location.endswith('.L5X'):
        save_location += '.L5X'
    with open(f'{save_location}', 'w') as f:
        f.write(doc.toprettyxml(indent='').replace('<?xml version="1.0" ?>',
                                                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'))
