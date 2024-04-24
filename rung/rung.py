#!/usr/bin/env python

""" rung
    derived from cla_logix_object
    this class represents an Allen Bradley Rung
    """

# pylogix imports #
from base import LogixRungType, PyLogixObject, PyLogixDependencies, PylogixList
from l5x import get_text_data
from tag import TagList

# python std lib imports #
from copy import copy
from itertools import chain
import re
from xml.dom import minidom


class Rung(PyLogixObject):
    """ logix rung
        """

    def __init__(self,
                 description: str | None = None,
                 number: int = None,
                 rung_type: LogixRungType | None = None,
                 text: str | None = None,
                 comment: str | None = None):
        """ initialize this class
            :return: object that contains information about a rung in logic
            """
        super().__init__('',
                         description)
        self.number = number
        self.rung_type = rung_type
        self.text = text
        self.tags: TagList = TagList()
        self.program_tags: TagList = TagList()
        self.add_on_instructions: [] = []
        self.comment: str | None = comment

    def __get_tag_metas__(self) -> [str]:
        if not self.text:
            return []

        iter_instructions = list(chain.
        from_iterable(
            [instr[instr.find('(') + 1:].split(',') for instr in self.text.split(')') if '(' in instr]))
        upper_tags_pre = list(set([tag.split('.')[0] for tag in iter_instructions]))

        illegal_chars = [',', '"', "'", '?', ':']
        upper_tags = []
        for tag in upper_tags_pre:  # remove any values that are straight up just a number... these are not dependant on anything
            if not tag:
                continue
            if any(x in tag for x in illegal_chars):
                continue
            try:
                _ = int(tag)
                continue
            except ValueError:
                pass
            bracket_char = tag.find('[')
            if bracket_char != -1:
                tag = tag[:bracket_char]
            upper_tags.append(tag)

        return upper_tags

    def __get_instruction_metas__(self) -> [str]:
        output_instructions = []
        if not self.text:
            return output_instructions
        illegal_chars = [',', '"', "'", '?', ':', '[', ']']
        rx = '[' + re.escape(''.join(illegal_chars)) + ']'
        for instruction in self.text.split(')'):
            inst = instruction[:instruction.find('(')]
            output_instructions.append(re.sub(rx, '', inst).strip())
        return list(set(output_instructions))

    def get_dependencies(self,
                         include_root: bool = False) -> PyLogixDependencies:
        dependencies = PyLogixDependencies()
        [dependencies.safe_add_item(dependencies.tags,
                                    tag) for tag in self.tags]
        [dependencies.safe_add_item(dependencies.program_tags,
                                    program_tag) for program_tag in self.program_tags]
        [dependencies.safe_add_item(dependencies.add_on_instructions,
                                    aoi) for aoi in self.add_on_instructions]
        ([dependencies.extend(tag.datatype.get_dependencies(include_root=True)) for tag in self.tags
          if tag.datatype and
          not tag.datatype.is_atomic and
          not tag.datatype.is_base_logix_instruction])
        ([dependencies.extend(program_tag.datatype.get_dependencies(include_root=True)) for program_tag in
          self.program_tags
          if program_tag.datatype and
          not program_tag.datatype.is_atomic and
          not program_tag.datatype.is_base_logix_instruction])
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
        rung = cls(get_text_data(xml_node, 'Description'),
                   int(xml_node.getAttribute('Number')),
                   LogixRungType.from_string(xml_node.getAttribute('Type')),
                   get_text_data(xml_node, 'Text'),
                   get_text_data(xml_node, 'Comment'))

        try:
            for tag_meta_name in rung.__get_tag_metas__():
                tag = kwargs['tags'].by_name(tag_meta_name)
                if tag:
                    rung.tags.append(tag)
                    continue
                tag = kwargs['program_tags'].by_name(tag_meta_name)
                if tag:
                    rung.program_tags.append(tag)
                    continue
            for instruction in rung.__get_instruction_metas__():
                instr = kwargs['add_on_instructions'].by_name(instruction)
                if instr:
                    rung.add_on_instructions.append(instr)

        except KeyError:
            pass

        return rung

    def to_l5x(self, root: minidom.Document) -> minidom.Element:
        rung_root = root.createElement('Rung')
        rung_root.setAttribute('Number', str(self.number))
        rung_root.setAttribute('Type', self.rung_type.value.__str__())

        if self.comment:
            comment_root = root.createElement('Comment')
            comment_root.appendChild(root.createCDATASection(self.comment))
            rung_root.appendChild(comment_root)

        if self.text:
            text_root = root.createElement('Text')
            text_root.appendChild(root.createCDATASection(self.text))
            rung_root.appendChild(text_root)

        return rung_root

    def rebind(self,
               *args,
               **kwargs) -> None:
        super().rebind(*args,
                       **kwargs)
        try:
            for tag in [t for t in self.tags if t.alias_for and t.alias_for != '']:
                ctrl_tag = kwargs['tags'].by_name(tag.alias_for)
                if not ctrl_tag:
                    continue

                tag_alias_for = tag.alias_for
                tag = copy(ctrl_tag)
                tag.alias_for = tag_alias_for

            for tag in [t for t in self.program_tags if t.alias_for and t.alias_for != '']:
                ctrl_tag = kwargs['tags'].by_name(tag.alias_for)
                if not ctrl_tag:
                    continue

                self.tags.append(ctrl_tag)
        except KeyError:
            return

    def rename_strings(self,
                       _old_name: str,
                       _new_name: str):
        if self.text:
            self.text = self.text.replace(_old_name, _new_name)
        if self.comment:
            self.comment = self.comment.replace(_old_name, _new_name)
        self.tags.rename_strings(_old_name, _new_name)
        self.program_tags.rename_strings(_old_name, _new_name)

    def to_dict(self) -> {}:
        """ compile this rung to a dictionary
            :return: {['comment']['text']}
            """
        return {
            'comment': self.comment,
            'text': ''.join(self.instruction_sequence)
        }


class RungList(PylogixList):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        return Rung
