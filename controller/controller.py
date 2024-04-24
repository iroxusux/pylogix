#!/usr/bin/env python

""" controller
    derived from pylogix_object
    this class represents an Allen Bradley Logix Controller
    """

# pylogix imports #
from add_on_instruction import AddOnInstructionList
from datatype import DataTypeList
from l5x import get_text_data, get_first_element, bool_from_l5x, bool_to_l5x, open_l5x_to_controller_node, \
    write_xml_to_l5x, l5x_content_wrapper
from base import PyLogixObject, ExtendedEnum, PyLogixDependencies, LogixTagType
from module import ModuleList
from program import Program, ProgramList
from tag import Tag, TagList
from task import TaskList

# python std lib imports #
from copy import copy
from typing import Callable, Self
from xml.dom import minidom


class ControllerRedundancyInfo(PyLogixObject):
    def __init__(self,
                 enabled: bool = True,
                 keep_test_edits_on_switch_over: bool = True):
        super().__init__('',
                         '')
        self.enabled = enabled
        self.keep_test_edits_on_switch_over = keep_test_edits_on_switch_over

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          class_constructor: type[Self] | None = None,
                          *args,
                          **kwargs):
        if not xml_node:
            return None
        return cls(True if xml_node.getAttribute('Enabled') == 'true' else False,
                   True if xml_node.getAttribute('KeepTestEditsOnSwitchOver') == 'true' else False)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        redundancy_root = root.createElement('RedundancyInfo')
        redundancy_root.setAttribute('Enabled', bool_to_l5x(self.enabled))
        redundancy_root.setAttribute('KeepTestEditsOnSwitchOver', bool_to_l5x(self.keep_test_edits_on_switch_over))
        return redundancy_root


class ControllerSecurity(PyLogixObject):
    def __init__(self,
                 code: int = 0,
                 changes_to_detect: str = ''):
        super().__init__('',
                         '')
        self.code = code
        self.changes_to_detect = changes_to_detect

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          class_constructor: type[Self] | None = None,
                          *args,
                          **kwargs):
        if not xml_node:
            return None
        return cls(int(xml_node.getAttribute('Code')),
                   xml_node.getAttribute('ChangesToDetect'))

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        security_root = root.createElement('Security')
        security_root.setAttribute('Code', '0' if not self.code else self.code)
        security_root.setAttribute('ChangesToDetect', self.changes_to_detect)
        return security_root


class ControllerSafetyInfo(PyLogixObject):
    class SafetyLevel(ExtendedEnum):
        sil2 = r'SIL2/PLd'

    def __init__(self,
                 safety_signature: str | None = None,
                 safety_locked: bool = False,
                 signature_runmode_protect: bool = False,
                 configure_safe_io_always: bool = False,
                 safety_level: SafetyLevel = False,
                 safety_lock_password: str | None = None,
                 safety_unlock_password: str | None = None, ):
        super().__init__('',
                         '')
        self.safety_signature = safety_signature
        self.safety_locked = safety_locked
        self.signature_runmode_protect = signature_runmode_protect
        self.configure_safe_io_always = configure_safe_io_always
        self.safety_level = safety_level
        self.safety_lock_password = safety_lock_password
        self.safety_unlock_password = safety_unlock_password
        self.safety_tag_map: [str] = []

    @classmethod
    def from_l5x_xml_node(cls,
                          xml_node: minidom.Element,
                          class_constructor: type[Self] | None = None,
                          *args,
                          **kwargs):
        if not xml_node:
            return None
        return cls(xml_node.getAttribute('SafetySignature'),
                   True if xml_node.getAttribute('SafetyLocked') == 'true' else False,
                   bool_from_l5x(xml_node.getAttribute('SignatureRunModeProtect')),
                   bool_from_l5x(xml_node.getAttribute('ConfigureSafetyIOAlways')),
                   cls.SafetyLevel.from_string(xml_node.getAttribute('SafetyLevel')),
                   xml_node.getAttribute('SafetyLockPassword'),
                   xml_node.getAttribute('SafetyUnlockPassword'))

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        safety_root = root.createElement('SafetyInfo')
        if self.safety_signature:
            safety_root.setAttribute('SafetySignature', self.safety_signature)
        safety_root.setAttribute('SafetyLocked', bool_to_l5x(self.safety_locked))
        if self.safety_lock_password:
            safety_root.setAttribute('SafetyLockPassword', self.safety_lock_password)
        if self.safety_unlock_password:
            safety_root.setAttribute('SafetyUnlockPassword', self.safety_unlock_password)
        safety_root.setAttribute('SignatureRunModeProtect', bool_to_l5x(self.signature_runmode_protect))
        safety_root.setAttribute('ConfigureSafetyIOAlways', bool_to_l5x(self.configure_safe_io_always))
        safety_root.setAttribute('SafetyLevel', self.safety_level.value)
        if len(self.safety_tag_map) > 0:
            safety_tag_map = root.createElement('SafetyTagMap')
            safety_tag_map.appendChild(root.createTextNode(', '.join(self.safety_tag_map)))
            safety_root.appendChild(safety_tag_map)
        return safety_root


class Controller(PyLogixObject):
    """ pylogix allen bradley logix controller
    """

    class ControllerType(ExtendedEnum):
        l82es = '1756-L82ES'
        l83es = '1756-L83ES'

    class SFCExecutionControl(ExtendedEnum):
        current_active = 'CurrentActive'

    class SFCRestartPosition(ExtendedEnum):
        most_recent = 'MostRecent'

    class SFCLastScan(ExtendedEnum):
        dont_scan = 'DontScan'

    class LogixPassThroughConfiguration(ExtendedEnum):
        enabled_with_append = 'EnabledWithAppend'

    def __init__(self,
                 name: str,
                 description: str | None,
                 controller_type: ControllerType | None = None,
                 major_rev: int = 0,
                 minor_rev: int = 0,
                 sfc_execution_ctrl: SFCExecutionControl | None = None,
                 sfc_restart_pos: SFCRestartPosition | None = None,
                 sfc_last_scan: SFCLastScan | None = None,
                 comm_path: str | None = None,
                 redundancy_info: ControllerRedundancyInfo | None = None,
                 security_info: ControllerSecurity | None = None,
                 safety_info: ControllerSafetyInfo | None = None,
                 project_sn: str | None = None,
                 match_project_to_controller: bool = False,
                 can_use_rpi_from_producer: bool = False,
                 inhibit_automatic_firmware_update: int = 0,
                 pass_through_configuration: LogixPassThroughConfiguration | None = None,
                 download_extended_properties: bool = False,
                 download_custom_properties: bool = False,
                 report_minor_overflow: bool = False):
        super().__init__(name,
                         description)
        self.controller_type = controller_type
        self.major_rev = major_rev
        self.minor_rev = minor_rev
        self.sfc_execution_ctrl = sfc_execution_ctrl
        self.sfc_restart_pos = sfc_restart_pos
        self.sfc_last_scan = sfc_last_scan
        self.comm_path = comm_path
        self.redundancy_info = redundancy_info
        self.security_info = security_info
        self.safety_info = safety_info
        self.project_sn = project_sn
        self.match_project_to_controller = match_project_to_controller
        self.can_use_rpi_from_producer = can_use_rpi_from_producer
        self.inhibit_automatic_firmware_update = inhibit_automatic_firmware_update
        self.pass_through_configuration = pass_through_configuration
        self.download_extended_properties = download_extended_properties
        self.download_custom_properties = download_custom_properties
        self.report_minor_overflow = report_minor_overflow
        self.datatypes: DataTypeList = DataTypeList()
        self.modules: ModuleList = ModuleList()
        self.add_on_instructions: AddOnInstructionList = AddOnInstructionList()
        self.tags: TagList = TagList()
        self.programs: ProgramList = ProgramList()
        self.tasks: TaskList = TaskList()

        """ setup callbacks
        """
        self.on_add: [Callable] = []

    @property
    def l5x_node_name(self):
        return 'Controller'

    def __on_add__(self, obj: PyLogixObject):
        for callback in self.on_add:
            callback(obj)

    def __resolve_tag_aliases__(self,
                                dependencies: PyLogixDependencies):
        for tag in [t for t in dependencies.tags if t.alias_for is not None and t.alias_for != '']:
            new_tag: Tag = copy(tag)
            new_tag.alias_for = None
            new_tag.name = tag.alias_for
            new_tag.tag_type = LogixTagType.base
            new_tag.datatype = next((x for x in self.datatypes if x.name == new_tag.datatype_meta_name), None)
            self.tags.append(new_tag,
                             True)
        return

    @staticmethod
    def __safe_add__(obj: object, lst: []) -> bool:
        """ safely add an object into a list based on presence in list
            :param obj: object to add to controller. must be a controller-type object
            :param lst: list to add object to
            :returns: boolean of success
                """
        if obj not in lst:
            lst.append(obj)
            return True
        return False

    @staticmethod
    def __safe_remove__(obj: object, lst: []) -> bool:
        """ safely add an object into a list based on presence in list
            :param obj: object to be removed
            :param lst: list to remove object from
            :returns: boolean of success
                """
        if obj in lst:
            lst.remove(obj)
            return True
        return False

    def all_objects(self) -> []:
        return self.datatypes + self.modules + self.add_on_instructions + self.tags + self.programs + self.tasks

    def append(self,
               obj: PyLogixObject) -> bool:
        """ dynamically append object to controller based on match case
        :param obj: object to append to controller
        :returns: boolean of success
        """

        match type(obj):
            case self.datatypes.object_constructor_type:
                return self.datatypes.append(obj)
            case self.modules.object_constructor_type:
                return self.modules.append(obj)
            case self.add_on_instructions.object_constructor_type:
                return self.add_on_instructions.append(obj)
            case self.tags.object_constructor_type:
                return self.tags.append(obj)
            case self.programs.object_constructor_type:
                return self.programs.append(obj)
            case self.tasks.object_constructor_type:
                return self.tasks.append(obj)
        raise TypeError(f'object {obj.__name__} could not be appended to the controller!\n'
                        f'Validate the object is a controller object!')

    @classmethod
    def clone_to_new_controller(cls, existing_controller: type[Self]) -> Self:
        raise NotImplementedError('not yet...')

    @classmethod
    def from_l5x(cls,
                 l5x_path: str,
                 *args,
                 **kwargs) -> Self | None:
        """ create a controller object (or supplied type class) from a l5x node
        :param l5x_path: l5x path to parse and create controller object from
        :type l5x_path: str
        :param class_constructor: class to create controller objects from
        :type class_constructor: type[Self] | None
        :return: type[Self] | None
        """
        if not l5x_path:
            return None

        controller_node = open_l5x_to_controller_node(l5x_path)
        try:
            constructor = kwargs['constructor'] if kwargs['constructor'] else cls
        except KeyError:
            constructor = cls

        controller = constructor(controller_node.getAttribute('Name'),
                                 get_text_data(controller_node, 'Description'),
                                 cls.ControllerType.from_string(controller_node.getAttribute('ProcessorType')),
                                 int(controller_node.getAttribute('MajorRev')),
                                 int(controller_node.getAttribute('MinorRev')),
                                 cls.SFCExecutionControl.from_string(
                                     controller_node.getAttribute('SFCExecutionControl')),
                                 cls.SFCRestartPosition.from_string(
                                     controller_node.getAttribute('SFCRestartPosition')),
                                 cls.SFCLastScan.from_string(controller_node.getAttribute('SFCLastScan')),
                                 controller_node.getAttribute('CommPath'),
                                 ControllerRedundancyInfo.from_l5x_xml_node(
                                     get_first_element(controller_node, 'RedundancyInfo')),
                                 ControllerSecurity.from_l5x_xml_node(get_first_element(controller_node, 'Security')),
                                 ControllerSafetyInfo.from_l5x_xml_node(
                                     get_first_element(controller_node, 'SafetyInfo')),
                                 controller_node.getAttribute('ProjectSN'),
                                 bool_from_l5x(controller_node.getAttribute('MatchProjectToController')),
                                 bool_from_l5x(controller_node.getAttribute('CanUseRPIFromProducer')),
                                 int(controller_node.getAttribute('InhibitAutomaticFirmwareUpdate')),
                                 cls.LogixPassThroughConfiguration.from_string(
                                     controller_node.getAttribute('PassThroughConfiguration')),
                                 bool_from_l5x(controller_node.getAttribute(
                                     'DownloadProjectDocumentationAndExtendedProperties')),
                                 bool_from_l5x(controller_node.getAttribute('DownloadProjectCustomProperties')),
                                 bool_from_l5x(controller_node.getAttribute('ReportMinorOverflow')))

        kwargs['controller'] = controller
        kwargs['ctrl_node'] = controller_node

        controller.datatypes.from_l5x(l5x_path,
                                      **kwargs)

        kwargs['datatypes'] = controller.datatypes

        controller.modules.from_l5x(l5x_path,
                                    **kwargs)

        kwargs['modules'] = controller.modules

        controller.add_on_instructions.from_l5x(l5x_path,
                                                **kwargs)

        kwargs['add_on_instructions'] = controller.add_on_instructions

        controller.tags.from_l5x(l5x_path,
                                 **kwargs)

        kwargs['tags'] = controller.tags

        controller.programs.from_l5x(l5x_path,
                                     **kwargs)

        kwargs['programs'] = controller.programs

        controller.tasks.from_l5x(l5x_path,
                                  **kwargs)

        controller.rebind()
        return controller

    def import_with_dependencies(self,
                                 obj: PyLogixObject,
                                 include_root: bool = False):
        self.resolve_dependencies(obj.get_dependencies(include_root=include_root))

    def push_updates(self,
                     other_obj: Self,
                     *args,
                     **kwargs):
        if type(other_obj) is not type(self):
            raise ValueError(f'Type of self: {type(self)} does not match type of other object: {type(other_obj)}.')
        other_obj.resolve_dependencies(self.programs.push_updates(other_obj.programs))

    def rebind(self) -> None:
        kwargs = {
            'datatypes': self.datatypes,
            'tags': self.tags,
            'modules': self.modules,
            'programs': self.programs,
            'add_on_instructions': self.add_on_instructions,
            'tasks': self.tasks,
        }
        super().rebind()
        self.datatypes.rebind(**kwargs)
        self.tags.rebind(**kwargs)
        self.modules.rebind(**kwargs)
        self.programs.rebind(**kwargs)
        self.add_on_instructions.rebind(**kwargs)
        self.tasks.rebind(**kwargs)

    def remove(self,
               obj: PyLogixObject) -> bool:
        """ dynamically remove object from controller based on match case
        :param obj: object to remove from controller
        :returns: boolean of success
        """

        match type(obj):
            case self.datatypes.object_constructor_type:
                return self.datatypes.remove(obj)
            case self.modules.object_constructor_type:
                return self.modules.remove(obj)
            case self.add_on_instructions.object_constructor_type:
                return self.add_on_instructions.remove(obj)
            case self.tags.object_constructor_type:
                return self.tags.remove(obj)
            case self.programs.object_constructor_type:
                return self.programs.remove(obj)
            case self.tasks.object_constructor_type:
                return self.tasks.remove(obj)
        raise TypeError(f'object {obj.__name__} could not be removed from the controller!\n'
                        f'Validate the object is a controller object!')

    def resolve_dependencies(self,
                             dependencies: PyLogixDependencies):
        self.add_on_instructions.extend(dependencies.add_on_instructions,
                                        True)
        self.datatypes.extend([d for d in dependencies.datatypes if not d.description_properties.editable],
                              True)
        self.modules.extend(dependencies.modules,
                            True)
        self.resolve_program_dependencies(dependencies)
        self.tags.extend(dependencies.tags,
                         True)
        self.tasks.extend(dependencies.tasks,
                          True)
        self.__resolve_tag_aliases__(dependencies)
        self.rebind()

    def resolve_program_dependencies(self,
                                     dependencies: PyLogixDependencies):
        """ abstract implementation of resolving program dependencies
            override this method as required to more finely resolve dependencies in an inheriting class
            """
        self.programs.extend(dependencies.programs,
                             True)

    def to_l5x(self,
               controller_name: str,
               save_location: str) -> None:
        export_options = self.get_schema_options()
        root, rslogix5000Content = l5x_content_wrapper(self.l5x_node_name,
                                                       self.name,
                                                       True,
                                                       'References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans',
                                                       **export_options)
        ctrl = self.to_l5x_xml_node(root,
                                    True)
        rslogix5000Content.appendChild(ctrl)

        """ generate description
        """
        if self.description:  # append description if exists
            desc_root = root.createElement('Description')
            desc_root.appendChild(root.createCDATASection(self.description))
            desc_root.appendChild(root.createTextNode(''))
            ctrl.appendChild(desc_root)

        """ generate redundancy info
        """
        if self.redundancy_info:
            ctrl.appendChild(self.redundancy_info.to_l5x_xml_node(root))

        if self.security_info:
            ctrl.appendChild(self.security_info.to_l5x_xml_node(root))

        if self.safety_info:
            ctrl.appendChild(self.safety_info.to_l5x_xml_node(root))

        ctrl.appendChild(self.datatypes.to_l5x_xml_node(root))
        ctrl.appendChild(self.modules.to_l5x_xml_node(root))
        ctrl.appendChild(self.add_on_instructions.to_l5x_xml_node(root))
        ctrl.appendChild(self.tags.to_l5x_xml_node(root))
        ctrl.appendChild(self.programs.to_l5x_xml_node(root))
        ctrl.appendChild(self.tasks.to_l5x_xml_node(root))

        # create anscillary data
        cst = root.createElement('CST')
        cst.setAttribute('MasterID', "0")
        ctrl.appendChild(cst)

        wct = root.createElement('WallClockTime')
        wct.setAttribute('LocalTimeAdjustment', '0')
        wct.setAttribute('TimeZone', '0')
        ctrl.appendChild(wct)

        ts = root.createElement('TimeSynchronize')
        ts.setAttribute('Priority1', '128')
        ts.setAttribute('Priority2', '128')
        ts.setAttribute('PTPEnable', 'true')
        ctrl.appendChild(ts)

        eps = root.createElement('EthernetPorts')
        ep = root.createElement('EthernetPort')
        ep.setAttribute('Port', '1')
        ep.setAttribute('Label', '1')
        ep.setAttribute('PortEnable', 'true')
        eps.appendChild(ep)
        ctrl.appendChild(eps)

        # append content to root, then return
        write_xml_to_l5x(root,
                         save_location)

    def to_l5x_xml_node(self,
                        root: minidom.Document,
                        as_target: bool = False,
                        include_dependencies: bool = False) -> minidom.Element:
        """ abstract implementation of to_l5x_xml_node
            to implement, create and write an xml node and return it
            in the derived class"""
        ctrl_root = root.createElement('Controller')

        if as_target:
            ctrl_root.setAttribute('Use', 'Target')

        ctrl_root.setAttribute('Name', self.name)
        ctrl_root.setAttribute('ProcessorType', self.controller_type.value.__str__())
        ctrl_root.setAttribute('MajorRev', self.major_rev.__str__())
        ctrl_root.setAttribute('MinorRev', self.minor_rev.__str__())
        ctrl_root.setAttribute('ProjectCreationDate', "Fri Oct 06 12:49:55 2023")
        ctrl_root.setAttribute('LastModifiedDate', "Thu Jan 11 16:29:06 2024")
        ctrl_root.setAttribute('SFCExecutionControl', self.sfc_execution_ctrl.value.__str__())
        ctrl_root.setAttribute('SFCRestartPosition', self.sfc_restart_pos.value.__str__())
        ctrl_root.setAttribute('SFCLastScan', self.sfc_last_scan.value.__str__())
        ctrl_root.setAttribute('CommPath', self.comm_path)
        ctrl_root.appendChild(root.createTextNode(''))
        if self.project_sn:  # idk if all controllers have serial numbers or not, so just in case...
            ctrl_root.setAttribute('ProjectSN', self.project_sn)
        ctrl_root.setAttribute('MatchProjectToController', 'true' if self.match_project_to_controller else 'false')
        ctrl_root.setAttribute('CanUseRPIFromProducer', 'true' if self.can_use_rpi_from_producer else 'false')
        ctrl_root.setAttribute('InhibitAutomaticFirmwareUpdate',
                               '0' if not self.inhibit_automatic_firmware_update else self.inhibit_automatic_firmware_update)
        ctrl_root.setAttribute('PassThroughConfiguration', str(self.pass_through_configuration.value))
        ctrl_root.setAttribute('DownloadProjectDocumentationAndExtendedProperties',
                               bool_to_l5x(self.download_extended_properties))
        ctrl_root.setAttribute('DownloadProjectCustomProperties', bool_to_l5x(self.download_custom_properties))
        ctrl_root.setAttribute('ReportMinorOverflow', bool_to_l5x(self.report_minor_overflow))

        return ctrl_root
