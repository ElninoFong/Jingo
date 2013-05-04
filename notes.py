from flask import Flask, render_template, g, flash, request, redirect, url_for
import MySQLdb as mdb
from datetime import datetime

SECRET_KEY = 'development key'
app = Flask(__name__)
app.config.from_object(__name__)

user = {'uid': 1,
		'username': 'James',
		'email': 'James@gmail.com',
		'profile_id': 6,
		'last_loc_name': 'soho',
		'state_id': 2,
		'state_name': 'at work'}

state = {'at work',
		 'lunch break',
		 'just chilling'}

dayofweek = [{'day': 'Monday', 'id': 0},
			 {'day': 'Tuesday', 'id': 1},
			 {'day': 'Wednesday', 'id': 2},
			 {'day': 'Thursday', 'id': 3},
			 {'day': 'Friday', 'id': 4},
			 {'day': 'Saturday', 'id': 5},
			 {'day': 'Sunday', 'id': 6}]

repeat = [{'type': 'Never', 'id': 0},
		  {'type': 'Every Day', 'id': 1},
		  {'type': 'Every Week', 'id': 2}]

def connect_db():
	return mdb.connect('127.0.0.1', 'root', 'root', 
		'Jingo_DB', port=8889);

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	g.db.close()

@app.route('/show_all_notes')
def show_all_notes():
	cur = g.db.cursor()
	query_field = "SHOW FIELDS FROM NOTE"
	query_data = "SELECT * FROM NOTE"
	flash(query_data)
	cur.execute(query_field)
	fields = [row[0] for row in cur.fetchall()]
	cur.execute(query_data)
	results = [row for row in cur.fetchall()]
	return render_template('show_notes.html',
		title = 'Show All Notes',
		table = 'NOTES',
		fields = fields,
		results = results)

@app.route('/write_notes', methods=['GET', 'POST'])
def write_notes():
	if request.method == 'POST':
		if request.form['words']:
			cur = g.db.cursor()
			query_add = "INSERT INTO NOTE (uid, words) VALUES (%s, %s)"
			cur.execute(query_add, (user['uid'], request.form['words']))
			g.db.commit()
			# flash(request.form['words'])
			flash("Write a new note.")
			return redirect(url_for("show_all_notes"))
		else:
			flash("Invalid input.")
	return render_template('write_notes.html',
		user = user,
		dayofweek = dayofweek,
		repeat = repeat)

@app.route('/recieve_notes')
def recieve_notes():
	cur = g.db.cursor()
	query_field = "SHOW FIELDS FROM NOTE"
	query_rec = "CALL recnotesproc (%s, %s, %s)"
	cur.execute(query_field)
	fields = [row[0] for row in cur.fetchall()]
	cur.execute(query_rec, (user['uid'], user['state_id'], user['last_loc_name']))
	results = [row for row in cur.fetchall()]
	flash(user['username'] + " in " + user['last_loc_name'] + " at " + str(datetime.now()) + " recieve following notes.")
	return render_template('show_notes.html',
		title = 'Show Recieve Notes',
		table = 'NOTES',
		fields = fields,
		results = results)

@app.route('/my_notes')
def my_notes():
	cur = g.db.cursor()
	query_field = "SHOW FIELDS FROM NOTE"
	query_my = "SELECT * FROM NOTE WHERE uid = %s"
	cur.execute(query_field)
	fields = [row[0] for row in cur.fetchall()]
	cur.execute(query_my, (user['uid']))
	results = [row for row in cur.fetchall()]
	flash(user['username'] + " published following notes.")
	return render_template('show_notes.html',
		title = 'Show My Notes',
		table = 'NOTES',
		fields = fields,
		results = results)

@app.route('/filter', methods=['GET', 'POST'])
def filter():
	if request.method == 'POST':
		if request.form['newstate'] != '':
			if request.form['newstate'] not in state:
				state.append(request.form['newstate'])
				user['state_name'] = request.form['newstate']
				flash("Add a New State")
			else: 
				user['state_name'] = request.form['newstate']
				flash("State Changed")
		elif request.form['selstate'] != '':
			user['state_name'] = request.form['selstate']
			flash("State Changed")
		else:
			flash("Nothing Change")
	return render_template('filter.html',
		user = user,
		state = state)

@app.route('/test')
def test():
	return render_template('test.html')