from VCD_Parser import VCD_Parser 
from utils import *

import time 
import re
import multiprocessing as mp

from os     import cpu_count
from _Var   import _Var   as Var
from _Scope import _Scope as Scope
from typing import Tuple, List, Dict
from tqdm import tqdm
from itertools import repeat

@singleton
class SVCD_Parser(VCD_Parser):


    def __init__(self,vcd_filename : str, sig_file : str = None):
        super().__init__(vcd_filename, VCD_Type.Standard, sig_file = sig_file)
        


    def find_all_signal_values(self, signal_name: str) -> List[str]:

        retvals = list()

        value_change = '\n'.join(self.raw_sections[Section.Value_Change])
        timestamp_regex = r"\#[0-9]+\n" 

        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_id()
        signal_size = signal.get_size()

        # can also be done with re.finditer
        sections = re.split(timestamp_regex, value_change, maxsplit=0, flags=re.DOTALL|re.MULTILINE)
    
        previous_value = None 

        for n, section in enumerate(sections): 
           
            if not section: continue 

            in_section = section.find(signal_ascii_id)

            # For both VCDs that have either #0...$dumpvars or $dumpvars...$end...#0
            if n == 1 and (not sections[n-1]) or \
               n == 0 and sections[n]: 

                # that's the $dumpvars section i.e., initial value
                previous_value = section[in_section-signal_size:in_section]
            
            if in_section == -1:
                # signal's value didn't change in current section 
                retvals.append(previous_value)
                continue
            
            # search for multiple signal changes occuring in the section
            while(in_section != -1):
                
                if in_section + 1 < len(section) and \
                (section[in_section + 1] == 'd'   or  # symbol == '$' && the $dumpvars line  
                 section[in_section + 1] == 'e'   or  # symbol == '$' && the $end line      
                 section[in_section + 1].isdigit()) : # symbol == '#' && the #[0-9]+ timestamp

                    in_section = section.find(signal_ascii_id,in_section + 1)
                    continue

                previous_value = section[in_section-signal_size:in_section]
                retvals.append(section[in_section-signal_size:in_section])
                in_section = section.find(signal_ascii_id, in_section + 1)

        return retvals 

    def find_signal_values_at_region(self, start : int, end : int, signal_name : str) -> List[str]:
      
        retvals = list()

        search_space = '\n'.join(self.raw_sections[Section.Value_Change])
                
        search_regex = f"#{start}(.*)^#{end}"

        # Extract the ]start,end[ segment
        regex_results = re.search(search_regex, search_space, flags=re.DOTALL|re.MULTILINE)

        if not regex_results: 
            raise ValueError("Provided timestamp(s) do not exist in the VCD file.")

        section = regex_results[1]

        # Find the signal attributes in the Tree.
        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_id()
        signal_size = signal.get_size()

        # Record every value change of the signal
        in_section = section.find(signal_ascii_id)

        while(in_section != -1):
            
            if in_section + 1 < len(section) and \
            (section[in_section + 1] == 'd'   or  # symbol == '$' && the $dumpvars line  
             section[in_section + 1] == 'e'   or  # symbol == '$' && the $end line      
             section[in_section + 1].isdigit()) : # symbol == '#' && the #[0-9]+ timestamp

                in_section = section.find(signal_ascii_id,in_section + 1)
                continue

            retvals.append(section[in_section-signal_size:in_section])

            in_section = section.find(signal_ascii_id,in_section+1)

        return retvals

    def find_signal_values_at(self, at : int, signal_name: str)  -> str: 

        timestamps = [ ts for ts in self.value_change.keys() ]

        if at not in timestamps: 
            raise KeyError(f"Timestamp {at} is not present in the VCD")

        search_space = [ ts for ts in timestamps[timestamps.index(at)::-1] ]

        # Find the signal attributes in the Tree.
        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_id()

        for ts in search_space: 

            for id, val in self.value_change[ts]: 

                if signal_ascii_id == id : return val 
        
        raise RuntimeError(f"Signal {signal_name} : {signal} has never been assigned a value up until the region {at} you are currently searching")

    def find_signal_initial_value(self, signal_name : str, search_space : str = None) -> str: 
        
        search_space = '\n'.join(self.raw_sections[Section.Value_Change]) if not search_space else search_space

        # Find the signal attributes in the Tree.

        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_id()
        signal_size = signal.get_size()

        found_symbol = search_space.find(signal_ascii_id)
        
        if found_symbol == -1: 
            exit(f"Signal {signal_name} with id: {signal_ascii_id} not found in the VCD file")
        
        logic_value = search_space[found_symbol-signal_size:found_symbol]
        while logic_value not in ["1","0"]:

            found_symbol = search_space.find(signal_ascii_id,found_symbol+1)
            logic_value = search_space[found_symbol-signal_size:found_symbol]

        return logic_value
   
    def _thread_func(self, values : Tuple[str,int,int])->List:
        
        raise NotImplemented("Soon...")
        signal, start, end = values 
        logic_values = (start,end,signal)

        return signal, logic_values

    def find_signals_values_at_region(self, signals : List[str], start : int, end : int, proc_num : int = mp.cpu_count()) -> Dict[str,str]:

        retval = dict()

        chunksize, remainder = divmod(len(signals), 4 * proc_num)

        if remainder: 
            chunksize += 1

        with mp.Pool(processes = proc_num) as pool: 

            for signal, values in pool.imap_unordered(self._thread_func, zip(signals,repeat(start),repeat(end)), chunksize=chunksize):
                
                retval[signal] = values 
        
        return retval
    
    def find_signals_initial_values(self, signals : List[str], proc_num : int = mp.cpu_count()) -> Dict[str,str]:
        
        retval = dict()

        values = list()

        chunksize, remainder = divmod(len(signals), proc_num)

        if remainder: 
            chunksize += 1

        with mp.Pool(processes = proc_num) as pool:

            for value in pool.imap(self.find_signal_initial_value, tqdm(signals), chunksize=chunksize):
                
                values.append(value) 

        retval = { signal : value for signal, value in zip(signals,values) }
        return retval 
        
def main():

    """
    Do stuff here
    """
    Test_SVCD = SVCD_Parser(vcd_filename="../misc/riscy_tb2.vcd", sig_file="../misc/si_ri5cy.txt")
    Test_SVCD2 = SVCD_Parser("../misc/riscy_tb.vcd", sig_file="../misc/si_ri5cy.txt")

    print(Test_SVCD.vcd_filename)
    print(Test_SVCD2.vcd_filename)
    exit(0)
    #Test_SVCD.get_signal("riscv_core_i/if_stage_i/prefetch_128_prefetch_buffer_i/L0_buffer_i/addr_q_reg_1_/Qf")

    init_state = list()
    for si in tqdm(Test_SVCD.signals): 

        # latch
        if "/enabled" in si :
            init_state.append('X')
            continue

        init_state.append(Test_SVCD.find_signal_values_at(220_000, si))

    for logic_value in init_state: 

        print(logic_value,end="")

if __name__ == "__main__":

    main()