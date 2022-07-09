#!/usr/bin/python3

import re
import multiprocessing as mp

from pyrsistent import l

from treelib     import Tree 
from enum        import Enum 
from os          import cpu_count
from os.path     import isfile, dirname, join
from _Var        import _Var   as Var
from _Scope      import _Scope as Scope
from collections import namedtuple
from typing      import Tuple, List, Dict

#########################################
#               UTILITIES               #
#########################################

class Section(Enum):
    Header = 0
    Variable_Definition = 1 
    Value_Change = 2

class Logic(Enum):
    ZERO = 0
    ONE  = 1
    X    = 2

__VAR_REGEXP__    = "^\$var\s+([a-z]+)\s+([0-9]+)\s+(.*)\s+([a-zA-Z0-9_]+)\s+\$end"
__SCOPE_REGEXP__  = "^\$scope\s+(.*)\s+(.*)\s+\$end"

class VCD_Parser():

    def __init__(self, vcd_filename : str, sig_file : str = None) -> None:

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
        self.raw_sections  = { sec : list() for sec in [Section.Header, Section.Variable_Definition, Section.Value_Change]}
        self.tree          = Tree()
        self.tree_metadata = dict() # node_names : node_ids
    
    def parse_VCD(self) -> None:
       
        """
        Parses the requested VCD file and fills in raw (str)
        format the object's dictionary and generates a Tree data structure.
        """

        def _generate_scope_tree() -> None:
         
            """
            Generates a Tree data structure where every node is a $scope 
            and holds as data nested $scopes and $vars
            """

            nesting_level = 0
            node_id  = 0

            s_regex = re.compile(__SCOPE_REGEXP__)
            v_regex = re.compile(__VAR_REGEXP__)

            current_cell = None

            for raw_str in self.raw_sections[Section.Variable_Definition]:           

                is_scope = re.match(s_regex,raw_str)
                is_var   = re.match(v_regex,raw_str)

                if is_scope:

                    scope = Scope(*is_scope.groups())
                    
                    self.tree_metadata[scope.cell_name] = node_id

                    if nesting_level == 0:
                        # this is the root node
                        self.tree.create_node(tag=scope.cell_name, identifier=node_id, data=scope)
                        current_cell = self.tree.get_node(node_id)

                    else:
                        
                        # update the predecessor's nesting modules
                        predecessor = self.tree.get_node(nesting_level-1)
                        predecessor.data.append_scope(scope)
                        self.tree.update_node(nid=predecessor.identifier, data=predecessor.data)
                        # add the new node as a child to the previous one
                        self.tree.create_node(tag=scope.cell_name, identifier=node_id, data=scope, parent=nesting_level-1)
                        current_cell = self.tree.get_node(node_id)

                    nesting_level += 1
                    node_id       += 1

                if is_var:
                    # get the current node (module) and update the wire's list
                    var = Var(*is_var.groups())
                    current_cell.data.append_var(var)
                    self.tree.update_node(nid=current_cell.identifier,data=current_cell.data)

                # closing statement for module in VCD syntax
                if "upscope" in raw_str: nesting_level -= 1


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

        _generate_scope_tree()

    def get_signal(self, signal : str, escape = False) -> Var:

        # CAREFUL ESCAPE " CHAR IN ASCII IDS (maybe?)
        hierarchy = signal.split('/')
        port      = hierarchy[-1]
        
        # Search tree to acquire the leaf's (signal) parental node i.e., nesting cell
        subtree = None 
        for module in hierarchy[:1]:
            
            _tree_id = self.tree_metadata[module]
            subtree = self.tree.subtree(_tree_id)

        return subtree.leaves()[0].data.get_var(port)

    def find_signal_values_at(self, start : int, end : int, signal_name : str) -> List[str]:
      
        retvals = list()

        search_space = '\n'.join(self.raw_sections[Section.Value_Change])
        search_regex = f"#{start}(.*)^#{end}"

        # Extract the ]start,end[ segment
        regex_results = re.search(search_regex, search_space, flags=re.DOTALL|re.MULTILINE)

        if not regex_results: 
            raise ValueError("Provided timestamp(s) do not exist in the VCD file.")

        period = regex_results[1]

        # Find the signal attributes in the Tree.
        signal = self.get_signal(signal_name)
        signal_ascii_id = signal.get_ascii_id()
        signal_size = signal.get_var_size()

        # Record every value change of the signal
        found_symbol = period.find(signal_ascii_id)
        while(found_symbol != -1):
            
            if period[found_symbol+1].isdigit(): 
                found_symbol = period.find(signal_ascii_id,found_symbol+1)
                continue;

            retvals.append(period[found_symbol-signal_size:found_symbol])

            found_symbol = period.find(signal_ascii_id,found_symbol+1)

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

    TestObj = VCD_Parser("../misc/wikipedia.vcd", sig_file=None)
    TestObj.parse_VCD()

    r = TestObj.find_signal_values_at(0,2211,'logic/data_valid')
    for ret in r: print(ret)  
 
    TestObj.find_signals_values({"SDT":[(123,123),(126,124)]})

if __name__ == "__main__":
    main()