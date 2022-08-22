from dataclasses import dataclass
from VCD_Parser import VCD_Parser 
from utils import Section, VCD_Type 

import re
import multiprocessing as mp

from _Var        import _Var   as Var
from _Scope      import _Scope as Scope
from typing      import Tuple, List, Dict

class EVCD_Parser(VCD_Parser):

    def __init__(self, vcd_filename : str, sig_file : str = None):
        super().__init__(vcd_filename, VCD_Type.Extended,  sig_file = sig_file)

    def find_all_signal_values(self, signal_name: str) -> List[str]: 

        retvals = list()

        extract_value = lambda section, signal_size, index : section[index - 3*signal_size : index - 2*signal_size]

        value_change = '\n'.join(self.raw_sections[Section.Value_Change])
        timestamp_regex = r"\#[0-9]+\n"
   
        signal = self.get_signal(signal_name)
        signal_id = signal.get_id()
        signal_size = signal.get_size()

        # can also be done with re.finditer
        sections = [
            re.sub(r"\s+", r"", section,flags= re.DOTALL | re.MULTILINE)  \
            for section in re.split(timestamp_regex, value_change, maxsplit=0, flags=re.DOTALL|re.MULTILINE)
        ]
     
        previous_value = None 

        for n, section in enumerate(sections): 
            
            if not section: continue 

            in_section = section.find(signal_id)

            # For both VCDs that have either #0...$dumpvars or $dumpvars...$end...#0
            if n == 1 and (not sections[n-1]) or \
               n == 0 and sections[n]: 

                # that's the $dumpvars section i.e., initial value
                previous_value = extract_value(section, signal_size, in_section)
                
  
            if in_section == -1:
                # signal's value didn't change in current section 
                retvals.append(previous_value)
                continue
            
            # search for multiple signal changes occuring in the section
            while(in_section != -1):

                previous_value = extract_value(section, signal_size, in_section)
                retvals.append(extract_value(section, signal_size, in_section))

                in_section = section.find(signal_id, in_section + 1)

        return retvals 

    def find_signal_values_at(self, start : int, end : int, signal_name : str) -> List[str]:
        raise NotImplementedError("Soon...")


def main():

    """
    Do stuff here
    """

if __name__ == "__main__":
    main()