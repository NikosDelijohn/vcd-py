class _Var():
	#$var wire 1 7* D $end
	def __init__(self, var_type : str, size : str, ascii_id : str, var_name : str ):

		self.var_type  = var_type
		self.var_size  = int(size) #bit len
		self._ascii_id  = ascii_id  #from ! to ~
		self._var_name  = var_name  #in the netlist

	def __repr__(self) -> str:
		return f"_Var(id={self._ascii_id},name={self._var_name},type={self.var_type},size={self.var_size})"

	def __str__(self) -> str:
		return self.__repr__()

	def get_ascii_id(self) -> str: 
		return self._ascii_id

	def get_var_size(self) -> int: 
		return self.var_size