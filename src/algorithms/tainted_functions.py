
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
    with T_method__('load_data', [fd_list, continue_reading]) as T:
        datalist = T([])
        attributes = T(dict())
        with T_scope__('if', 1, T) as T:
            if T_(type(fd_list) != list, T):
                fd_list = T([T(fd_list)])
        with T_scope__('for', 1, T) as T:
            for fd in T_(fd_list, T):
                try:
                    lines = T(fd.readlines())
                    print('---len(lines) is ', len(lines))
                    with T_scope__('if', 2, T) as T:
                        if T_(len(lines) == 0, T):
                            continue
                except:
                    print("except")
                    continue
                with T_scope__('for', 2, T) as T:
                    z= 1
                    for i in T_(range(len(lines)), T):
                        if i % 100000 == 0: 
                            #print("***************************\n", z, " - Passed 100000", " - ", i, "***************************\n")
                            z += 1
                        line = T(lines)[T(i)]
                        #if z >= 16 : print("---- ", line)
                        with T_scope__('if', 3, T) as T:
                            if T_(line[0] == '|', T):
                                break
                        entry = T(line.replace('\n', '').split(','))
                        with T_scope__('if', 4, T) as T:
                            if T_(len(entry) > 1, T):
                                T(datalist.append(entry))
                    print("========================= len(datalist) = ", len(datalist))
                with T_scope__('if', 5, T) as T:
                    #print("HERE 1")
                    if T_(len(attributes) == 0, T):
                        attribute_counter = T(0)
                        attribute_lines = T([])
                        #print("FOR -3")
                        with T_scope__('for', 3, T) as T:
                            for j in T_(range(i, len(lines)), T):
                                if j % 100000 == 0: print("Passed  - 1000000")
                                line = T(lines)[T(j)]
                                T(attribute_lines.append(line))
                                with T_scope__('if', 6, T) as T:
                                    if T_(line[0] == '|', T):
                                        continue
                                with T_scope__('if', 7, T) as T:
                                    if T_(':' not in line, T):
                                        continue
                                l = T(line.replace('.', '').replace('\n',
                                    '').split(': '))
                                column = T(l)[T(0)]
                                a = T(l)[T(1)]
                                a = T(a.split(', '))
                                attributes[column] = T((T(attribute_counter
                                    ), T(a)))
                                attribute_counter += T(1)
                with T_scope__('if', 8, T) as T:
                    if T_(not continue_reading, T):
                        print("BREAK")
                        break
                    else:
                        T(print('have read', len(datalist),
                            'entries, continuing...'))
        #print("END of loading")
        assert T(T(len(datalist)) > T(0)), T(
            'no data in any of the file descriptors!')
        return T((T(datalist), T(attributes), T(attribute_lines)))


def fw_user_function(data, send_end, do_sandboxing=True):
    with T_method__('fw_user_function', [data, send_end, do_sandboxing]) as T:
        with T_scope__('if', 1, T) as T:
            if T_(do_sandboxing, T):
                T(p.enter())
        sum = T(0)
        with T_scope__('for', 1, T) as T:
            for d in T_(data, T):
                T(print('----- ', d[7]))
                sum += T(int(d[0]))
        T(send_end.send(sum))


def fw_user_function_2(data, send_end, do_sandboxing=True):
    with T_method__('fw_user_function_2', [data, send_end, do_sandboxing]
        ) as T:
        with T_scope__('if', 1, T) as T:
            if T_(do_sandboxing, T):
                T(p.enter())
        sum = T(0)
        with T_scope__('for', 1, T) as T:
            for d in T_(data, T):
                dt = T(d)[T(7)]
                with T_scope__('if', 2, T) as T:
                    if T_(isinstance(dt, str), T):
                        dt = T(dt.strip())
                with T_scope__('if', 3, T) as T:
                    if T_(dt.isdigit(), T):
                        sum += T(int(dt))
        T(send_end.send(sum))


def user_function_3(data, send_end, do_sandboxing=True):
    with T_method__('fw_user_function_3', [data, send_end, do_sandboxing]
        ) as T:
        with T_scope__('if', 1, T) as T:
            if T_(do_sandboxing, T):
                T(p.enter())
        i = T(0)
        sum = T(0)
        with T_scope__('for', 1, T) as T:
            for d in T_(data, T):
                try:
                    dt = T(d)[T(3)]
                    with T_scope__('if', 2, T) as T:
                        if T_(isinstance(dt, str), T):
                            dt = T(dt.strip())
                    with T_scope__('if', 3, T) as T:
                        if T_(dt.isdigit(), T):
                            sum += T(int(dt))
                except T(Exception) as e:
                    T(print('[ERROR][exc] dt is = ', d))
        T(send_end.send(sum))


def write_data(fd_list, datalist, attribute_lines):
    with T_method__('write_data', [fd_list, datalist, attribute_lines]) as T:
        
        writethis = T('\n'.join([', '.join(data) for data in datalist]))
        writethis += T(''.join(attribute_lines))
        writethis += T('\n\n')
        with T_scope__('if', 1, T) as T:
            if T_(type(fd_list) == list, T):
                T(fd_list[0].write(writethis))
            else:
                T(fd_list.write(writethis))


def data_where(fd_list_in, fd_list_out, args):
    with T_method__('data_where', [fd_list_in, fd_list_out, args]) as T:
        data, attributes, attribute_lines = T(load_data(fd_list_in))
        assert T(T(len(args)) == T(2))
        column = T(args)[T(0)]
        value = T(args)[T(1)]
        with T_scope__('if', 1, T) as T:
            if T_(column not in attributes, T):
                raise T(Exception('column %s not available!' % column))
        column_id, column_values = T(attributes)[T(column)]
        with T_scope__('if', 2, T) as T:
            if T_(value not in column_values and column_values[0] !=
                'continuous', T):
                raise T(Exception('invalid value %s for %s' % (value, column)))
        filtered_list = T([])
        with T_scope__('for', 1, T) as T:
            for d in T_(data, T):
                with T_scope__('if', 3, T) as T:
                    if T_(d[column_id] == value, T):
                        T(filtered_list.append(d))
        T(write_data(fd_list_out, filtered_list, attribute_lines))


def convert_attributes(attribute_map, data_elem):
    with T_method__('convert_attributes', [attribute_map, data_elem]) as T:
        d_enc = T([])
        with T_scope__('for', 1, T) as T:
            for a_id in T_(range(len(data_elem) - 1), T):
                dea_id = T(data_elem)[T(a_id)]
                with T_scope__('if', 1, T) as T:
                    if T_(isinstance(a_id, str), T):
                        a_id = T(a_id.strip())
                dea_id = T(data_elem)[T(a_id)]
                with T_scope__('if', 2, T) as T:
                    if T_(isinstance(dea_id, str), T):
                        dea_id = T(dea_id.strip())
                with T_scope__('if', 3, T) as T:
                    if T_(dea_id == '?', T):
                        T(d_enc.append(float(0)))
                        continue
                with T_scope__('if', 4, T) as T:
                    if T_(a_id not in attribute_map, T):
                        T(d_enc.append(float(dea_id)))
                    else:
                        with T_scope__('if', 5, T) as T:
                            if T_(a_id in attribute_map and attribute_map[
                                a_id] is not None, T):
                                att = T(attribute_map)[T(a_id)]
                                with T_scope__('if', 6, T) as T:
                                    if T_(isinstance(dea_id, str), T):
                                        dea_id = T(dea_id.strip())
                                att = T(attribute_map)[T(a_id)][T(dea_id)]
                                with T_scope__('if', 7, T) as T:
                                    if T_(isinstance(att, str), T):
                                        att = T(att.strip())
                                T(d_enc.append(float(att)))
        return T(d_enc)


def make_train_test(datalist, attribute_map, train_factor):
    with T_method__('make_train_test', [datalist, attribute_map, train_factor]
        ) as T:
        X_all = T([])
        Y_all = T([])
        i = T(1)
        with T_scope__('for', 1, T) as T:
            for d in T_(datalist, T):
                d_enc = T(convert_attributes(attribute_map, d))
                with T_scope__('if', 1, T) as T:
                    if T_(len(d_enc) > 0, T):
                        T(X_all.append(np.array(d_enc)))
                        with T_scope__('if', 2, T) as T:
                            if T_(d[-1] == '<=50K', T):
                                T(Y_all.append(0))
                            else:
                                T(Y_all.append(1))
        X_all = T(np.array(X_all))
        Y_all = T(np.array(Y_all))
        ids = T([i for i in range(len(X_all))])
        T(np.random.shuffle(ids))
        with T_scope__('if', 3, T) as T:
            if T_(train_factor is not None, T):
                split = T(int(train_factor * len(X_all)))
                ids_train = T(ids)[:T(split)]
                ids_test = T(ids)[T(split):]
                return T((T(X_all)[T(ids_train)], T(Y_all)[T(ids_train)], T
                    (X_all)[T(ids_test)], T(Y_all)[T(ids_test)]))
            else:
                return T((T(None), T(None), T(X_all), T(Y_all)))


def learn(X_train, Y_train, X_test, Y_test, C, random_state, outspec):
    with T_method__('learn', [X_train, Y_train, X_test, Y_test, C,
        random_state, outspec]) as T:
        clf = T(LinearRegression(random_state=42, C=C))
        T(clf.fit(X_train, Y_train))
        acc = T(clf.score(X_test, Y_test))
        fd_out, datalist, attribute_lines, fd_model, fd_acc = T(outspec)
        T(write_data(fd_out, datalist, attribute_lines))
        T(pickle.dump(clf, fd_model))
        T(fd_acc.write(str(acc)))
        return T((T(fd_acc), T(fd_model), T(fd_out)))


def learn_scaled(X_train, Y_train, X_test, Y_test, C, random_state, outspec):
    with T_method__('learn_scaled', [X_train, Y_train, X_test, Y_test, C,
        random_state, outspec]) as T:
        scaler = T(preprocessing.StandardScaler().fit(X_train))
        clf = T(sklearn.linear_model.LogisticRegression(random_state=42, C=C))
        T(clf.fit(scaler.transform(X_train), Y_train))
        acc = T(clf.score(scaler.transform(X_test), Y_test))
        fd_out, datalist, attribute_lines = T(outspec)
        T(write_data(fd_out, datalist, attribute_lines))
        return T(fd_out)


def load_and_encode_data(fd_list_in):
    with T_method__('load_and_encode_data', [fd_list_in]) as T:
        datalist, attributes, attribute_lines = T(load_data(fd_list_in))
        attribute_map = T(dict())
        with T_scope__('for', 1, T) as T:
            for a in T_(attributes, T):
                a_id, values = T(attributes)[T(a)]
                with T_scope__('if', 1, T) as T:
                    if T_(values[0] == 'continuous', T):
                        continue
                with T_scope__('if', 2, T) as T:
                    if T_(isinstance(a_id, str), T):
                        a_id = T(a_id.strip())
                attribute_map[a_id] = T(dict())
                with T_scope__('for', 2, T) as T:
                    for i in T_(range(len(values)), T):
                        vs = T(values)[T(i)]
                        with T_scope__('if', 3, T) as T:
                            if T_(isinstance(vs, str), T):
                                vs = T(vs.strip())
                        attribute_map[a_id][vs] = T(float(i))
        return T((T(datalist), T(attributes), T(attribute_lines), T(
            attribute_map)))


def logistic_regression_step(fd_list_in, fds_out, train_test_split, C,
    exclude_this_much, rand):
    with T_method__('logistic_regression_step', [fd_list_in, fds_out,
        train_test_split, C, exclude_this_much, rand]) as T:
        fd_out = T(fds_out)
        datalist, attributes, attribute_lines, attribute_map = T(
            load_and_encode_data(fd_list_in))
        X_train, Y_train, X_test, Y_test = T(make_train_test(datalist,
            attribute_map, train_test_split))
        outspec = T((T(fd_out), T(datalist), T(attribute_lines)))
        fd_out = T(learn_scaled(X_train, Y_train, X_test, Y_test, 1.0, rand,
            outspec))


def data_where_multiple(fd_list_in, fd_list_out, args):
    with T_method__('data_where_multiple', [fd_list_in, fd_list_out, args]
        ) as T:
        #print("Go to load")
        data, attributes, attribute_lines = T(load_data(fd_list_in,
            continue_reading=True))
        #print("Loading is finished")
        assert len(args) == 2
        all_these = T(args)[T(0)]
        any_these = T(args)[T(1)]
        all_ids = T([])
        with T_scope__('for', 1, T) as T:
            for a in T_(all_these, T):
                column, value = T(a)
                with T_scope__('if', 1, T) as T:
                    if T_(column not in attributes, T):
                        raise T(Exception('column %s not available!' % column))
                column_id, column_values = T(attributes)[T(column)]
                with T_scope__('if', 2, T) as T:
                    if T_(value not in column_values and column_values[0] !=
                        'continuous', T):
                        raise T(Exception('invalid value %s for %s' % (
                            value, column)))
                T(all_ids.append((column_id, value)))
        any_ids = T([])
        with T_scope__('for', 2, T) as T:
            for a in T_(any_these, T):
                column, value = T(a)
                with T_scope__('if', 3, T) as T:
                    if T_(column not in attributes, T):
                        raise T(Exception('column %s not available!' % column))
                column_id, column_values = T(attributes)[T(column)]
                with T_scope__('if', 4, T) as T:
                    if T_(value not in column_values and column_values[0] !=
                        'continuous', T):
                        raise T(Exception('invalid value %s for %s' % (
                            value, column)))
                T(any_ids.append((column_id, value)))
        filtered_list = T([])
        with T_scope__('for', 3, T) as T:
            for d in T_(data, T):
                d_in = T(True)
                with T_scope__('for', 4, T) as T:
                    for column_id, value in T_(all_ids, T):
                        with T_scope__('if', 5, T) as T:
                            if T_(d[column_id] != value, T):
                                d_in = T(False)
                                break
                with T_scope__('if', 6, T) as T:
                    if T_(not d_in, T):
                        continue
                with T_scope__('if', 7, T) as T:
                    if T_(len(any_ids) == 0, T):
                        T(filtered_list.append(d))
                with T_scope__('for', 5, T) as T:
                    for column_id, value in T_(any_ids, T):
                        with T_scope__('if', 8, T) as T:
                            if T_(d[column_id] == value, T):
                                T(filtered_list.append(d))
                                break
        T(write_data(fd_list_out, filtered_list, attribute_lines))


def data_where_multiple_2(fd_list_in, fd_list_out, args):
    with T_method__('data_where_multiple_2', [fd_list_in, fd_list_out, args]
        ) as T:
        data, attributes, attribute_lines = T(load_data(fd_list_in,
            continue_reading=True))
        assert len(args) == 2
        all_these = T(args)[T(0)]
        any_these = T(args)[T(1)]
        all_ids = T([])
        with T_scope__('for', 1, T) as T:
            for a in T_(all_these, T):
                column, value = T(a)
                with T_scope__('if', 1, T) as T:
                    if T_(column not in attributes, T):
                        raise T(Exception('column %s not available!' % column))
                column_id, column_values = T(attributes)[T(column)]
                with T_scope__('if', 2, T) as T:
                    if T_(value not in column_values and column_values[0] !=
                        'continuous', T):
                        raise T(Exception('invalid value %s for %s' % (
                            value, column)))
                T(all_ids.append((column_id, value)))
        any_ids = T([])
        with T_scope__('for', 2, T) as T:
            for a in T_(any_these, T):
                column, value = T(a)
                with T_scope__('if', 3, T) as T:
                    if T_(column not in attributes, T):
                        raise T(Exception('column %s not available!' % column))
                column_id, column_values = T(attributes)[T(column)]
                T(any_ids.append((column_id, value)))
        filtered_list = T([])
        with T_scope__('for', 3, T) as T:
            for d in T_(data, T):
                d_in = T(True)
                with T_scope__('for', 4, T) as T:
                    for column_id, value in T_(all_ids, T):
                        with T_scope__('if', 4, T) as T:
                            if T_(d[column_id] != value, T):
                                d_in = T(False)
                                break
                with T_scope__('if', 5, T) as T:
                    if T_(not d_in, T):
                        continue
                with T_scope__('if', 6, T) as T:
                    if T_(len(any_ids) == 0, T):
                        T(filtered_list.append(d))
                with T_scope__('for', 5, T) as T:
                    for column_id, value in T_(any_ids, T):
                        with T_scope__('if', 7, T) as T:
                            if T_(d[column_id] == value, T):
                                T(filtered_list.append(d))
                                break
        T(write_data(fd_list_out, filtered_list, attribute_lines))


def count_data(fd_list_in):
    with T_method__('count_data', [fd_list_in]) as T:
        data, attributes, attribute_lines = T(load_data(fd_list_in))
        count = T(len(data))
        return T(count)


def count(fd_in, fd_out, args):
    with T_method__('fw_count', [fd_in, fd_out, args]) as T:
        T(print('[LOG][fw_count] type(fd_in): ', type(fd_in)))
        count = T(count_subset([fd_in], args))
        T(print('[LOG][fw_count] count: ', count))
        T(fd_out.write(str(count)))


def subset_selection(params, fds_in, fds_out, meta_data):
    with T_method__('fw_subset_selection', [params, fds_in, fds_out, meta_data]
        ) as T:
        with T_scope__('if', 1, T) as T:
            if T_('column' in params and 'value' in params, T):
                column = T(params)[T('column')]
                value = T(params)[T('value')]
                assert T(T(type(column)) == T(str))
                assert T(T(type(value)) == T(str))
                with T_scope__('if', 2, T) as T:
                    if T_('raw-data' in fds_in, T):
                        T(data_where(fds_in['raw-data'], [fds_out['output']
                            ], [column, value]))
                    else:
                        T(data_where(fds_in['input'], [fds_out['output']],
                            [column, value]))
                return True, ""
            else:
                with T_scope__('if', 3, T) as T:
                    if T_('all_these' in params and 'any_these' in params, T):
                        all_these = T(params)[T('all_these')]
                        any_these = T(params)[T('any_these')]
                        assert T(T(type(all_these)) == T(list))
                        assert T(T(type(any_these)) == T(list))
                        with T_scope__('if', 4, T) as T:
                            if T_(len(all_these) > 0, T):
                                c, v = T(all_these)[T(0)]
                                assert T(T(type(c)) == T(str))
                                assert T(T(type(v)) == T(str))
                        with T_scope__('if', 5, T) as T:
                            if T_(len(any_these) > 0, T):
                                c, v = T(any_these)[T(0)]
                                assert T(T(type(c)) == T(str))
                                assert T(T(type(v)) == T(str))
                        with T_scope__('if', 6, T) as T:
                            if T_('raw-data' in fds_in, T):
                                T(data_where_multiple(fds_in['raw-data'], [
                                    fds_out['output']], [all_these, any_these])
                                    )
                            else:
                                T(data_where_multiple(fds_in['input'], [
                                    fds_out['output']], [all_these, any_these])
                                    )
                        return True, ""
                    else:
                        raise T(Exception('parameters not found!'))


def lr_learn(params, fds_in, fds_out, meta_data):
    with T_method__('fw_lr_learn', [params, fds_in, fds_out, meta_data]) as T:
        train_test_split = T(params)[T('train_test_split')]
        rand = T(params)[T('rand')]
        C = T(params)[T('C')]
        assert T(T(T(type(train_test_split)) == T(float)) and T(T(0) < T(
            train_test_split) < T(1)))
        assert T(T(type(rand)) == T(int))
        assert T(T(T(type(C)) == T(float)) and T(T(C) > T(0)))
        T(np.random.seed(rand))
        T(print('C', C))
        fds_out = T(fds_out)[T('output')]
        T(logistic_regression_step([fds_in['input']], fds_out,
            train_test_split, C, None, rand))
        return True, ""
