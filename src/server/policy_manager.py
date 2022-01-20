from multiprocessing import Process, Pipe
import server.helper as hlp
from flask import request, session
from server import server, db, bcrypt, state_machine
import server.execution_manager as em
from flask_login import current_user
import server.capability_manager as cm

def processActionRequest(current_state, act_name):
        try:
            
            action = state_machine.get_action_by_name_at(current_state, act_name)
            action_type = action.get_action_type()
            
            to_state = action.get_to_state()
            need_raw_data = action.need_raw_data_input()
              
            if((current_state == 0 or need_raw_data) and ('rawfiles' not in session)):
                raise Exception("please select raw data files beforehand")
                    
    
            if('cap_file' not in session):
                raise Exception("please upload a capability beforehand")
            
            required_budget =  action.get_required_budget()
            
            if not required_budget == 0:
				if cm.reduce_budget(required_budget) == -1:
					raise Exception("not enough privacy budget")
        except Exception as e:
            raise Exception(str(e))


def setState(act_name, to_state):
	hlp.set_user_state(to_state)
    ms = current_metadata["metadata_sys"]
    ms["visitedStates"] += ", " + state_machine.get_state_name(to_state)
    ms["invokedActions"] += ", " + act_name
    hlp.set_all_metadata(current_metadata)
