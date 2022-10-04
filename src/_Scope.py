from _Var import _Var as Var
from typing import List, Dict 

class ScopeHasNoVar(BaseException): 
	"""Exception that can be triggered by any of the `find` methods of the tool. 
	This indicates either an error on the naming convention that the user has used
	i.e., a missmatch with the VCD names OR that the hierarhy search mechanism is wrong. 
	See VCD_Parser's `get_signal`.
	"""
	def __init__(self, message):            
		super().__init__(message)
		
class _Scope():

	"""Class representing a VCD/eVCD `$scope` module. 

	### Attributes
	1. scope_type : str 
		- The `$scope` type field (e.g., begin, module).
	2. cell_name : str
		- The `$scope` cell name.
	3. vars : Dict[ _Var.var_name : _Var ]
		- A hashmap with all the `$var`s that belong to the `$scope`.
	4. scopes : List[ _Scope ] 
		- A list with all the nested `$scopes` of the current `$scope`.

	### Methods
	- append_var(vcd_variable : _Var) : None 
		- Adds the <k,v>:=<variable_name,_Var> to the `vars` hashmap of the `$scope` object.
	- append_scope( other : _Scope) : None
		- Appends a nested `$scope` to the current's `$scope` list of nested `$scopes`.
	- get_var(variable_name : str) : str 
		- Returns a reference to a `_Var` object assosciated with `variable_name`. 
		- Raises `ScopeHasNoVar` exception if `$var` is not found in the current `$scope`.
    """

	def __init__(self,  scope_type : str, cell_name : str):
		"""Constructor

		### Parameters
		1. scope_type : str 
			- The `$scope` type field (e.g., `begin`, `module`).
		2. cell_name : str
			- The `$scope` cell name.
		### Returns 
		`_Scope` object instance.
		"""

		self.scope_type = scope_type
		self.cell_name  = cell_name
		self.vars      	= Dict[str, Var]
		self.scopes    	= List["_Scope"]

	def __repr__(self) -> str:
		"""String representation for the _Scope object instance 
		
		### Parameters 
		- None
		
		### Returns 
		- str
		"""
		return f"_Scope(cell_name={self.cell_name}, #wires={len(self.vars.items())}, #modules={len(self.scopes)})"

	def __str__(self) -> str:
		"""To string for _Scope object
		
		### Parameters 
		- None
		
		### Returns 
		- str		
		"""
		return self.__repr__()

	def append_var(self, vcd_variable : Var) -> None:
		"""Appends a `_Var` object to the `vars` dictionary of the `$scope`.

		### Parameters 
		1. vcd_variable : _Var 
		
		### Returns 
		- None
		"""
		self.vars[vcd_variable.get_reference()] = vcd_variable

	def append_scope(self, other : "_Scope") -> None:
		"""Appends a `_Scope` object to the `scopes` list of the `$scope`.
		
		### Parameters 
		1. other : _Scope 
		
		### Returns 
		- None
		"""
		self.scopes.append(other)

	def get_var(self, variable_name : str) -> str:
		"""Searches in the `vars` dictionary for a `_Var` that belongs to the `$scope` and returns it (if found).

		### Parameters
		1. variable_name : str 
			- The `_Var.var_name` attribute of the `_Var` currently begin searched.

		### Returns 
		`_Var` object reference.

		Raises
		------ 
		- ScopeHasNoVar
			- The `variable_name` does not match any of the names of `$vars` that belong to the current `$scope`. Indicates
		"""
		if variable_name not in self.vars.keys(): 
			scopes_vars_are = ','.join([var.get_reference() for var in self.vars.keys()])
			raise ScopeHasNoVar(f"VCD $var {variable_name} not found in $scope {self}. Variables are:\n {scopes_vars_are}")

		return self.vars[variable_name]