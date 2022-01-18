import inspect
import enum

import numpy as np
from sklearn import *

from server.taintWrappers import *
from io import TextIOWrapper, BufferedWriter

from copy import deepcopy


fd = open('oo.txt', 'w')

    
def make_str_abort_wrapper(fun):
    def proxy(*args, **kwargs):
        raise tstr.TaintException('%s Not implemented in TSTR' % fun.__name__)
    return proxy

def trace_return():
    METHOD_NUM_STACK.pop()

def trace_set_method(method):
    set_current_method(method, len(METHOD_NUM_STACK), METHOD_NUM_STACK[-1][0])
    
class in_wrap:
    def __init__(self, s):
        self.s = s

    def in_(self, s):
        return self.s in s

def taint_wrap__(st):
    if isinstance(st, str):
        return in_wrap(st)
    else:
        return st


class Taint:
    def __init__(self):
        self.TAINTS = [None]

    def push(self, v):
        #print("[LOG TT][push] value = ", v)
        self.TAINTS.append(v)

    def pop(self):
        #print("[LOG TT][pop]")
        self.TAINTS.pop()

    def t(self):
        return self.TAINTS[-1]
        print(' ' * len(self.TAINTS), self.t(), repr(p), repr(val), 'taint:',hasattr(val, 'taint'), 'bgtaint:', t.t())


            
    def __call__(self, val):
        # if hasattr(val, 'taint'): print('tainted: A')
        # also check if self.t() has a taint
        # if self.t()[1] is not None: print('tainted: B')
        
        current_taint = val.taint if hasattr(val, 'taint') else None
        # if self.t()[1] is None: return val

        current_taint = taint_policy(current_taint, self.t()[1])
       
        if hasattr(val, 'taint'):
            if isinstance(val, tTextIOWrapper) or isinstance(val, tBufferedWriter):
                return val
            
            val.taint = current_taint
            return val
        
            if val is None: return val
            return val            
           
        if isinstance(val, int): return tint(val, current_taint)
        if isinstance(val, bool): return tbool(val, current_taint)
        if isinstance(val, tuple): return ttuple(val, current_taint)
        if isinstance(val, str): return tstr(val, current_taint)
        if isinstance(val, float): return tfloat(val, current_taint)
        if isinstance(val, list): return tlist(val, current_taint)
        if isinstance(val, dict): return tdict(val, current_taint)
        if isinstance(val, np.ndarray): return tndarray(val, current_taint)
        if isinstance(val, preprocessing._data.StandardScaler): return tStandardScaler(val, current_taint)
        if isinstance(val, linear_model._logistic.LogisticRegression): return tLogisticRegression(val, current_taint)
        if isinstance(val, TextIOWrapper): return tTextIOWrapper(val, current_taint)
        if isinstance(val, BufferedWriter): return tBufferedWriter(val, current_taint)
        if val is None: return val
        return val

TAINTS = Taint()



import traceback
class T_method:
    def __init__(self, method_name, *args):
        self.method_name = method_name
        
    def __enter__(self):
        taint = None # method by default does not have a base taint.
        TAINTS.push([self.method_name, taint])
        #TAINTS.p_('*>')
        return TAINTS
    
    def __exit__(self, typ, val, tb):
        #p = '*<'
        if isinstance(val, Exception):
             #p = '*<' + str(val)
             traceback.print_tb(tb)
        #STAINTS.p_(p)
        TAINTS.pop()
        
T_method__ = T_method

from contextlib import contextmanager
@contextmanager
def T_method__x(method_name, *args):
    taint = None # method by default does not have a base taint.
    TAINTS.push([method_name, taint])
    #TAINTS.p_('*>')
    try:
        yield TAINTS
    finally:
        #TAINTS.p_('*<')
        TAINTS.pop()

class T_scope:
    def __init__(self, scope_name, num, taint_obj):
        taint = taint_obj.t()[1]
        TAINTS.push([scope_name, taint])
        #TAINTS.p_('> %s %s' % (scope_name, num))
        
    def __enter__(self):
        return TAINTS
    
    def __exit__(self, typ, val, tb):
        #p = '*<--'
        if isinstance(val, Exception):
             traceback.print_tb(tb)
        #TAINTS.p_(p)
        TAINTS.pop()
T_scope__ = T_scope

@contextmanager
def T_scope__X(scope_name, num, taint_obj):
    taint = taint_obj.t()[1]
    TAINTS.push([scope_name, taint])
    #TAINTS.p_('==> %s %s' % (scope_name, num))
    try:
        yield TAINTS
    finally:
        #TAINTS.p_('<')
        TAINTS.pop()

def taint_expr__(expr, taint):
    try:
        #taint.p('>taint_expr', expr, taint)
        if hasattr(expr, 'taint'): # this is tainted
            taint.t()[1] = expr.taint
            
        return expr
    except Exception as e:
        print('TaintErr:', e)
        raise e
    
def wrap_input(inputstr):
    return tstr(inputstr, parent=None) #.with_comparisons([])

