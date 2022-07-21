class _Var():
	
	#$var wire 1 7* D $end
	def __init__(self, var_type : str, size : str, id : str, var_name : str):

		self.var_type  = var_type 
		self.id  = id  
		self.reference = var_name  

		if size.isdigit() :
			# standard vcd $var 
			self.size = int(size) 
		elif ":" in size: 
			# extended vcd $var
			msb,lsb = map(int,size.strip('[]').split(':'))
			self.size = (msb - lsb) + 1

	def __repr__(self) -> str:
		return f"_Var(id={self.id},name={self.reference},type={self.var_type},size={self.size})"

	def __str__(self) -> str:
		return self.__repr__()

	def get_id(self) -> str: 
		return self.id

	def get_size(self) -> int: 
		return self.size
	
	def get_reference(self) -> str:
		return self.reference 