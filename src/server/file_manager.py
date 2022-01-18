import os
import os.path
import pycapsicum as p
import server.helper as hlp
from server.taintWrappers import *
from flask import session

AT_FDCWD = -100

def prepare_raw_input_files(tainted=False):
    fd_list = []
    # make a new CapRights, set to CAP_READ
    b = p.CapRights(['CAP_READ'])

    if(('rawfiles' not in session)):
          raise Exception("please select raw data files beforehand")
  
    cwd = os.getcwd()

    for root, dirs, files in os.walk("./raw_data"):
        for filename in files:
            if(filename in session['rawfiles']):
                fd = p.openat(AT_FDCWD, root+ "/" + filename, 'rw')
                b.limit(fd)
                if tainted:
                    fd_in = tTextIOWrapper(fd, 'HIGH')
                    fd_list.append(fd_in)
                else:
                    fd_list.append(fd)


    return fd_list

def prepare_input_files(user_id, current_state, need_raw_data, tainted=False):
    try:
        fds_in = dict()
        fileName = './output_files/id_' + str(user_id) + '_state_' + str(current_state)
        if current_state == 0:
            fds_in['raw-data'] = prepare_raw_input_files(True)
        elif os.path.exists(fileName):
            current_metadata = hlp.get_all_metadata()
            ms = current_metadata["metadata_sys"]
            mm = current_metadata["metadata_sys"]
            mt = current_metadata["metadata_sys"]
            fd_taint = 'None' # should revise it
            
            input_fd = p.open( fileName, 'rw')
            fdHdlr = os.fdopen(input_fd, "r+")
            # create a new CapRights object
            b = p.CapRights(['CAP_READ'])
            # set those capabilites to x
            b.limit(fdHdlr)
            fds_in['input'] = fdHdlr#_in
            
        else:
            raise Exception(("[prepare_input_files] input file deso not exist"))
        return fds_in

    except Exception as e:
                print("[ERROR] there was an error in preparing input - "+ str(e))


def prepare_output_file(user_id, to_state):

    fds_out = dict()

    try:
        fileName = './output_files/id_' + str(user_id) + '_state_' + str(to_state)
        fd_data = p.open( fileName , 'rwc') # no _data postfix
        dataHdlr = os.fdopen(fd_data, "w+")
        #empty the file if it is not the first time the user call for this state
        dataHdlr.truncate()
        b = p.CapRights(['CAP_WRITE'])
        # set those capabilites to x
        b.limit(dataHdlr)
        fds_out['output'] = dataHdlr#_out
        
        return fds_out 

    except Exception as e:
                print("there was an error in preparing output - "+ str(e))

