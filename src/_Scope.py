from _Var import _Var as Var

class _Scope():

	def __init__(self,  scope_type : str, cell_name : str):
	
		self.scope_type = scope_type
		self.cell_name  = cell_name
		self.vars      	= dict()
		self.scopes    	= list()

	def __repr__(self) -> str:
		return f"<{self.cell_name}, {len(self.vars.items())} wires, {len(self.scopes)} modules>"

	def __str__(self) ->str:
		return self.__repr__()

	def append_var(self, vcd_variable : Var) -> None:
		self.vars[vcd_variable._var_name] = vcd_variable

	def append_scope(self, scope) -> None:
		self.scopes.append(scope)

	def get_var(self,variable_name : str) -> str:
		return self.vars[variable_name]