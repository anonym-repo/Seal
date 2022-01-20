
from base64 import b64encode, b64decode
import hashlib
from Cryptodome.Cipher import AES
import os
from Cryptodome.Random import get_random_bytes
from flask import session
from flask_login import  current_user
import server.helper as hlp
from server.models import Action_capability
from server import server, db, bcrypt
import server.caps as cs

key = b'very secret key_'
delima = ";;;"
init_properties = 1
revoked_subproperty = 16
disabled_subproperty = 8

system_capabilities = []


def get_action_capability(entry_id):
    cap = Action_capability.query.filter_by(id=entry_id).first()
    return cap
    

def add_to_system_capabilities(sys_cap):
	global system_capabilities
	system_capabilities.append(sys_cap)
	return len(system_capabilities) - 1
	



def check_capability(filename):
     try:
         f = open("./cap_folder/"+filename, "r")
         analyst_capability = f.read()
         elements = analyst_capability.split(';')
         
         analyst_id = elements[0]
         pointer = elements[1]
         hash_value = elements[2]
         
         first_part = str(analyst_id) + str(pointer)
         
         if not bcrypt.check_password_hash(hash_value, first_part):
             print("ERRRO: no match\n", hash_value, "\n", calculated_hash)
             return False
         
         return True
         
     except Exception as e:
         print("Error of exception " , str(e))
         return False
     
def create_caps(analyst_id, permissions, rights, privacy_budget):
	global system_capabilities
	sys_cap = {}
	sys_cap['permissions'] = permissions
	sys_cap['rights'] = rights
	sys_cap['privacy_budget'] = privacy_budget
	
	pointer = add_to_system_capabilities(sys_cap)
	first_part = str(analyst_id) + str(pointer)
	
	hash_value = bcrypt.generate_password_hash(first_part).decode('utf-8')
	analyst_cap = str(analyst_id) + ';' + str(pointer) + ';' + hash_value
	system_capabilities[pointer]['hash_value'] = bcrypt.generate_password_hash(analyst_cap).decode('utf-8')
	
	with open('./cap_folder/cap_analyst_' + str(analyst_id) + '.txt', 'w') as f:
            f.write(analyst_cap)
	
	return analyst_cap
	
	
	
def create_action_capability(capabilities, properties):
    action_cap = Action_capability(capability = capabilities, properties = properties)
    db.session.add(action_cap)
    db.session.commit()
    return action_cap.id
    
    
def delegate(action_cap_id, user_id, capabilities, properties = init_properties):
    new_id = create_action_capability(capabilities, properties)
    new_cap = Action_capability.query.filter_by(id=new_id).first()
    act_cap = Action_capability.query.filter_by(id=action_cap_id).first()
    new_cap.parent = action_cap_id
    pre_last_child_id = act_cap.last_child
    
    if(pre_last_child_id == None):             # it is the first delegated child
        act_cap.first_child = new_id
    else:                                      # insert new delgated capbility at the end of the list
        Prev_Last_Child = Action_capability.query.filter_by(id=pre_last_child_id).first()
        act_cap.last_child = new_id
        Prev_Last_Child.right_sibling = new_id
        new_cap.left_sibling = pre_last_child_id
    
    act_cap.last_child = new_id
    db.session.commit()

def revoke_capability(act_cap_id):
    revoked_cap = Action_capability.query.filter_by(id=act_cap_id).first()
    parent = Action_capability.query.filter_by(id=revoked_cap.parent).first()
    
    if(parent == None):
        return
    
    if(parent.first_child == parent.last_child): # it is the only delegated capability
       parent.first_child = None
       parent.last_child = None
    elif(parent.first_child == int(act_cap_id)): 
       parent.first_child = revoked_cap.right_sibling
       prev_rs = Action_capability.query.filter_by(id=revoked_cap.right_sibling).first()
       prev_rs.left_sibling = None
    elif(parent.last_child == int(act_cap_id)):
       parent.last_child = revoked_cap.left_sibling
       prev_ls = Action_capability.query.filter_by(id=revoked_cap.left_sibling).first()
       prev_ls.right_sibling = None
    else:                                        #the revoked capability is in the middle of the delegated capabilities' list
       prev_ls = Action_capability.query.filter_by(id=revoked_cap.left_sibling).first()
       prev_rs = Action_capability.query.filter_by(id=revoked_cap.right_sibling).first()
       prev_ls.right_sibling = prev_rs
       prev_rs.left_sibling = prev_ls
      
    revoked_cap.properties |= revoked_subproperty #mark the revoked capability
    db.session.commit()


def disable_capability(act_cap_id):
    disabled_cap = Action_capability.query.filter_by(id=act_cap_id).first()
    disabled_cap.properties |= revoked_subproperty #mark the revoked capability
    db.session.commit()
    
 
def get_child_caps(cap_file):
    child_caps = []
    if True: #('cap_file' in session):
        #filename = session['cap_file']
        f = open("./cap_folder/" + cap_file, "r")
        user_capability = f.read()
        plain_txt = decrypt(user_capability)
        split_data = bytes.decode(plain_txt).split(";")
        user_id = split_data[0].split('=')[1]
        
        if(not(hlp.is_int(user_id)) or not(( int(user_id) == current_user.id))):
           raise Exception("wrong uploaded capability")
        
        act_cap_id = split_data[1].split('=')[1]
        act_cap = Action_capability.query.filter_by(id=act_cap_id).first()
     
        next_child_id = act_cap.first_child
        while( not(next_child_id == None)): # there is at least one delegated capability
            c_cap = Action_capability.query.filter_by(id=next_child_id).first()
            if ((c_cap.properties & revoked_subproperty)  == 0): #select childs which are not revoked
                child_caps.append(c_cap)
            next_child_id = c_cap.right_sibling
        
    return child_caps
    
    
def listAll():
    caps = Action_capability.query.all()
    #print("[LOG][listall]\n", caps)


def __init__(self):
	global system_capabilities
	system_capabilities = [1]

