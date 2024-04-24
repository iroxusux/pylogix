#!/usr/bin/env python

""" instruction
    derived from cla_logix_object
    this class represents an Allen Bradley Instruction
    """


class Instruction(object):
    """ logix instruction
        """

    def __init__(self, mnemonic: str, src_a: str, src_b: str = None, dest: str = None):
        """ initialize this class
            :param mnemonic: mnemonic device used to print out logic (e.g., XIC)
            :param src_a: logical source 'a' used in components (e.g., MyTag)
            :param src_b: [optional] logical source 'b' used in components (e.g., MySecondTag)
            :param dest: [optional] logical destination used in components (e.g., MyDestinationTag)
            :return: object that contains information about an instruction in logic
            """
        self.mnemonic = mnemonic
        self.src_a = src_a
        self.src_b = src_b
        self.dest = dest

    def to_neutral_text(self) -> str:
        """ get neutral text output describing this instruction
            :return: a string of neutral text (e.g., XIC(MyTag,MySecondTag,MyDestinationTag)
            """
        src_text = self.src_a
        if self.src_b:
            src_text += f',{self.src_b}'
        if self.dest:
            src_text += f',{self.dest}'

        return f'{self.mnemonic}({src_text})'