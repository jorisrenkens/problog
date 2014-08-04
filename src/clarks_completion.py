from utils import KeyIndexDict
from logic import Leaf, Disjunction, Literal, CNF
from weights import Weights

class ClarksCompletion(object):
    def __call__(self,logic_program,weights,literals):
        self.__logic_program = logic_program
        self.__weights = weights
        self.__new_weights = Weights()
        self.__translation = KeyIndexDict()
        self.__done = []
        self.__leafs = {}
        self.__completion = CNF()
        for lit in literals:
            self.__get_completion(lit)
        return self.__completion, self.__translation, self.__new_weights
            
    def __get_completion(self,lit):
        if not lit.truth_value:
            lit = -lit
        if not lit in self.__done:
            self.__done.append(lit)
            rules = self.__logic_program[lit]
            if len(rules) == 0:
                pass
            elif len(rules) == 1:
                big_clause = Disjunction([self.__get_leaf(lit)],[self.__completion])
                for atom in rules[0]:
                    self.__get_completion(atom)
                    big_clause.add_child(self.__get_leaf(-atom))
                    Disjunction([self.__get_leaf(-lit),self.__get_leaf(atom)],[self.__completion])
            else:
                big_disjunction = Disjunction([self.__get_leaf(-lit)],[self.__completion])
                for i in range(0,len(rules)):
                    new_lit = Literal(lit.atom + '_' + str(i),True)
                    big_disjunction.add_child(self.__get_leaf(new_lit))
                    Disjunction([self.__get_leaf(lit),self.__get_leaf(-new_lit)],[self.__completion])
                    big_conjunction = Disjunction([self.__get_leaf(new_lit)],[self.__completion])
                    for rule_lit in rules[i]:
                        self.__get_completion(rule_lit)
                        big_conjunction.add_child(self.__get_leaf(-rule_lit))
                        Disjunction([self.__get_leaf(-new_lit),self.__get_leaf(rule_lit)],[self.__completion])
                        
    def __get_leaf(self,lit):
        if not lit in self.__leafs:
            if lit.truth_value:
                if lit in self.__translation:
                    index = Literal(self.__translation[lit],True)
                else:
                    index =  Literal(self.__translation.add(lit),True)
            else:
                if lit in self.__translation:
                    index = Literal(self.__translation[-lit],False)
                else:
                    index =  Literal(self.__translation.add(-lit),False)
            self.__leafs[lit] = Leaf(index,[])
            if lit in self.__weights:
                self.__new_weights[index] = self.__weights[lit]
                self.__new_weights[-index] = self.__weights[-lit]
            else:
                self.__new_weights[index] = 1
                self.__new_weights[-index] = 1
        return self.__leafs[lit]