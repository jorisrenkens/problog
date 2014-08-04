from logic import LogicProgram,Literal
from weights import Weights

class LoopBreaker:
    def __call__(self,logic_program,weights,queries,evidence):
        self.__original_program = logic_program
        self.__original_weights = weights
        self.__new_program = LogicProgram()
        self.__new_weights = Weights()
        self.__built_rules = {}
        for lit in queries | evidence:
            self.__get_rule(lit)
        new_evidence = set([])
        for lit in evidence:
            if lit.truth_value:
                for (new_lit,_) in self.__built_rules[lit]:
                    new_evidence.add(new_lit)
            else:
                for (new_lit,_) in self.__built_rules[-lit]:
                    new_evidence.add(-new_lit)
        return self.__new_program, self.__new_weights, new_evidence 
        
    def  __get_rule(self,lit,ancestors=set([])):
        if lit.truth_value:
            atom = lit
        else:
            atom = -lit
            ancestors = set([])
        for (new_atom,cycles) in self.__built_rules.get(atom,[]):
            if cycles <= ancestors:
                break
        else:
            (new_atom,cycles) = self.__build_rule(atom,ancestors)
        if lit.truth_value:
            return (new_atom,cycles)
        else:
            return (-new_atom,cycles)
        
        
    def __build_rule(self,atom,ancestors):
        if atom in self.__original_program:
            all_new_rules = []
            all_new_cycles = set([])
            for rule in self.__original_program[atom]:
                if not rule & ancestors:
                    new_cycles = set([])
                    new_rule = set([])
                    for lit in rule:
                        (new_lit,cycles) = self.__get_rule(lit,ancestors | set([atom]))
                        if new_lit:
                            new_cycles = new_cycles | cycles
                            new_rule.add(new_lit)
                        else:
                            new_cycles = cycles
                            break
                    else:
                        all_new_rules.append(new_rule)
                        all_new_cycles = all_new_cycles | new_cycles
                else:
                    all_new_cycles = all_new_cycles | (rule & ancestors)
            all_new_cycles = all_new_cycles - set([atom])
            if all_new_rules:
                if all_new_cycles:
                    new_atom = Literal(atom.atom + '_' + str(len(self.__built_rules.get(atom,[]))),True)
                else:
                    new_atom = atom
                self.__new_weights[new_atom] = self.__original_weights[atom]
                self.__new_weights[-new_atom] = self.__original_weights[-atom]
                for rule in all_new_rules:
                    self.__new_program.add_rule(new_atom, rule)
                result = (new_atom,all_new_cycles)
                if atom in self.__built_rules:
                    self.__built_rules[atom].append(result)
                else:
                    self.__built_rules[atom] = [result] 
                return result
            else:
                return (None,all_new_cycles)
                    
        else:
            self.__new_weights[atom] = self.__original_weights[atom]
            self.__new_weights[-atom] = self.__original_weights[-atom]
            result = (atom,set([]))
            self.__built_rules[atom] = [result]
            return result
            
            
            
        
        