#!/usr/bin/python3

import re
import multiprocessing as mp

from utils import Section

from treelib     import Tree 
from enum        import Enum 
from os          import cpu_count
from os.path     import isfile, dirname, join
from _Var        import _Var   as Var
from _Scope      import _Scope as Scope
from collections import namedtuple
from typing      import Tuple, List, Dict


__VAR_REGEXP__    = "^\$var\s+([a-z]+)\s+([0-9]+)\s+(.*)\s+([a-zA-Z0-9_]+)\s+\$end"
__SCOPE_REGEXP__  = "^\$scope\s+(.*)\s+(.*)\s+\$end"

class VCD_Parser():

    def __init__(self, vcd_filename : str, sig_file : str = None, mode : str = "standard") -> None:

        def _sanitize_file( _file : str):
            
            if not _file : return None

            is_absolute = _file[0] == '/'
            if is_absolute and isfile(_file):       
                return _file
            elif not is_absolute and isfile(_file): 
                return join(dirname(__file__),_file) 
            else: 
                exit(f"File {_file} not found")

        self.vcd_filename = _sanitize_file(vcd_filename)
        self.sig_file     = _sanitize_file(sig_file)    
        self.mode         = mode 
        self.raw_sections  = { sec : list() for sec in [Section.Header, Section.Variable_Definition, Section.Value_Change]}
        self.tree          = Tree()
        self.tree_metadata = dict() # node_names : node_ids
    
    def fill_VCD_sections(self) -> None:
       
        """
        Parses the requested VCD file and fills in raw (str)
        format the object's dictionary and generates a Tree data structure.
        """
        with open(self.vcd_filename) as VCDFILE:
            
            # VCD HEADER # 
            current_section = Section.Header
            line = VCDFILE.readline()
            while line:  

                if current_section == Section.Header and "$scope" in line: 
                    current_section = Section.Variable_Definition
                    self.raw_sections[current_section].append(line.rstrip())
                    line = VCDFILE.readline()
                    continue
                          
                elif current_section == Section.Variable_Definition and "$enddefinitions" in line:
                    self.raw_sections[current_section].append(line.rstrip())
                    current_section = Section.Value_Change
                    line = VCDFILE.readline()
                    continue
              
                self.raw_sections[current_section].append(line.rstrip())

                line = VCDFILE.readline()

    def get_signal(self, signal) -> Var:

        hierarchy = signal.split('/')
        port      = hierarchy[-1]

        # Search tree to acquire the leaf's (signal) parental node i.e., nesting cell
        subtree = None 
        for module in hierarchy[:-1]:

            _tree_id = self.tree_metadata[module]
            subtree = self.tree.subtree(_tree_id)
      
        return subtree.leaves()[0].data.get_var(port)
    
    def find_all_signal_values(self, signal_name: str) -> List[str]:
        
        retvals = list()

        search_space = '\n'.join(self.raw_sections[Section.Value_Change])

        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_ascii_id()
        print(signal_ascii_id)
        input("")
        signal_size = signal.get_var_size()

        # Record every value change of the signal
        found_symbol = search_space.find(signal_ascii_id)
        while(found_symbol != -1):
            
            if search_space[found_symbol+1].isdigit():  # special case for the '#' char only
                found_symbol = search_space.find(signal_ascii_id,found_symbol+1)
                continue;

            retvals.append(search_space[found_symbol-signal_size:found_symbol])

            found_symbol = search_space.find(signal_ascii_id,found_symbol+1)

        return retvals

    def find_signals_values(self, signal_timestamp_map : Dict[str,List[Tuple[int,int]]], proc_num = cpu_count()) -> Dict[str,list]:
        
        #UNDER CONSTRUCTION
        def _compute_chunksize(iterable_size, proc_num : int) -> int:
 
            chunksize, remainder = divmod(iterable_size, 4 * proc_num)
            if remainder:
                chunksize += 1
        
            return chunksize

        def _thread_func(signal, timestamps : List[Tuple[int,int]])->List:
            
            logic_values = list() 
            for start, end in timestamps: 
            
                logic_values.extend(self.find_signal_values_at(start,end,signal))
        
            return logic_values
                
        chunksize = _compute_chunksize(len(signal_timestamp_map.keys()), proc_num)

        # launch a "thread" for each signal
        with mp.Pool(processes=proc_num) as procs: 

            for signal, timestamps in signal_timestamp_map.items():
                
                pass

def main():

    TestObj = VCD_Parser("../misc/wikipedia.vcd", sig_file=None, mode="standard")
    TestObj.parse_VCD()
    TestObj.tree.show()

    #exit(1)
    r = TestObj.find_signal_values_at(0,2302,'logic/tx_en')
    r = TestObj.find_all_signal_values("tb_top_level/uGPGPU/uStreamingMultiProcessor/uPipelineDecode/U1211/A")
    for ret in r: print(ret)  
    
if __name__ == "__main__":
    main()