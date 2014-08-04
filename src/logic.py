class Literal(object) :
    def __init__(self, atom, truth_value) :
        self.atom, self.truth_value = atom, truth_value
        
    def __str__(self) :
        if self.truth_value :
            return str(self.atom)
        else :
            return '-' + str(self.atom)
        
    def toProlog(self):
        if self.truth_value :
            return str(self.atom)
        else :
            return 'not(' + str(self.atom) + ')'
            
    def __repr__(self) :
        return str(self)
            
    def __eq__(self, other) :
        return str(self) == str(other)
        
    def __hash__(self) :
        return hash(str(self))
        
    def __lt__(self, other) :
        return str(self) < str(other)
        
    def __neg__(self) :
        return Literal(self.atom, not self.truth_value)
        
    @classmethod
    def parse(cls, string) :
        if string.startswith('not('):
            return Literal(string[4:-1].strip(),False)
        elif string.startswith('not'):
            return Literal(string[3:].strip(),False)
        elif string.startswith('\+'):
            return Literal(string[2:].strip(),False)
        elif string[0] == '-' :
            return Literal(string[1:], False)
        else :
            return Literal(string, True)
        
class LogicProgram(object):
    def __init__(self):
        self.__rules = {}
    
    def add_rule(self, head, body):
        bodies = self[head]
        new_body = set([])
        for lit in body:
            if self[lit] != [[]]:
                new_body.add(lit)
        if new_body:
            bodies.append(new_body)
            self.__rules[head] = bodies
        else:
            self.__rules[head] = [[]]
            for head in self.__rules:
                for body in self.__rules[head]:
                    if head in body:
                        body.remove(head)
                if [] in self.__rules[head]:
                    self.__rules[head] = [[]]
     
    def __getitem__(self,key):
        return self.__rules.get(key,[])
    
    def __contains__(self, key) :
        return key in self.__rules
    
    def __str__(self):
        result = ''
        for head in self.__rules:
            for body in self.__rules[head]:
                result += head.toProlog()
                if body:
                    result += ':-'
                    for lit in body:
                        result += lit.toProlog() + ','
                    result = result[:-1]
                result += '.\n'
        return result
    
    def __len__(self):
        return len(self.__rules)
    
    def __iter__(self) :
        for head in self.__rules:
            yield head
    
class Node(object):
    def __init__(self, value, children = [], parents = []):
        self.value = value
        self.__children = set([])
        for child in children:
            self.add_child(child)
        self.__parents = set([])
        for parent in parents:
            self.add_parent(parent)
        
    def add_child(self, child):
        child.__parents.add(self)
        self.__children.add(child)
            
    def remove_child(self, child):
        if child in self.__children:
            self.__children.remove(child)
            child.__parents.remove(self)
        else:
            raise LogicException("This child is not present in this node")
        
    def has_child(self, child):
        return child in self.__children
            
    def children(self):
        for child in self.__children:
            yield child
        
    def add_parent(self, parent):
        self.__parents.add(parent)
        parent.__children.add(self)
    
    def remove_parent(self, parent):
        self.__parents.remove(parent)
        parent.__children.remove(self)
        
    def has_parent(self, parent):
        return parent in self.__parents
    
    def parents(self):
        for parent in self.__parents:
            yield parent
            
    def variables(self):
        variables = set([])
        for child in self.__children:
            variables = variables | child.variables()
        return variables
        
class Leaf(Node):
    def __init__(self,value,parents=[]):
        super(Leaf,self).__init__(value,[],parents)
        
    def add_child(self, child):
        raise LogicException("Leafs can't have children")
    
    def __str__(self):
        return str(self.value)
    
    def variables(self):
        if self.value.truth_value:
            return set([self.value])
        else:
            return set([-self.value])

class Negation(Node):
    def __init__(self, children, parents = []):
        if len(children) > 1:
            raise LogicException("Negations can't have more than 1 child")
        else:
            super(Negation,self).__init__(None,children,parents)
            
            
    def add_child(self, child):
        if len(self.children) == 1:
            raise LogicException("Negations can't have more than 1 child")
        else:
            super(Negation, self).add_child(self,child)
    
    def __str__(self):
        result = '-('
        for child in self.children():
            result += str(child)
        result += ')'
        return result
        
class Conjunction(Node):
    def __init__(self, children = [], parents = []):
        super(Conjunction, self).__init__(None, children, parents)
        
    def __str__(self):
        if len(list(self.children())) > 1:
            result = '('
            for child in self.children():
                result += str(child) + ','
            result = result[:-1] + ')'
        else:
            result = str(list(self.children())[0])
        return result
        
class Disjunction(Node):
    def __init__(self, children = [], parents = []):
        super(Disjunction, self).__init__(None, children, parents)
        
    def __str__(self):
        if len(list(self.children())) > 1:
            result = '('
            for child in self.children():
                result += str(child) + ';'
            result = result[:-1] + ')'
        else:
            result = str(list(self.children())[0])
        return result
    
class CNF(Conjunction):
    def __init__(self, children = []):
        super(CNF, self).__init__(children, [])
        
    def add_child(self,child):
        if not child.type  == Disjunction:
            raise LogicException("You can only add disjunctions to a CNF")
        for grandchild in child.children():
            if not grandchild.type == Leaf:
                raise LogicException("The children of the disjunction can only contain leafs")
        super(CNF, self).add_child
    
    def toDimacs(self):
        result = 'p cnf ' + str(len(list(self.variables()))) + ' ' + str(len(list(self.children()))) + '\n'
        for child in self.children():
            for grandchild in child.children():
                result += str(grandchild) + ' '
            result += '0\n'
        return result
    
    @classmethod
    def readFromDimacs(cls, filename) :
        with open(filename) as file:
            leafs = {}
            cnf = CNF()
            for line in file:
                if not line.startswith('p'):
                    clause = Disjunction([],[cnf])
                    literals = line.split()[:-1]
                    for lit in literals:
                        if not lit in leafs:
                            leafs[lit] = Leaf(Literal.parse(lit),[])
                        clause.add_child(leafs[lit])
        return cnf
                    
class LogicException(Exception):
    def __init__(self,msg):
        self.__msg = msg
        
    def __str__(self):
        return 'error in logic representation' + self.__msg