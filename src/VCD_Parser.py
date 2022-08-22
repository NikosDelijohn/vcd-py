#!/usr/bin/python3

import re
import time
import multiprocessing as mp

from utils import *

from tqdm    import tqdm 
from treelib import Tree, Node
from os      import cpu_count
from os.path import isfile, dirname, join
from _Var    import _Var   as Var
from _Scope  import _Scope as Scope
from typing  import Tuple, List, Dict

class VCD_Parser():

    def __init__(self, vcd_filename : str, file_type : VCD_Type, sig_file : str = None) -> None:

        def _fill_VCD_sections() -> None:
        
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

        def _generate_tree(type : VCD_Type) -> None:
            
            def id_generator():
                n = 0 
                while True:
                    yield n 
                    n += 1
            
            seq = id_generator()

            node_id = next(seq)

            s_regex  = re.compile(SCOPE_REGEXP)
            v_regex  = re.compile(S_VAR_REGEXP) if type == VCD_Type.Standard else re.compile(E_VAR_REGEXP) 

            current_cell   = None
            predecessor_ids = list() 

            for raw_str in self.raw_sections[Section.Variable_Definition]:           

                is_scope = re.match(s_regex, raw_str)
                is_var   = re.match(v_regex, raw_str)

                if is_scope:

                    scope = Scope(*is_scope.groups())
                    
                    self.tree_metadata[scope.cell_name] = node_id

                    if self.tree.size() == 0:
                        # this is the root node
                        current_cell = Node(tag = scope.cell_name, identifier = node_id, data = scope)
                        self.tree.add_node(current_cell)
                    # current_cell = self.tree.get_node(node_id)  
                        predecessor_ids.append(node_id) 

                    else:
                        
                        # update the predecessor's nesting modules
                        predecessor = self.tree.get_node(predecessor_ids[-1])
                        predecessor.data.append_scope(scope)
                        self.tree.update_node(nid = predecessor.identifier, data = predecessor.data)

                        # add the new node as a child to the predecessor to the tree
                        current_cell = Node(tag = scope.cell_name, identifier = node_id, data = scope)
                        self.tree.add_node(current_cell, parent=predecessor)
                        predecessor_ids.append(node_id)

                    node_id = next(seq)

                if is_var:

                    # get the current node (scope) and update the wire's list                   
                    var = Var(*is_var.groups())
                    current_cell.data.append_var(var)
                    self.tree.update_node(nid=current_cell.identifier, data=current_cell.data)

                # closing statement for module in VCD syntax
                if "upscope" in raw_str: predecessor_ids.pop()

        def _sanitize_file( _file : str):
            
            if not _file : return None

            is_absolute = _file[0] == '/'
            if is_absolute and isfile(_file):       
                return _file
            elif not is_absolute and isfile(_file): 
                return join(dirname(__file__),_file) 
            else: 
                exit(f"File {_file} not found")

        self.vcd_filename  = _sanitize_file(vcd_filename)
        self.type          = file_type
        self.sig_file      = _sanitize_file(sig_file)    
        self.raw_sections  = { sec : list() for sec in [Section.Header, Section.Variable_Definition, Section.Value_Change]}
        self.tree          = Tree()
        self.tree_metadata = dict() # node_names : node_ids
        self.signals       = [line.rstrip() for line in open(self.sig_file).readlines()] if sig_file else list()

        _fill_VCD_sections()
        _generate_tree(file_type)
   
    def get_signal(self, signal) -> Var:

        hierarchy = signal.split('/')
        port      = hierarchy[-1]

        # Search tree to acquire the leaf's (signal) parental node i.e., nesting cell
        subtree = None 
        for module in hierarchy[:-1]:
            _tree_id = self.tree_metadata[module]
            subtree = self.tree.get_node(_tree_id)

        return subtree.data.get_var(port)
  