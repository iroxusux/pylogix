#!/usr/bin/env python

""" pylogix_enum
    this file manages enums for pylogix
    """

# pylogix imports #
# ---

# python std lib imports #
import enum


class ExtendedEnum(enum.Enum):
    @classmethod
    def from_string(cls, string: str):
        return next((x for x in cls if x.value == string), None)


class PyLogixObjectStatus(ExtendedEnum):
    master_ok = 1
    master_warning = 2
    user_ok = 3
    user_warning = 4


class EKeyState(ExtendedEnum):
    disabled = 'Disabled'
    compatible_module = 'CompatibleModule'
    exact_match = 'ExactMatch'


class LogixClass(ExtendedEnum):
    no_class = 'N/A'
    standard = 'Standard'
    safety = 'Safety'


class LogixDataTypeClass(ExtendedEnum):
    User = 'User'
    standard = 'Standard'


class LogixRadix(ExtendedEnum):
    Decimal = 'Decimal'
    ASCII = 'ASCII'
    null_type = 'NullType'
    float = 'Float'


class LogixTagType(ExtendedEnum):
    add_on_instruction = 'AddOnInstruction'
    base = 'Base'
    alias = 'Alias'


class LogixFamily(ExtendedEnum):
    no_family = 'NoFamily'
    none = 'None'
    string_family = 'StringFamily'


class LogixRoutineType(ExtendedEnum):
    rll = 'RLL'


class LogixRungType(ExtendedEnum):
    n = 'N'


class ModulePortType(ExtendedEnum):
    icp = 'ICP'
    ethernet = 'Ethernet'
    point_io = 'PointIO'
    rhino_bp = 'RhinoBP'


class TaskType(ExtendedEnum):
    continuous = 'CONTINUOUS'
    periodic = 'PERIODIC'


class TagUsage(ExtendedEnum):
    public = 'Public'
    input = 'Input'
    output = 'Output'
    inout = 'InOut'


class DescriptionPropertyIdentifier(ExtendedEnum):
    none = 'N/A'
    add_on_instruction = '@AOI'
    controller = '@CONTROLLER'
    datatype = '@DATATYPE'
    info = '@INFO'
    module = '@MODULE'
    program = '@PROGRAM'
    routine = '@ROUTINE'
    rung = '@RUNG'
    tag = '@TAG'
    task = '@TASK'
    todo = '@TODO'
    udt = '@UDT'
