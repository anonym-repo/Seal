from typing import List
from os import path
import networkx as nx

from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
import pygraphviz as pgv
from networkx.drawing.nx_pydot import write_dot
import json
from json import JSONEncoder

def print_set_params(k, v):
    print("---------------------------------")
    print("parameter set name: ", k)
    for i in range(len(v)):
        print("name: \"" + v[i].get_name() + "\", value: \""
              + v[i].get_value() + "\", type: \"" + v[i].get_type() + "\"")
        
class param(JSONEncoder):
    name: str
    value: str
    param_type: str

    def __init__(self, name, param_type):
        self.name = name
        self.value = ""
        self.param_type = param_type

    def set_value(self, value):
        self.value = value

    def get_name(self):
        return self.name

    def get_value(self):
        return self.value

    def get_type(self):
        return self.param_type

#Parameters = List[param]

class action:
    to_state: int
    name: str
    alias: str
    #parameters: Parameters
    need_raw_data: bool
    check_params_func: str
    action_type: str
    required_budget: int

    def __init__(self, to_state, name, alias, needRawData, check_params_func, parameters, action_type):
        self.to_state = to_state
        self.name = name
        self.parameters = parameters
        self.need_raw_data = needRawData
        self.check_params_func = check_params_func
        self.alias = alias
        self.action_type = action_type
#        print("****===========================================================")
#        print("act_to_state: ", self.to_state, " act_name: ", self.name)
#        for k, v in self.parameters.items():
#            print("---------------------------------")
#            print("parameter set name: ", k)
#            for i in range(len(v)):
#               print("name: \"" + v[i].get_name() + "\", value: \""
#               + v[i].get_value() + "\", type: \"" + v[i].get_type() + "\"")
#        print("action_type: ", self.action_type)

    def get_name(self):
        return self.name

    def get_alias(self):
        return self.alias
    
    def get_to_state(self):
        return self.to_state

    def get_parameters(self):
        return self.parameters

    def get_parameters_type(self, params_set_name):
        if params_set_name == "":
            return dict()
        if params_set_name not in self.parameters:
            raise Exception("Not such a parameter set")
        params_set = self.parameters[params_set_name]
        types = dict()
        for param in params_set:
            types[param.get_name()] = param.get_type()

        return types
    

    def get_parameter_at(self, params_set_name, index):
        if params_set_name not in self.parameters:
            raise Exception("Not such a parameter set")
        params_set = self.parameters[params_set_name]
        if index >= len(params_set):
             raise Exception("Out of range, no such a parameter")
        return params_set[index]
    
    def need_raw_data_input(self):
        return self.need_raw_data

    def get_parameters_len(self, params_set_name):
        if params_set_name not in self.parameters:
            raise Exception("Not such a parameter set")
        params_set = self.parameters[params_set_name]
        return len(params_set)
 
    def get_action_type(self):
        return self.action_type

    def get_required_budget(self):
		return self.required_budget
		
Actions = List[action]

class state:
    id: int
    name: str
    actions: Actions

    def __init__(self, s_name):
        self.name = s_name
        self.actions = list()
        
    def get_name(self):
        return self.name

    def add_action(self, new_action):
        self.actions.append(new_action)

    def actions_len(self):
        return len(self.actions)

    def get_action(self, index):
        if index >= 0 and index < len(self.actions):
            return self.actions[index]
        return -1

    def get_action_by_name(self, name):
        return  next(filter(lambda act: act.get_name() == name, self.actions), None)
    
    def get_actions(self):
         return self.actions

States = List[state]

class fsm:
    num_of_states: int
    states: States
    isLoaded: bool

    def __init__(self):
        num_of_states = 0
        states = None

    def print_fsm(self):
        print("number of sates is: " + str(self.num_of_states))
        for index in range(self.num_of_states):
            print("===========================================================")
            print("state number " + str(index))
            print("    state name: " + self.states[index].get_name())
            state = self.states[index]
            print("    number of actions: " + str(state.actions_len()))
            for idx in range(state.actions_len()):
                action = state.get_action(idx)
                print("        action " + str(idx + 1) + ": to state -> "
                      + str(action.get_to_state()) + " -- name : " + action.get_name())
                print("            Does action need raw data?: "  +
                      str(action.need_raw_data_input()))
                for params_set_name, params_set in action.get_parameters().items():
                    print("            parameters set: ", params_set_name)
                    for param_idx in range(len(params_set)):
                        param = params_set[param_idx]
                        print("                  parameter number " + str(param_idx) + " --> "
                            + "name: \"" + param.get_name() + "\", value: \""
                            + param.get_value() + "\", type: \"" + param.get_type() + "\"")
                print("            action_type: ", action.action_type)

    def find_state_by_name(self, name):
        found = False
        for index in range(self.num_of_states):
            if self.states[index].get_name() == name:
                found = True
                break

        if found:
            return index
        return -1

    def get_actions_at(self, index):
        return self.states[index].get_actions()
    
    def get_state_name(self, index):
        if index < 0 or index >= len(self.states):
            raise Exception("out of bound, no such sate in the defined index")
        return self.states[index].get_name()

    def get_action_by_name_at(self, index, act_name):
        return self.states[index].get_action_by_name(act_name)

    def get_states(self):
        return self.states

    def generate_graphs(self):
        states = self.states
        length = len(states)
        for current_state in range(length):
            out_file = './server/static/graphs/' + str(current_state) + '_sm_plot.png'
            current_state_name = states[current_state].get_name()
            DG=nx.DiGraph()
            for index in range(length):
                 if index == current_state:
                      DG.add_node(states[index].get_name(), style='filled',fillcolor='red')
                 else:
                      DG.add_node(states[index].get_name(), style='filled',fillcolor='yellow')

            for state in states:
                 state_name = state.get_name()
                 actions = state.get_actions()

                 if state_name == current_state_name:
                      colr = 'blue'
                 else:
                      colr = 'black'
                 for act in actions:
                      to_state_name = states[act.get_to_state()].get_name()
                      DG.add_edge(state_name, to_state_name, label=str(act.get_alias()), fontcolor=colr, color=colr)

            A = to_agraph(DG)
            A.layout(prog='dot', args="-Grankdir=LR -Gdecorate=True")
            A.draw(out_file)
            out_file = './server/static/graphs/' + str(current_state) + '_sm_plot.svg'
            A.draw(out_file)
        
            
    def load(self, filePath):
        self.num_of_states = 0;
        self.states = list()
        fp = None

        with open(filePath) as fp:
           line = fp.readline()
           tokens = line.rstrip("\n").split(" ")
           self.num_of_states = int(tokens[1])
           #Process states
           for index in range(self.num_of_states):
               line = fp.readline()
               tokens = line.rstrip("\n").split(" ")
               s_name = tokens[1]
               self.states.append(state(s_name))

           #Process actions
           line = fp.readline()
           tokens = line.rstrip("\n").split(" ")
           token_length = len(tokens)
           token_index = 0
           action_type = None
           required_budget = 0
           while tokens[0] == "EDGE":
               token_index += 1
               act_from_state = tokens[token_index]
               token_index += 1
               
               index = self.find_state_by_name(act_from_state)
               if index == -1:
                   raise Exception("Sorry, a problem occured during the loading of the state machine")

               act_to_state = self.find_state_by_name(tokens[token_index])
               token_index += 1
               act_name = tokens[token_index]
               token_index += 1

               alias = tokens[token_index]
               token_index += 1
               
               act_need_raw_data = False
               if tokens[token_index] == "Need_Raw_Data":
                   
                   if tokens[token_index + 1] == "true":
                       act_need_raw_data = True
                   
                   token_index += 2
               
               #check parameters function
               check_params_func = None
               if token_index < token_length and tokens[token_index] == "check_params_fun":
                   check_params_func = tokens[token_index + 1]
                   token_index += 2
                   
               
               action_params_set = {}
               set_params = list()
               params_set_name = None
               
               while token_index < token_length:
                    params_set_name == None
                    token = tokens[token_index]
                    
                    if token.startswith("parameter_set"):                      
                        params_set_name = token
                        set_params = []
                        token_index += 1
                        token = tokens[token_index]
                        
                        while token == "param" and token_index < token_length:
                            param_name_token = tokens[token_index + 1]
                            param_value_token = tokens[token_index + 2]
                            token_index += 3
                            tmp_param = param( param_name_token, param_value_token)
                            set_params.append(tmp_param)
                            token = tokens[token_index]
                        
                        if not set_params:
                            raise Exception("[Exception] parameter_set has no parameter")
                        else:
                            if params_set_name != None:
                                action_params_set[params_set_name] = set_params 
                            
                    elif token == "action_type":
                        action_type = tokens[token_index + 1]
                        token_index += 2
                    
                    elif token == "required_budget":
                        required_budget = int(tokens[token_index + 1])
                        token_index += 2
                        
                    else:
                        raise Exception("[Exception] unknow input token name - token is: ", token)

               new_action = action(act_to_state, act_name, alias, act_need_raw_data,
                                   check_params_func, action_params_set, action_type, required_budget)
               
             
               self.states[index].add_action(new_action)
               line = fp.readline()
               tokens = line.rstrip("\n").split(" ")
               token_length = len(tokens)
               token_index = 0

        #self.print_fsm()
        self.generate_graphs()


