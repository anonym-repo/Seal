import pycapsicum as p
import os
import math
import os.path
import algorithms.tainted_functions as al
import algorithms.fw_functions as fwFun 
from server import server
from server.models import StateMetadata
import server.helper as hlp

from server.taintWrappers import *
from flask import session
import cProfile, pstats, io
from pstats import SortKey
from datetime import datetime
from termcolor import colored
import multiprocessing
import subprocess

def execute_user_function(fd_in, fd_out, act_name, do_sandboxing=True):
    try:
        data, attributes, attribute_lines = fwFun.load_data(fd_in)
        length = len(data)
        l = math.ceil(length** 0.4)
        l_length = math.ceil(length/ l)
        splited_data = list(hlp.divide_chunks(data, l_length))
        sum = 0
        recv_end, send_end = multiprocessing.Pipe(False)
        jobs = []
        pipe_list = []
        for sd in splited_data:
            pr = multiprocessing.Process(target=fwFun.fw_user_function_3, args=(sd, send_end))
            jobs.append(pr)
            pipe_list.append(recv_end)
            pr.start()
      
        for proc in jobs:
            proc.join()
    
        sum = 0
        for pl in pipe_list:
            sum += pl.recv()
        
        fd_out.write(str(sum/length))
    except Exception as e:
        raise Exception(str(e))
          
def entry(dispatcher_conn, params, user_id, current_state,
          to_state, action_name, action_type,
          need_raw_data, fds_in, fds_out, do_sandboxing=True):
    tmp_to_states = str(to_state)
    if current_state == to_state:
        tmp_to_states += "_tmp" 
    try:
        if(action_name == 'Go-To'):
            dispatcher_conn.send("Done")
            dispatcher_conn.send("")
        elif (action_name == 'Read'):
            x = 10
        elif (action_name != 'None'):
            if action_type == 'user_function':
                execute_user_function( fds_in['input'] , fds_out['output'], action_name, do_sandboxing)
                dispatcher_conn.send("Done")
                dispatcher_conn.send("")
                if do_sandboxing:
                   #enter capability mode
                   p.enter()
                
            else:
                metadata = []
                if action_name.startswith('fw_'):
                    action_to_call = getattr(fwFun, action_name)
                else:
                   action_to_call = getattr(al, action_name)
                fds_out = fm.prepare_output_file(user_id, tmp_to_states)

                returnValue, returnMsg = action_to_call(params, fds_in, fds_out, metadata)

                if returnValue == True:
                    dispatcher_conn.send("Done")
                    dispatcher_conn.send("")
         
                else:
                    dispatcher_conn.send("Error: " + returnMsg)
        else:
            dispatcher_conn.send("Done")
            taints = []
            dispatcher_conn.send(taints)
            dispatcher_conn.close()
        
    except Exception as e:
        print("[ERROR][Dispatcher] --> " + str(e))
        print(traceback.format_exc())
        dispatcher_conn.send(e)
        dispatcher_conn.close()
