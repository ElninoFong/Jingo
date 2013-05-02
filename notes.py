from flask import Flask, render_template, g, flash, request, redirect, url_for
import MySQLdb as mdb
from datetime import datetime

SECRET_KEY = 'development key'
app = Flask(__name__)
app.config.from_object(__name__)

user = {'uid': 2,
		'username': 'James',
		'email': 'James@gmail.com',
		'profile_id': 6,
		'last_loc_name': 'soho',
		'state_id': 2}

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
			query_add = "INSERT INTO NOTE (words) VALUES (%s)"
			cur.execute(query_add, request.form['words'])
			g.db.commit()
			# flash(request.form['words'])
			flash("Write a new note.")
			return redirect(url_for("show_all_notes"))
		else:
			flash("Invalid input.")
	return render_template('write_notes.html')

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