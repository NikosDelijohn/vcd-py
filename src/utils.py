#########################################
#               UTILITIES               #
#########################################

from enum import Enum, auto

class Section(Enum):
    Header              = auto()
    Variable_Definition = auto()
    Value_Change        = auto()

class eVCD_Strenth_Value(Enum):

    HIGHZ  = 0
    SMALL  = 1
    MEDIUM = 2
    WEAK   = 3 
    LARGE  = 4
    PULL   = 5
    STRONG = 6
    SUPPLY = 7

    def __str__(self):
        return f"{self.value}"

class eVCD_Input_Values(Enum):
    
    D = "0" # low 
    U = "1" # high
    N = "U" # unknown
    Z = "Z" # three-state
    d = "d" # low (two or more drivers active)
    u = "u" # high (two or more drivers active)

    def __str__(self):
        return f"{self.value}"

class eVCD_Output_Values(Enum):
   
    L = "0" # low
    H = "1" # high
    X = "X" # unknown (do-not care)
    T = "T" # three-state
    l = "l" # low (two or more drivers active)
    h = "h" # high (two or more drivers active)

    def __str__(self):
        return f"{self.value}"

class eVCD_Uknown_Direction_Values(Enum):
   
    ZERO = "0" # (both input and output are active with 0 value)"
    ONE = "1"  # (both input and output are active with 1 value)"
    U = "?"    # unknown
    F = "F"    # three-state (input and output unconnected)
    A = "A"    # unknown (input 0 and output 1)
    a = "a"    # unknown (input 0 and output X)
    B = "B"    # unknown (input 1 and output 0)
    b = "b"    # unknown (input 1 and output X)
    C = "C"    # unknown (input X and output 0)
    c = "c"    # unknown (input X and output 1)
    f = "f"    # unknown (input and output three-stated)

    def __str__(self):
        return f"{self.value}"


#$var var_type size < identifier_code reference $end
