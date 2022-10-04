class VarTypeUnknown(BaseException): 
	"""Exception that can be triggered during parsing the VCD file during the Variable Definition section reading.
	The variable type is unknown. Potential syntax error on the VCD file.
	"""
	def __init__(self, message):            
		# Call the base class constructor with the parameters it needs
		super().__init__(message)
		print(f"Check the Variable Definition section of the VCD file for syntax error(s)!")

class _Var():

	"""Class representing a VCD/eVCD `$var` type.  

	### Instance Attributes
	1. var_type : str 
		- The `$var` type field (e.g., `wire`)
	2. size : str
		- The bit length of the `$var`.
		- This field is the only thing that diferentiates the eVCD syntax from the SVCD syntax for `$var`.
	3. id : str
		- Identifier assigned to the `$var` 
	4. var_name : str 
		- Wire name of the represented by the `$var`

	### Methods
	- get_id() : str 
		- Returns the `id` attribute of the object
	- get_size() : str
		- Returns the `size` attribute of the object
	- get_reference() : str 
		- Returns the `var_name` attribute of the object 

	### Notes 
	The class supports both types of VCD `$var` types. It distinguishes between the two
	by inspecting the way the `size` attribute is defined.   

    """

	def __init__(self, var_type : str, size : str, id : str, var_name : str):
		"""Constructor

		### Parameters
		1. var_type : str 
			- The `$var` type field (e.g., `wire`).
		2. size : str
			- The bit length of the `$var`.
			- This field is the only thing that diferentiates the eVCD syntax from the SVCD syntax for `$var`.
		3. id : str
			- Identifier assigned to the `$var`.
		4. var_name : str 
			- Wire name of the represented by the `$var`.

		### Returns 
		`_Var` object instance.

		Raises
		------ 
		- VarTypeUnknown
			- The Constructor is unable to understand the type of the VCD variable. The `size` is in a wrong syntax.
		"""
		self.var_type = var_type 
		self.id = id  
		self.reference = var_name  

		if size.isdigit() :
			# standard vcd $var 
			self.size = int(size) 
		elif ":" in size: 
			# extended vcd $var
			msb,lsb = map(int,size.strip('[]').split(':'))
			self.size = (msb - lsb) + 1
		else: 
			raise VarTypeUnknown(f"Size attribute ({size}) is given in the wrong format for $var \"{var_name}\" ") 

	def __repr__(self) -> str:
		"""String representation for the _Var object 
		
		### Parameters 
		- None
		
		### Returns 
		- str
		"""
		return f"_Var(id={self.id},name={self.reference},type={self.var_type},size={self.size})"

	def __str__(self) -> str:
		"""To string for _Var object
		
		### Parameters 
		- None
		
		### Returns 
		- str		
		"""
		return self.__repr__()

	def get_id(self) -> str: 
		"""Getter method for the `id` attribute 

		### Parameters 
		- None
		
		### Returns 
		- str	
		"""
		return self.id

	def get_size(self) -> int: 
		"""Getter method for the `size` attribute 

		### Parameters 
		- None
		
		### Returns 
		- str	
		"""
		return self.size
	
	def get_reference(self) -> str:
		"""Getter method for the `reference` attribute 

		### Parameters 
		- None
		
		### Returns 
		- str	
		"""	
		return self.reference