import os,subprocess
from utils import Timer, Logger
from logic import Literal, LogicProgram
from weights import Weights

class Grounder(object):
    def __call__(self, infiles, env):
        self.__env = env
        logfile = open(env.tmp_path('grounding.log'),'w')
        logger = Logger(file = logfile,verbose = 1)
        with Timer('grounding',logger) as timer:
            self.__convert_to_lpad(infiles)
            self.__ground_lpad()
            (rules, weights, constraints, queries, evidence) = self.__parse_grounding()
            logger(1,'number defined predicates:',len(rules),msgtype = 'RESULT')
            nr_rules = 0
            for head in rules:
                nr_rules += len(rules[head])
            logger(1,'number rules:',nr_rules,msgtype = 'RESULT')
            logger(1,'number queries:',len(queries),msgtype = 'RESULT')
            logger(1,'number evidence atoms:',len(evidence),msgtype = 'RESULT')
            return (rules, weights, constraints, queries, evidence)
            
    def __convert_to_lpad(self, infiles):
        parser = ProbLogParser()
        if os.path.exists(self.__lpad_path()):
            os.remove(self.__lpad_path())
        parser(infiles,self.__lpad_path())
    
    def __ground_lpad(self):
        main_pred = "catch(main('" + self.__lpad_path() + "','" + self.__ground_lpad_path() + "','" + self.__queries_path() + "','" + self.__evidence_path() + "'),_,halt(1))."
        subprocess.check_call(['yap','-q','-l','grounder.pl','-g',main_pred])
        
    def __parse_grounding(self):
        parser = GroundProbLogParser()
        (rules, weights, constraints,queries, evidence) = parser(self.__ground_lpad_path(), self.__queries_path(), self.__evidence_path())
        return (rules, weights, constraints, queries, evidence)
        
    def __lpad_path(self):
        return self.__env.tmp_path('parsed_input')
    
    def __ground_lpad_path(self):
        return self.__env.tmp_path('grounding')
    
    def __queries_path(self):
        return self.__env.tmp_path('queries')
    
    def __evidence_path(self):
        return self.__env.tmp_path('evidence')

class ProbLogParser:
    def __call__(self, infiles, outfile):
        self.__strings = {}
        rule = ''
        with open(outfile,'w') as out:
            for file in infiles:
                for line in open(file):
                    line = line.strip()
                    if line.startswith(':- '):
                        raise ParseError("lines can't start with :-. Built-in libraries are preloaded for you. Other files can be included by giving multiple input files")
                    if not line.startswith('%'):
                        if '%' in line:
                            line = line.split('%')[0].strip()
                        rule += line
                        if line.endswith('.'):
                            if rule.startswith('query'):
                                out.write(self.__parse_query(rule) + '\n')
                            elif rule.startswith('evidence'):
                                out.write(self.__parse_evidence(rule) + '\n')
                            else:
                                out.write(self.__parse_rule(rule) + '\n')
                            rule = ''
    
    def __parse_query(self, query):
        return query
    
    def __parse_evidence(self, evidence):
        return evidence
    
    def __parse_rule(self, rule):
        p = RuleParser()
        (head,body) = p(rule)
        result = str(head[0][0]) + '::' + head[0][1].toProlog()
        for (prob,lit) in head[1:]:
            result += ';' + prob + '::' + lit.toProlog()
        if body:
            result += '<-' + body[0].toProlog()
            for lit in body[1:]:
                result += ',' + lit.toProlog()
        else:
            result += '<-true'
        result += '.'
        return result
    
class GroundProbLogParser:
    def __call__(self, lpad, queries, evidence):
        self.__parse_queries(queries)
        self.__parse_evidence(evidence)
        self.__parse_lpad(lpad)
        return (self.__logicProgram, self.__constraints, self.__weights, self.__queries, self.__evidence)
            
    def __parse_queries(self, queries):
        self.__queries = set([])
        for line in open(queries):
            self.__queries.add(Literal.parse(line.strip()))
            
    def __parse_evidence(self, evidence):
        self.__evidence = set([])
        for line in open(evidence):
            atom = line.split()[0]
            truth = line.split()[1]
            if truth == 'true':
                self.__evidence.add(Literal(atom,True))
            elif truth == 'false':
                self.__evidence.add(Literal(atom,False))
            else:
                raise ParseError('The truth value for evidence: ' + atom + ' should be true/false')
        
    def __parse_lpad(self, lpad):
        self.__weights = Weights()
        self.__logicProgram = LogicProgram()
        self.__constraints = []
        self.__rule_counter = 0
        for line in open(lpad):
            line = line.strip()
            self.__parse_AD(line)
                
    def __parse_AD(self,ad):
        p = RuleParser()
        (head,body) = p(ad)
        head = self.__calculate_probabilities(head)
        choices = self.__get_choices(head)
        self.__make_rules(choices, body)
        self.__make_constraints(choices, body)
            
    def __calculate_probabilities(self,head):
        new_head = []
        for (prob,atom) in head:
            if '/' in prob:
                parts = prob,atom.split('/')
                new_head.append((float(parts[0])/float(parts[1]),atom))
            else:
                new_head.append((float(prob),atom))
        return new_head
        
                    
    def __get_choices(self,head):
        total_prob = 0
        result = []
        for i in range(0,len(head)):
            (prob,atom) = head[i]
            total_prob += prob
            self.__weights[atom] = 1.0
            self.__weights[-atom] = 1.0
            choice = Literal('choice_node_' + str(self.__rule_counter) + '_' + str(i),True)
            self.__weights[choice] = prob
            self.__weights[-choice] = 1.0
            result.append((atom,choice))
        if total_prob > 1:
            raise ParseError('the total probability of a rule is bigger than one: ' + head)
        nillChoice = Literal('choice_node_' + str(self.__rule_counter) + '_' + str(len(head)),True)
        self.__weights[nillChoice] = round(1-total_prob)
        self.__weights[-nillChoice] = 1.0
        result.append((None,nillChoice))
        self.__rule_counter += 1
        return result
                
    def __make_rules(self,choices,body):
        for (head,choice) in choices:
            if head:
                body_copy = [choice]
                for atom in body:
                    body_copy.append(atom)
                self.__logicProgram.add_rule(head, body_copy)
            
    def __make_constraints(self,choices,body):
        if len(choices) > 1:
            for i in range(0,len(choices)- 1):
                for j in range(i+1,len(choices)):
                    self.__constraints.append([-choices[i][1],-choices[j][1]])
        constraint = []
        for (_,choice) in choices:
            constraint.append(choice)
        if body != ['true']:
            for atom in body:
                constraint.append(-atom)
                for (_,choice) in choices:
                    self.__constraints.append([-choice,atom])
            self.__constraints.append(constraint)
    
class RuleParser:
    def __call__(self, rule):
        (head, body) = self.__split_head_body(rule[:-1])
        head = self.__parse_head(head)
        body = self.__parse_body(body)
        return (head,body)
        
    def __split_head_body(self, rule):
        parts = self.__split(rule,':-','<-')
        if len(parts) == 1:
            return (parts[0],'true')
        elif len(parts) == 2:
            return (parts[0],parts[1])
        else:
            raise ParseError('more than one :- in rule: ' + rule)
        
    def __parse_head(self, head):
        if len(self.__split(head, ',')) > 1:
            raise ParseError("heads of rules can't contain conjunction: '" + head)
        atoms = self.__split(head,';')
        result = []
        for atom in atoms:
            parts = self.__split(atom,'::')
            if len(parts) == 1:
                prob = '1.0'
                pred = Literal.parse(atom)
            elif len(parts) == 2:
                prob = parts[0]
                pred = Literal.parse(parts[1])
            else:
                raise ParseError('more than one :: in head: ' + head)
            if not pred.truth_value:
                raise ParseError('no negation in the head of rules supported: ' + head)
            result.append((prob,pred))
        return result
    
    def __parse_body(self,body):
        if len(self.__split(body,';')) > 1:
            raise ParseError("bodies of rules can't contain disjunctions: '" + body)
        result = []
        for atom in self.__split(body,','):
            if atom != 'true':
                result.append(Literal.parse(atom))
        return result
    
    def __split(self,string,*separators):
        parts = [string]
        for separator in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(separator))
            parts = new_parts
        singleQuoted = False
        doubleQuoted = False
        bracketCount = 0
        result = ['']
        for part in parts:
            for char in part:
                if char == "'":
                    if not doubleQuoted:
                        singleQuoted = not singleQuoted
                elif char == '"':
                    if not singleQuoted:
                        doubleQuoted = not doubleQuoted
                elif char == '(':
                    bracketCount += 1
                elif char == ')':
                    bracketCount -= 1
            result[-1] += part
            if not singleQuoted and not doubleQuoted and not bracketCount:
                result.append('')
            else:
                result[-1] += separator[0]
        del result[-1]
        if singleQuoted:
            raise ParseError('single quotes not closed: ' + string)
        if doubleQuoted:
            raise ParseError('double quoted not closed: ' + string)
        if bracketCount:
            raise ParseError('wrong brackets: ' + string)
        return result
            
        
class ParseError(Exception):
    def __init__(self,msg):
        self.__msg = msg
        
    def __str__(self):
        return 'error while parsing: ' + self.__msg
