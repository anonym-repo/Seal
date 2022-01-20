from multiprocessing import Process, Pipe
import server.helper as hlp
from flask import redirect, url_for, request, render_template, flash, session
from server import server, db, bcrypt, state_machine
from server.forms import LoginForm, UpdateCapability
from server.models import User, StateMetadata, Action_capability
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
import os
import server.policy_manager as pm
import server.capability_manager as cm
import cProfile, pstats, io
from pstats import SortKey
from datetime import datetime
from termcolor import colored

@server.route('/', methods=['GET', 'POST'])
@server.route('/home', methods=['GET', 'POST'])
def home():
    pr = cProfile.Profile()
    pr.enable()
    if  current_user.is_authenticated:
        current_state = hlp.get_current_state()
        current_metadata = hlp.get_all_metadata()
        state_name = state_machine.get_state_name(int(current_state))
        
        
    if request.method == 'POST':
        try:
            ac.processRequest(request.form)
        except Exception as e:
            flash("there was an error in procesing of the request - "+ str(e) , 'danger')

        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        
        with open('./exe_m/profiler_output.txt', 'w') as f:
            f.write(colored("[LOG][Dispatcher][Time]]\n", 'red')+s.getvalue())
        return redirect(url_for('home'))
                  
    else:    
        
        if not  current_user.is_authenticated:
           return render_template('index.html', title = "home")

        actions = hlp.filter_actions_by_caps( state_machine.get_actions_at(current_state))
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        
        return render_template('index.html',
                               title = 'home',
                               current_state = current_state,
                               current_metadata = current_metadata,
                               state_name=state_name,
                               actions=actions)
    	
@server.route('/reset')
def reset():
    if current_user.is_authenticated:
        hlp.reset_state()
    
    return redirect(url_for('home'))


@server.route('/login', methods=['GET', 'POST'])
def login():
    
    if  current_user.is_authenticated:
        flash('You already logged in!', 'success')
        return redirect(url_for('home'))
    
    loginForm = LoginForm()
    
    if loginForm.validate_on_submit():
        user = User.query.filter_by(email=loginForm.email.data).first()
        if user and bcrypt.check_password_hash(user.password, loginForm.password.data):
            login_user(user, remember=loginForm.remember.data)
            flash('Welcome  ' + user.firstname + '!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
            
    return render_template("login.html", title='login', form=loginForm)

@server.route("/selectrawdata", methods=['GET', 'POST'])
def selectrawdata():
    
    if request.method == 'POST':
        selected_files = request.form.getlist('rawfiles')
        print(selected_files)   
        session['rawfiles'] = selected_files
        return redirect(url_for('home'))
    else: 
        fileList = hlp.select_raw_data('HIGH')
        return render_template("selectrawdata.html", title='Select Raw Data', files=fileList)

@server.route("/showdata")
def showdata():
    pr = cProfile.Profile()
    pr.enable()
    if not current_user.is_authenticated:
         flash('Please Login first', 'danger')
         return redirect(url_for('login'))
     
    current_state = hlp.get_current_state()
    content = ""
    if not current_state == 0:
        file_path = "output_files/id_" + str(current_user.id) + "_state_" + str(current_state) 
        with open(file_path, 'r') as f:
            content = f.read()
    else:
        flash('Raw data cannot be shown', 'danger')
    pr.disable()
    s = io.StringIO()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
        
    with open('./exe_m/fw_showdata_lr_1.txt', 'w') as f:
       f.write(colored("[LOG][Dispatcher][Time]]\n", 'red')+s.getvalue())   
    return  render_template("showdata.html", title='Show Data', text=content)

@server.route('/capmanage', methods=['GET', 'POST'])
@server.route("/capmanage")
def capmanage():
    child_caps = []
    try:
        if('cap_file' in session):
            child_caps = cm.get_child_caps(session['cap_file'])
            print(child_caps)
            if request.method == 'POST':
                 print("[LOG][capmange] ", request.form)
                 cm.revoke_capability(request.form.get('rev'))
                 return redirect(url_for('capmanage'))
            else:
                 pass
    except Exception as e:
            flash("there was an error in procesing of the request - "+ str(e) , 'danger')
   
           
    return  render_template("capmanage.html", title='Capability Management', c_caps = child_caps)

@server.route("/logout")
def logout():
    
    logout_user()
    session.clear()   
    return redirect(url_for('home'))


@server.route("/account", methods=['GET', 'POST'])
def account():
    
    capForm = UpdateCapability()
    if not current_user.is_authenticated:
         flash('Please Login first', 'danger')
         return redirect(url_for('login'))
     
    if capForm.validate_on_submit():
        cap = capForm.capability.data
        cap_filename = 'uploaded_cap' + str(current_user.id) + "_" + secure_filename(cap.filename)
        cap.save(os.path.join(server.config['CAP_FOLDER'], cap_filename))
        passed = cm.check_capability(cap_filename)
        
        if passed:
           flash('Your capabilities are updated successfully!', 'success')
        else:
           flash('Not a valid capability!', 'danger')			
        
        return redirect(url_for('account'))

    return render_template("account.html", title='account', form=capForm)
