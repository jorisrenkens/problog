from logic import Literal

class Weights:
    def __init__(self):
        self.__weights = {}
        
    def __getitem__(self,key):
        if key not in self.__weights:
            raise Exception('no weight for: ' + str(key))
        else:
            return self.__weights[key]
        
    def __setitem__(self,key,value):
        self.__weights[key] = value
        
    def __str__(self):
        result = ''
        for lit in self.__weights:
            if lit.truth_value:
                result += str(lit) + ' ' + str(self.__weights[lit]) + ' ' + str(self.__weights[-lit]) + '\n'
        return result

    def __contains__(self, key) :
        return key in self.__weights
    
    @classmethod
    def readFromFile(cls, filename) :
        with open(filename) as file:
            weights = Weights()
            for line in file:
                parts = line.split()
                lit = Literal.parse(parts[0])
                weights[lit] = float(parts[1])
                weights[-lit] = float(parts[2])
                
        
        
            
        
        
        
    