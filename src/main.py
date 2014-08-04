#! /usr/bin/env python3

import utils, ground, sys
from loop_breaking import LoopBreaker
from clarks_completion import ClarksCompletion
from logic import CNF

def main(argv) :
    with utils.WorkEnv('out/',2) as work_env:
        grounder = ground.Grounder()
        (rules, constraints, weights, queries, evidence) = grounder(argv, work_env)
        l = LoopBreaker()
        (new_rules,new_weights,new_evidence) = l(rules,weights,queries,evidence)
        c = ClarksCompletion()
        (completion,translation, cnf_weights) = c(new_rules,new_weights,queries | new_evidence)
        print(completion.toDimacs())
        
    
if __name__ == '__main__' :
    main(sys.argv[1:])