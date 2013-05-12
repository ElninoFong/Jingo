# -*- coding: utf-8 -*-

from __future__ import with_statement
import time
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
	 render_template, abort, g, flash
from werkzeug import check_password_hash, generate_password_hash
import MySQLdb as mdb


# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
	return mdb.connect('127.0.0.1', 'root', 'root', 
		'Jingo_DB', port=8889);


def query_db(query, args=(), one=False):
	"""Queries the database and returns a list of dictionaries."""
	cur = g.db.cursor()
	cur.execute(query, args)
	rv = cur.fetchall()
	return (rv[0] if rv else None) if one else rv


def findpassword(username):
	cur = g.db.cursor()
	query = "select password from USER where username = %s"
	#flash(query)
	cur.execute(query, (username,))
	results = [row[0] for row in cur.fetchall()]
	return results


@app.before_request
def before_request():
	g.db = connect_db()
	g.user = None
	if 'username' in session:
		g.user = query_db('select uid from USER where username = %s',
						  [session['username']], one=True)
		g.state = query_db('select state_name from STATE where uid = %s',
						  g.user)
		# flash(g.state)


@app.teardown_request
def teardown_request(exception):
	g.db.close()


def format_datetime(timestamp):
	"""Format a timestamp for display."""
	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
	"""Return the gravatar image for the given email address."""
	return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
		(md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.route('/')
def timeline():
	"""Shows a users timeline or if no user is logged in it will
	redirect to the public timeline.  This timeline shows the user's
	messages as well as all the messages of followed users.
	"""
	if not g.user:
		return redirect(url_for('public_timeline'))

	return render_template('timeline.html')


@app.route('/public')
def public_timeline():
	"""Displays the latest messages of all users."""
	return render_template('timeline.html')


@app.route('/add_message', methods=['POST'])
def add_message():
	"""Registers a new message for the user."""
	if 'user_id' not in session:
		abort(401)
	# if request.form['text']:
	#     db = get_db()
	#     db.execute('''insert into message (author_id, text, pub_date)
	#       values (?, ?, ?)''', (session['user_id'], request.form['text'],
	#                             int(time.time())))
	#     db.commit()
	#     flash('Your message was recorded')
	return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	"""Logs the user in."""
	if g.user:
		return redirect(url_for('timeline'))
	error = None
	if request.method == 'POST':
		cur = g.db.cursor()
		query = "select username from USER" 
	  #flash(query)
		cur.execute(query)
		results = [row[0] for row in cur.fetchall()]
	if request.form['username'] not in results:
		error = 'Invalid username'
	elif request.form['password'] not in findpassword(request.form['username']):
		error = 'Invalid password'
	else:
		session['username'] = request.form['username']
		flash('You were logged in')
		return redirect(url_for('timeline'))
	return render_template('login.html', error=error)
   

@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers the user."""
	if g.user:
		return redirect(url_for('timeline'))
	error = None
	if request.method == 'POST':
		if not request.form['username']:
			error = 'You have to enter a username'
		elif not request.form['email'] or \
				 '@' not in request.form['email']:
			error = 'You have to enter a valid email address'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else:
			cur = g.db.cursor()
			query = "INSERT INTO USER (`uid`, `username`, `password`, `last_name`, `first_name`, `gender`, `created_at`, `last_location_id`, `email`) VALUES (NULL, %s, %s ,NULL, NULL, NULL, CURRENT_TIMESTAMP, NULL, %s)"
			cur.execute(query, (request.form['username'],generate_password_hash(request.form['password'],request.form['email'])))
			g.db.commit()
			flash('You were successfully registered and can login now')
			return redirect(url_for('login'))
	return render_template('register.html', error=error)
	
	
	
@app.route('/profile',methods=['GET', 'POST'])
def profile():
	if 'user_id' not in session:
		abort(401)
	if request.method == 'POST':
		cur = g.db.cursor()
		query = "UPDATE  `Jingo_DB`.`USER` SET  `last_name` = %s,first_name = %s, email = %s , gender = %s WHERE  username = %s"
		# flash(query)
		cur.execute(query, (request.form['lname'],request.form['fname'],request.form['email'],request.form['gender'],session['username']))
		g.db.commit()
		cur = g.db.cursor()
		query = "select first_name,last_name,gender,email from  USER WHERE username = %s"
		# flash(query)
		cur.execute(query, session['username'])
	else:  
		cur = g.db.cursor()
		query = "select first_name,last_name,gender,email from  USER WHERE username = %s"
		#flash(query)
		cur.execute(query, session['username'])
	results = [row[:] for row in cur.fetchall()]
	return render_template('profile.html',results = results)
	
	
@app.route('/friends',methods=['GET', 'POST'])
def friends():
	if 'user_id' not in session:
		abort(401)
	cur = g.db.cursor()
	query = "SELECT U1.username,F.request_time \
	FROM FRIENDSHIP AS F JOIN USER AS U1 JOIN USER AS U2 \
	WHERE  F.from_uid=U1.uid and F.to_uid=U2.uid and F.response_status=0 and U2.username= %s"
	#flash(query)
	cur.execute(query, session['username'])
	results3 = [row[:] for row in cur.fetchall()]
	
	if request.method == 'POST':      
		cur = g.db.cursor()
		query = "SELECT U2.username FROM FRIENDSHIP as F join USER AS U1 join USER AS U2 WHERE F.from_uid = U1.uid and F.to_uid = U2.uid and U1.username = '%s' \
		 and  F.response_status=1 UNION (SELECT U1.username FROM FRIENDSHIP as F join USER AS U1 join USER AS U2 WHERE F.from_uid = U1.uid and F.to_uid = U2.uid and U2.username = '%s'  and  F.response_status=1) " % (session['username'],session['username'])
		#flash(query)
		cur.execute(query)
		results = [row[0] for row in cur.fetchall()]        
		cur = g.db.cursor()
		query = "select username from USER \
		where username LIKE '%%%s%%' \
		and username NOT IN (SELECT U2.username \
		FROM FRIENDSHIP as F join USER AS U1 join USER AS U2 \
		WHERE F.from_uid = U1.uid and F.to_uid = U2.uid \
		and U1.username = '%s'  and  F.response_status=1 \
		UNION\
		(SELECT U1.username\
		FROM FRIENDSHIP as F join USER AS U1 join USER AS U2	 \
		WHERE F.from_uid = U1.uid and F.to_uid = U2.uid \
		and U2.username = '%s'  and  F.response_status=1))" % (request.form['search'],session['username'],session['username'])
		#flash(query)
		cur.execute(query)
		results1 = [row[0] for row in cur.fetchall()]       
		return render_template('friends.html',results = results,results1 = results1,results3= results3 )
	else:
		cur = g.db.cursor()
		query = "SELECT U2.username FROM FRIENDSHIP as F join USER AS U1 join USER AS U2 WHERE F.from_uid = U1.uid and F.to_uid = U2.uid and U1.username = '%s'  and  F.response_status=1 UNION (SELECT U1.username FROM FRIENDSHIP as F join USER AS U1 join USER AS U2 WHERE F.from_uid = U1.uid and F.to_uid = U2.uid and U2.username = '%s'  and  F.response_status=1) " % (session['username'],session['username'])
		#flash(query)
		cur.execute(query)
		results = [row[0] for row in cur.fetchall()]
		return render_template('friends.html',results = results,results3= results3)
	


@app.route('/<username>')
def user_timeline(username):
	profile_user = query_db('select uid from USER where username = %s',
							[username], one=True)
	if profile_user is None:
		abort(404)
	cur = g.db.cursor()
	query = "SELECT username,words,N.created_at \
	FROM NOTE AS N JOIN USER AS U \
	WHERE N.uid=U.uid and username = '%s'" % username
	# flash(query)
	cur.execute(query)
	results = [row[:] for row in cur.fetchall()]
	
	return render_template('timeline.html',results=results, 
		profile_user=profile_user, profile_username=username)


@app.route('/friendsreq/<uname>')
def friendsreq(uname):
	if not g.user:
		abort(401)
	flash('Friend Request Sent.')
	cur = g.db.cursor()
	query = "INSERT INTO `Jingo_DB`.`FRIENDSHIP` (`from_uid`, `to_uid`, `request_time`, `response_time`, `response_status`) VALUES ((select uid from USER where username = '%s'), (select uid from USER where username = '%s'), CURRENT_TIMESTAMP, '0000-00-00 00:00:00', '0')" % (session['username'],uname)
	cur.execute(query)
	g.db.commit()
	
	return redirect(url_for('friends'))


@app.route('/rejectreq/<uname>')
def rejectreq(uname):
	if not g.user:
		abort(401)
	flash('Rejected the Friend Request.')
	cur = g.db.cursor()
	query = "update FRIENDSHIP SET RESPONSE_STATUS = 2 \
	WHERE from_uid = (SELECT  uid FROM USER 	 WHERE username = '%s' )" % uname
	flash(query)
	cur.execute(query)
	g.db.commit()
	return redirect(url_for('friends'))
	
@app.route('/agreereq/<uname>')
def agreereq(uname):
	if not g.user:
		abort(401)
	flash('Friend Request Accepted.')
	cur = g.db.cursor()
	query = "update FRIENDSHIP SET RESPONSE_STATUS = 1 \
	WHERE from_uid = (SELECT  uid FROM USER 	 WHERE username = '%s' )" % uname
	flash(query)
	cur.execute(query)
	g.db.commit()
	return redirect(url_for('friends'))



@app.route('/logout')
def logout():
	"""Logs the user out."""
	session.pop('username', None)
	flash('You were logged out')
	return redirect(url_for('timeline'))

# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url


if __name__ == '__main__':
	app.run()
