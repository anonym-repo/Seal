from multiprocessing import Process, Pipe
from flask import request, session
from server import server, db, bcrypt, state_machine
from flask_login import current_user

import server.execution_manager as em
import server.capability_manager as cm
import server.policy_manager as pm
import server.file_manager as fm
import server.helper as hlp


def processRequest(form):
	if  current_user.is_authenticated:
        current_state = hlp.get_current_state()
        current_metadata = hlp.get_all_metadata()
        state_name = state_machine.get_state_name(int(current_state))
    else:
        raise Exception("User is not authenticated")
        
        
    params, errors = hlp.extract_params(form)
    if errors:
        for err in errors:
            flash(err, 'danger') 
    else:
		try:
			if(not cm.check_capability(session['cap_file'])):
                raise Exception("no appropriate cap has been found")
            
            act_name = form.get('action')
            pm.processActionRequest(current_state, act_name)
            
            server_conn, dispatcher_conn = Pipe()
            
            fds_in = None
            fds_out = None
            
            if (action_name != 'None'):
				if action_type == 'user_function':
					fds_in = fm.prepare_input_files(user_id, current_state, need_raw_data, False)
					fds_out = fm.prepare_output_file(user_id, tmp_to_states)
				else:
					if action_name.startswith('fw_'):
						fds_in = fm.prepare_input_files(user_id, current_state, need_raw_data, False)
					else:
					   fds_in = fm.prepare_input_files(user_id, current_state, need_raw_data, True)
					   
					fds_out = fm.prepare_output_file(user_id, tmp_to_states)
					
            prc = Process(target=em.entry,
            args=(dispatcher_conn, params, current_user.id, current_state,
                      to_state, act_name, action_type, need_raw_data, fds_in, fds_out, ))
            
            prc.start()
            
            dispatcher_error = False
            msg =  server_conn.recv()
            
            if not msg == "Done":
                dispatcher_error = True

            if not dispatcher_error:
                msg =  server_conn.recv()
                if act_name == 'None':
                    metadata = [] 
                elif act_name == 'Go-To':
                    metadata = []
                else:
                   if current_state == to_state:
                        hlp.correct_tmp_filenames(current_user.id, to_state)
                        
                               
            prc.join()
       
            if not dispatcher_error:
               pm.setState(act_name, to_state)
               
         except Exception as e:
            raise Exception(str(e))
