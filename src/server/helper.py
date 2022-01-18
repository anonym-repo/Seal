from __future__ import division
from server import server, db, bcrypt, state_machine
from server.models import User, StateMetadata, Action_capability
from flask_login import  current_user

from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)
import math
import operator
import networkx as nx
import matplotlib.pyplot as plt

import os
import os.path
import pickle

class NumericStringParser(object):

    def pushFirst(self, strg, loc, toks):
        self.exprStack.append(toks[0])

    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0] == '-':
            self.exprStack.append('unary -')

    def __init__(self):
        point = Literal(".")
        e = CaselessLiteral("E")
        fnumber = Combine(Word("+-" + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(e + Word("+-" + nums, nums)))
        ident = Word(alphas, alphas + nums + "_$")
        plus = Literal("+")
        minus = Literal("-")
        mult = Literal("*")
        div = Literal("/")
        lpar = Literal("(").suppress()
        rpar = Literal(")").suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal("^")
        pi = CaselessLiteral("PI")
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                 (ident + lpar + expr + rpar | pi | e | fnumber).setParseAction(self.pushFirst))
                | Optional(oneOf("- +")) + Group(lpar + expr + rpar)
                ).setParseAction(self.pushUMinus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + \
            ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
        term = factor + \
            ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
        expr << term + \
            ZeroOrMore((addop + term).setParseAction(self.pushFirst))
        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf = expr
        # map operator symbols to corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {"+": operator.add,
                    "-": operator.sub,
                    "*": operator.mul,
                    "/": operator.truediv,
                    "^": operator.pow}
        self.fn = {"sin": math.sin,
                   "cos": math.cos,
                   "tan": math.tan,
                   "exp": math.exp,
                   "abs": abs,
                   "trunc": lambda a: int(a),
                   "round": round,
                   "sgn": lambda a: abs(a) > epsilon and cmp(a, 0) or 0}

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack(s)
        if op in "+-*/^":
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluateStack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parseAll=True):
        self.exprStack = []
        results = self.bnf.parseString(num_string, parseAll)
        val = self.evaluateStack(self.exprStack[:])
        return val

def get_current_state():
    user = User.query.filter_by(id=current_user.id).first()
    return user.current_state
    
def set_user_state(to_state): 
    metadata = get_all_metadata()
    user = User.query.filter_by(id=current_user.id).first()
    user.current_state = to_state
    
    if not to_state == 0 :
      stateMetadata = StateMetadata.query.filter_by(user_id=current_user.id, state=user.current_state).first()
      if not stateMetadata:
        stateMetadata = StateMetadata(user_id=current_user.id, state=to_state, metadata_sys=metadata['metadata_sys'], metadata_manual=metadata['metadata_manual'], metadata_taint=metadata['metadata_taint'])
      else:
        stateMetadata.metadata_sys = metadata['metadata_sys']
        stateMetadata.metadata_manual = metadata['metadata_manual']
        stateMetadata.metadata_taint = metadata['metadata_taint']
        
      db.session.add(stateMetadata)
    db.session.commit()
    
def get_all_metadata():
    user = User.query.filter_by(id=current_user.id).first()
    state = StateMetadata.query.filter_by(user_id=current_user.id, state=user.current_state).first()
    return {"metadata_sys" : state.metadata_sys, "metadata_manual" : state.metadata_manual, "metadata_taint" : state.metadata_taint}

def set_all_metadata(metadata):
    user = User.query.filter_by(id=current_user.id).first()
    stateMetadata = StateMetadata.query.filter_by(user_id=current_user.id, state=user.current_state).first()
    stateMetadata.metadata_sys = metadata["metadata_sys"]
    stateMetadata.metadata_manual = metadata["metadata_manual"]
    stateMetadata.metadata_taint = metadata["metadata_taint"]
    db.session.commit()
    

def divide_chunks(list_in, n):
    # looping till length l
    for i in range(0, len(list_in), n): 
        yield list_in[i:i + n]
            
def filter_actions_by_caps(actions):
    return actions

def create_user(username, email,
                password, firstname,
                lastname, is_admin=False):
    
    hashed_password = bcrypt.generate_password_hash("password").decode('utf-8')
    
    user1 = User(username='john.doe', email='john.doe@uni.edu',
                 password=hashed_password,
                 firstname='John', lastname='Doe')
    
    user_admin = User(username='admin', email='admin@uni.edu',
                 password=hashed_password,
                 firstname='Admin', lastname='', is_admin=True)
    
    db.session.add(user_admin)
    db.session.add(user1)
    db.session.commit()

    met_sys = dict(visitedStates = "START", invokedActions="START")
    stateMetadata1 = StateMetadata(user_id=user1.id, state=user1.current_state, metadata_sys=met_sys, metadata_manual=dict(), metadata_taint=dict())
    print(stateMetadata1)
    db.session.add(stateMetadata1)
    db.session.commit()

def createe_action_capability(capabilities, properties):
    action_cap = Action_capability(capability = capabilities, properties = properties)
    db.session.add(action_cap)
    db.session.commit()
    return action_cap.id
    
def get_parameters_types_of_action(act_name, prarms_set_name):
    current_state = get_current_state()
    action = state_machine.get_action_by_name_at(current_state, act_name)
 
    types = action.get_parameters_type(prarms_set_name)
    return types

def is_int(s):
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

def parse_listkv(param_value, orig_type):
    param_list = []
    error = None
    
    all_params = param_value.split(",")
    for elm in all_params:
        if elm == '':
            break
        tmp_val = elm.split("=")
        if len(tmp_val) == 2 :
            param_list.append((tmp_val[0].rstrip().lstrip(), tmp_val[1].rstrip().lstrip()))
        else:
            return param_list, "[ERR][parse_listkv] Keys and values should be sparated by a \'=\'"
    
    for elm in param_list:
        if orig_type == 'integer':
            if not is_int(elm[1]):
                error = "[ERR][parse_listkv] parameter " + elm[0] + " should be an integer"
            else:
                try:
                    elm[1] = int(parser.eval(elm[1]))
                except:
                    error = "[ERR][parse_listkv] parameter " + elm[0] + " should be an integer or parsable mathematical expression"
        elif orig_type =='float':
            try:
                elm[1] = parser.eval(elm[1])
            except:
                error = "[ERR][parse_listkv] parameter " + key + " should be a float or parsable mathematical expression"
        
        if error != None:
            param_list = []
            return param_list, error
    return param_list, error
        
def check_and_convert_parameteres(parameters, types):
    errors = list()
    parser = NumericStringParser()
    for key in parameters.keys():
        orig_type = types[key]
        if orig_type == 'integer':
            if not is_int(parameters[key]):
                errors.append("[ERR][check_and_convert_parameteres] parameter " + key + " should be an integer")
            else:
                try:
                    parameters[key] = int(parser.eval(parameters[key]))
                except:
                    errors.append("[ERR][check_and_convert_parameteres] parameter " + key +
                                  " should be an integer or parsable mathematical expression")
        elif orig_type =='float':
            try:
                parameters[key] = parser.eval(parameters[key])
                
            except:
                errors.append("[ERR][check_and_convert_parameteres] parameter " + key +
                              " should be a float or parsable mathematical expression")     
        elif orig_type.startswith('listkv'):
             param_list, error = parse_listkv(parameters[key], orig_type[7:])
             if error != None:
                 errors.append(error)
                 
             else:
                 parameters[key] = param_list
                 
        else:
            pass
        
    return errors
        
def extract_params(form_data):
    act_name = form_data['action'] 
    params = list()
    errors = list()
    
    if act_name == 'None':
        return list(), list()
    
    par_set_key = 'selection-params-set_' + act_name
    for key, value in form_data.items() :
        print ("       ", key, value)
    
    if par_set_key not in form_data.keys():
        return params, errors
    
    params_set_name = form_data[par_set_key]
    types = get_parameters_types_of_action(act_name, params_set_name)
    params = dict()
    
    prefix = "param__" + act_name + "__paramset__" + params_set_name
    filtered_params =  dict(filter(lambda elem: elem[0].startswith(prefix), form_data.items()))
    for key in filtered_params.keys():
        new_key =  key.split("__")[-1]
        params[new_key] = filtered_params[key]
        
    errors = check_and_convert_parameteres(params, types)
    return params, errors

def reset_state():
    set_user_state(0)


def select_raw_data(level):
    fileList = []
    for root, dirs, files in os.walk("./raw_data"):
        for filename in files:
            fileList.append(filename)
    return fileList


    
def correct_tmp_filenames(user_id, to_state):
    filename = './output_files/id_' + str(user_id) + '_state_' + str(to_state)
    
    tmp_filename = filename + '_tmp'
   
    os.remove(filename)
    
    os.rename(tmp_filename, filename)
