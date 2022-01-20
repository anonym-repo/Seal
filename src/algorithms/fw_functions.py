import server.taints
from server.taints import T_method__, T_scope__
from server.taints import taint_expr__ as T_
from server.taintWrappers import *
import server.staticTaintManager as stm

import numpy as np
import os
from sklearn import preprocessing
import sklearn.linear_model
import pickle
import typing

import multiprocessing
import subprocess

import pycapsicum as p

import re

from diffprivlib.models import LinearRegression

def load_data(fd_list, continue_reading=False):
    datalist = []
    attributes = dict()
    if type(fd_list) != list:
        fd_list = [fd_list]
    for fd in fd_list:
        try:
            lines = fd.readlines()
            print("type of len(lines) is ", len(lines))
            if len(lines) == 0:
                continue
        except:
            continue
        # read the data
        for i in range(len(lines)):
            line = lines[i]
            if line[0] == "|":
                break
            entry = line.replace("\n", "").split(", ")
            if len(entry) > 1:
                datalist.append(entry)
        # read the attributes
        if len(attributes) == 0:
            attribute_counter = 0
            attribute_lines = []
            for j in range(i, len(lines)):
                line = lines[j]
                attribute_lines.append(line)
                if line[0] == "|":
                    continue
                if ":" not in line:
                    continue
                l = line.replace(".", "").replace("\n", "").split(": ")
                column = l[0]
                a = l[1]
                a = a.split(", ")
                attributes[column] = (attribute_counter, a)
                attribute_counter += 1
        # otherwise skip reading the attributes again - they are assumed to be the same if data is split in multiple files
        if not continue_reading:
            break
        else:
            print("have read", len(datalist), "entries, continuing...")
    
    assert len(datalist) > 0, "no data in any of the file descriptors!"
    return datalist, attributes, attribute_lines

def fw_user_function(data, send_end, do_sandboxing=True):
     if do_sandboxing:
       #enter capability mode
       p.enter()
     sum = 0
     for d in data:
       print("----- ", d[7])
       sum += int(d[0])
  
     send_end.send(sum)


def fw_user_function_2(data, send_end, do_sandboxing=True):
     if do_sandboxing:
       #enter capability mode
       p.enter()
     sum = 0
     for d in data:
       dt = d[7]
       if isinstance(dt, str):
          dt = dt.strip()
       if dt.isdigit():
          sum += int(dt)
  
     send_end.send(sum)
    
def fw_user_function_3(data, send_end, do_sandboxing=True):
     if do_sandboxing:
       #enter capability mode
       p.enter()
     
     i = 0
     sum = 0
     for d in data:
       try:
           dt = d[3]
           if isinstance(dt, str):
               dt = dt.strip()
           if dt.isdigit():
               sum += int(dt)
       except Exception as e:
        raise Exception("[ERROR][exc] dt is = ", d)
  
     send_end.send(sum)
      
def write_data(fd_list, datalist, attribute_lines):
    writethis = "\n".join([", ".join(data) for data in datalist])
    writethis += "".join(attribute_lines) #lines still have their \n
    writethis += "\n\n"
    if type(fd_list) == list:
        fd_list[0].write(writethis)
        
    else:
        fd_list.write(writethis)
        #fd_list.close()
    
def data_where(fd_list_in, fd_list_out, args):
    data, attributes, attribute_lines = load_data(fd_list_in)
    assert len(args) == 2
    column = args[0]
    value = args[1]
    
    if column not in attributes:
        raise Exception("column %s not available!"%column)
    column_id, column_values = attributes[column]
    if value not in column_values and column_values[0] != "continuous":
        raise Exception("invalid value %s for %s" %(value, column))
    filtered_list = []
    for d in data:
        if d[column_id] == value:
            filtered_list.append(d)
            
    write_data(fd_list_out, filtered_list, attribute_lines)

def convert_attributes(attribute_map, data_elem):
    d_enc = []
    for a_id in range(len(data_elem) - 1): #last one is label
        dea_id = data_elem[a_id]
        if isinstance(a_id, str):
             a_id = a_id.strip()
        dea_id = data_elem[a_id]
        if isinstance(dea_id, str):
             dea_id = dea_id.strip()
        if dea_id == "?":
             d_enc.append(float(0))
             continue
            
        if a_id not in attribute_map:
            d_enc.append(float(dea_id))
        else:
            if a_id in attribute_map and attribute_map[a_id] is not None:
                att = attribute_map[a_id]
                if isinstance(dea_id, str):
                    dea_id = dea_id.strip()
                att = attribute_map[a_id][dea_id]
                if isinstance(att, str):
                    att = att.strip()
                d_enc.append(float(att))
                
    return d_enc
    
def make_train_test(datalist, attribute_map, train_factor):
    X_all = []
    Y_all = []
    i = 1
    for d in datalist:
        d_enc = convert_attributes(attribute_map, d)
        if len(d_enc) > 0:
            X_all.append(np.array(d_enc))
            if d[-1] == "<=50K":
                Y_all.append(0)
            else:
                Y_all.append(1)
        
    X_all = np.array(X_all)
    Y_all = np.array(Y_all)    
        
    ids = [i for i in range(len(X_all))]
    np.random.shuffle(ids)
    if train_factor is not None:
        split = int(train_factor * len(X_all))
        ids_train = ids[:split]
        ids_test = ids[split:]
        return X_all[ids_train], Y_all[ids_train], X_all[ids_test], Y_all[ids_test]
    else:
        return None, None, X_all, Y_all

def learn(X_train, Y_train, X_test, Y_test, C, random_state, outspec):
    clf  = LinearRegression(random_state=42, C=C)
    clf.fit(X_train, Y_train)
    acc = clf.score(X_test, Y_test)
    fd_out, datalist, attribute_lines, fd_model, fd_acc = outspec
    write_data(fd_out, datalist, attribute_lines)
    pickle.dump(clf, fd_model)
    
    fd_acc.write(str(acc))
    
    return fd_acc, fd_model, fd_out       
        
def learn_scaled(X_train, Y_train, X_test, Y_test, C, random_state, outspec):
    scaler = preprocessing.StandardScaler().fit(X_train)
    clf = sklearn.linear_model.LogisticRegression(random_state=42, C=C)
    clf.fit(scaler.transform(X_train), Y_train)
    acc = clf.score(scaler.transform(X_test), Y_test)
    fd_out, datalist, attribute_lines = outspec
    write_data(fd_out, datalist, attribute_lines)
    
    return  fd_out 
    
def load_and_encode_data(fd_list_in):
    datalist, attributes, attribute_lines = load_data(fd_list_in)
    #discrete attributes need to be converted to float, otherwise ValueError: could not convert string to float: 'White'
    #attributes[attribute name][1] is a list -> can be used for indexing 
    attribute_map = dict()
    for a in attributes:
        a_id, values = attributes[a]
        if values[0] == "continuous":
            continue
        if isinstance(a_id, str):
            a_id = a_id.strip()
        attribute_map[a_id] = dict()
        for i in range(len(values)):
            vs = values[i]
            if isinstance(vs, str):
               vs = vs.strip()
            attribute_map[a_id][vs] = float(i)
    return datalist, attributes, attribute_lines, attribute_map

    
def logistic_regression_step(fd_list_in, fds_out, train_test_split, C, exclude_this_much, rand):
    fd_out = fds_out
    datalist, attributes, attribute_lines, attribute_map = load_and_encode_data(fd_list_in)
    
    X_train, Y_train, X_test, Y_test = make_train_test(datalist, attribute_map, train_test_split)
    outspec = fd_out, datalist, attribute_lines
    fd_out = learn_scaled(X_train, Y_train, X_test, Y_test, 1.0, rand, outspec)

def data_where_multiple(fd_list_in, fd_list_out, args):
    
    data, attributes, attribute_lines = load_data(fd_list_in, continue_reading=True)
    assert len(args) == 2
    all_these = args[0]
    any_these = args[1]

    all_ids = []
    for a in all_these:
        column, value = a
        if column not in attributes:
            raise Exception("column %s not available!" % column)
        column_id, column_values = attributes[column]
        if value not in column_values and column_values[0] != "continuous":
            raise Exception("invalid value %s for %s" % (value, column))
        all_ids.append((column_id, value))
    any_ids = []
    for a in any_these:
        column, value = a
        if column not in attributes:
            raise Exception("column %s not available!" % column)
        column_id, column_values = attributes[column]
        if value not in column_values and column_values[0] != "continuous":
            raise Exception("invalid value %s for %s" % (value, column))
        any_ids.append((column_id, value))

    filtered_list = []
    for d in data:
        d_in = True
        for column_id, value in all_ids:
            if d[column_id] != value:
                d_in = False
                break
        if not d_in:
            continue
        if len(any_ids) == 0:
            filtered_list.append(d)
        for column_id, value in any_ids:
            if d[column_id] == value:
                filtered_list.append(d)
                break
    write_data(fd_list_out, filtered_list, attribute_lines)
    
    
def data_where_multiple_2(fd_list_in, fd_list_out, args):
    
    data, attributes, attribute_lines = load_data(fd_list_in, continue_reading=True)
    assert len(args) == 2
    all_these = args[0]
    any_these = args[1]

    all_ids = []
    for a in all_these:
        column, value = a
        if column not in attributes:
            raise Exception("column %s not available!" % column)
        column_id, column_values = attributes[column]
        if value not in column_values and column_values[0] != "continuous":
            raise Exception("invalid value %s for %s" % (value, column))
        all_ids.append((column_id, value))
    any_ids = []
    for a in any_these:
        column, value = a
        if column not in attributes:
            raise Exception("column %s not available!" % column)
        column_id, column_values = attributes[column]
        any_ids.append((column_id, value))

    filtered_list = []
    for d in data:
        d_in = True
        for column_id, value in all_ids:
            if d[column_id] != value:
                d_in = False
                break
        if not d_in:
            continue
        if len(any_ids) == 0:
            filtered_list.append(d)
        for column_id, value in any_ids:
            if d[column_id] == value:
                filtered_list.append(d)
                break
    write_data(fd_list_out, filtered_list, attribute_lines)
    
def count_data(fd_list_in):
    data, attributes, attribute_lines = load_data(fd_list_in)
    count = len(data)
    return count
     
def fw_count(fd_in, fd_out, args):
    print("[LOG][fw_count] type(fd_in): ", type(fd_in))
    count = count_subset([fd_in], args)
    print("[LOG][fw_count] count: ", count)
    fd_out.write(str(count))
    
    
def fw_subset_selection(params, fds_in, fds_out, meta_data):
    
    if "column" in params and "value" in params:
        column = params['column']
        value = params['value']
        assert type(column) == str
        assert type(value) == str
        #further checks on validity done by data_where
        if "raw-data" in fds_in:        
            data_where(fds_in['raw-data'], [fds_out["output"]], [column, value])
        else:
            data_where(fds_in['input'], [fds_out["output"]], [column, value])

        return True, ""
    elif "all_these" in params and "any_these" in params:
        all_these = params["all_these"]
        any_these = params["any_these"]
        assert type(all_these) == list
        assert type(any_these) == list
        if len(all_these) > 0:
            c, v = all_these[0]
            assert type(c) == str
            assert type(v) == str
        if len(any_these) > 0:
            c, v = any_these[0]
            assert type(c) == str
            assert type(v) == str    
        if "raw-data" in fds_in:        
            data_where_multiple(fds_in["raw-data"], [fds_out["output"]], [all_these, any_these])
        else:
            data_where_multiple(fds_in["input"], [fds_out["output"]], [all_these, any_these])
        return True, ""

    else:
        raise Exception("parameters not found!")
        
def fw_lr_learn(params, fds_in, fds_out, meta_data):
    train_test_split = params['train_test_split']
    rand = params['rand']
    C = params['C']
    assert type(train_test_split) == float and 0 < train_test_split < 1
    assert type(rand) == int
    assert type(C) == float and C > 0 
    np.random.seed(rand)
    
    fds_out = fds_out["output"]
    logistic_regression_step([fds_in["input"]], fds_out, train_test_split, C, None, rand)
    return True, ""
