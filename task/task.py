#!/usr/bin/env python

""" task
    derived from cla_logix_object
    this class represents an Allen Bradley Task
    """

# pylogix imports #
from l5x import get_text_data, bool_to_l5x, bool_from_l5x
from program import Program, ProgramList
from base import TaskType, LogixClass, PyLogixObject, PylogixList, PyLogixDependencies

# python std lib imports #
from xml.dom import minidom


class Task(PyLogixObject):

    def __init__(self,
                 name: str,
                 description: str | None = None,
                 task_type: TaskType | None = None,
                 priority: int = None,
                 watchdog: int = None,
                 disable_update_outputs: bool = False,
                 inhibit_task: bool = False,
                 task_class: LogixClass | None = None,
                 rate: str | None = None):
        super().__init__(name,
                         description)
        self.task_type = task_type
        self.priority = priority
        self.rate = rate
        self.watchdog = watchdog
        self.disable_update_outputs = disable_update_outputs
        self.inhibit_task = inhibit_task
        self.task_class = task_class
        self.scheduled_meta_programs: [str] = []
        self.scheduled_programs: ProgramList = ProgramList()

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          *args,
                          **kwargs):
        if not xml_node:
            return None
        task = cls(xml_node.getAttribute('Name'),
                   get_text_data(xml_node, 'Description'),
                   TaskType.from_string(xml_node.getAttribute('Type')),
                   int(xml_node.getAttribute('Priority')),
                   int(xml_node.getAttribute('Watchdog')),
                   bool_from_l5x(xml_node.getAttribute('DisableUpdateOutputs')),
                   bool_from_l5x(xml_node.getAttribute('InhibitTask')),
                   LogixClass.from_string(xml_node.getAttribute('Class')),
                   xml_node.getAttribute('Rate'))

        # parse through members if they exist
        programs_list_xml = xml_node.getElementsByTagName('ScheduledPrograms')[0]
        if programs_list_xml:
            for program_xml in [x for x in programs_list_xml.childNodes if isinstance(x, minidom.Element)]:
                task.scheduled_programs.append(kwargs['programs'].by_name(program_xml.getAttribute('Name')))
                task.scheduled_meta_programs.append(program_xml.getAttribute('Name'))

        return task

    def get_dependencies(self,
                         include_root: bool = False) -> PyLogixDependencies:
        dependencies = PyLogixDependencies()
        if include_root:
            dependencies.tasks.append(self)
        return dependencies

    def rebind(self,
               *args,
               **kwargs) -> None:
        """ rebind this object as required
        """
        super().rebind()
        self.scheduled_programs = [prog for prog in kwargs['programs'] if prog.name in self.scheduled_meta_programs]

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        task_root = root.createElement('Task')
        task_root.setAttribute('Name', self.name)
        task_root.setAttribute('Type', self.task_type.value.__str__())

        if self.rate:
            task_root.setAttribute('Rate', self.rate)

        task_root.setAttribute('Priority', str(self.priority))
        task_root.setAttribute('Watchdog', str(self.watchdog))
        task_root.setAttribute('DisableUpdateOutputs', bool_to_l5x(self.disable_update_outputs))
        task_root.setAttribute('InhibitTask', bool_to_l5x(self.inhibit_task))
        task_root.setAttribute('Class', self.task_class.value.__str__())

        if self.description:
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            task_root.appendChild(desc_root)

        programs_root = root.createElement('ScheduledPrograms')
        for prog in self.scheduled_programs:
            scheduled_program = root.createElement('ScheduledProgram')
            scheduled_program.setAttribute('Name', prog.name)
            programs_root.appendChild(scheduled_program)

        task_root.appendChild(programs_root)

        return task_root


class TaskList(PylogixList):
    def __init__(self):
        super().__init__()

    @property
    def object_constructor_type(self):
        return Task
