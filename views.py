from flask import Flask, render_template, g, flash, request, \
	 redirect, url_for, abort, session
import MySQLdb as mdb
from hashlib import md5
from datetime import datetime
from dbprocess import dbprocess
from config import state, dayofweek, repeat, tags, PER_PAGE
from werkzeug import check_password_hash, generate_password_hash
import re

app = Flask(__name__)
app.config.from_object('config')
process = dbprocess()


def connect_db():
	return mdb.connect('127.0.0.1', 'root', 'root', 'Jingo_DB', port=8889)


@app.before_request
def before_request():
	g.db = connect_db()
	g.uid = None
	g.locid = None
	g.stateid = None
	g.state = None
	if 'username' in session:
		res = query_db('SELECT uid, last_location_id, last_state_id FROM USER WHERE username = %s',
						  [session['username']], one=True)
		g.uid, g.locid, g.stateid = res
	if g.stateid:
		res = query_db('SELECT state_name FROM STATE WHERE state_id = %s AND uid = %s',
							[g.stateid, g.uid], one=True)
		g.state = res[0]

		
@app.teardown_request
def teardown_request(exception):
	g.db.close()


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
	return results[0]

def get_user_id(username):
	"""Convenience method to look up the id for a username."""
	rv = query_db('select uid from USER where username = %s',
				  [username], one=True)
	return rv[0] if rv else None


# def format_datetime(timestamp):
# 	"""Format a timestamp for display."""
# 	return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
	"""Return the gravatar image for the given email address."""
	return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
		(md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.route('/', methods=['GET','POST'])
def timeline():
	"""Shows a users timeline or if no user is logged in it will
	redirect to the public timeline.  This timeline shows the user's
	messages as well as all the messages of followed users.
	"""
	if not g.uid:
		return redirect(url_for('public_timeline'))

	cur = g.db.cursor()
	if request.method == 'POST':
		if g.stateid:
			query_rec = "CALL recnotesproc (%s, %s, %s, %s)"
			# curlocid = g.locid
			# curlocname = user['last_loc_name']
			curdatetime = str(datetime.now().replace(second=0, microsecond=0))
			if request.form['curdatetime']:
				curdatetime = str(request.form['curdatetime'])
			curlocid = process.get_location_id(request.form['curloc'])
			process.update_loc(g.uid, curlocid)
			g.locid = curlocid
			# curlocname = re.split('; |, ', request.form['curloc'])[0]
			cur.execute(query_rec, (g.stateid, curlocid, curdatetime, PER_PAGE))
			results = cur.fetchall()
		else:
			flash("Please set your state first.")
			results = []
	else:
		if not g.stateid or not g.locid:
			flash("Please set your state and location first.")
			results = []
		else:
			query_rec = "CALL recnotesproc (%s, %s, %s, %s)"
			curdatetime = str(datetime.now().replace(second=0, microsecond=0))
			cur.execute(query_rec, (g.stateid, g.locid, curdatetime, PER_PAGE))
			results = cur.fetchall()

	messages=[]
	for res in results:
		messages.append({'email': res[0], 'username': res[1], 'words': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M'), 'noteid': res[4]})
	return render_template('timeline.html',
		state = state,
		messages=messages)


@app.route('/public')
def public_timeline():
	"""Displays the latest messages of all users."""
	form_content = {'words': '',
					'startdatetime': '',
					'enddatetime': '',
					'starttime': '',
					'endtime': '',
					'radius': 500,
					'selecttag': '',
					'addtag': ''}
	cur = g.db.cursor()
	query_data = "SELECT email, username, words, NOTE.created_at, note_id FROM NOTE, USER WHERE NOTE.uid = USER.uid \
		ORDER BY NOTE.created_at DESC LIMIT %s"
	cur.execute(query_data, (PER_PAGE,))
	results = cur.fetchall()
	messages=[]
	for res in results:
		messages.append({'email': res[0], 'username': res[1], 'words': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M'), 'noteid': res[4]})
	return render_template('timeline.html',
		dayofweek = dayofweek,
		repeat = repeat,
		tags = tags,
		form_content = form_content,
		messages=messages)


@app.route('/login', methods=['GET', 'POST'])
def login():
	"""Logs the user in."""
	if g.uid:
		return redirect(url_for('public_timeline'))
	error = None
	if request.method == 'POST':
		cur = g.db.cursor()
		query = "select username from USER" 
		#flash(query)
		cur.execute(query)
		results = [row[0] for row in cur.fetchall()]
		if request.form['username'] not in results:
			error = 'Invalid username'
		elif not check_password_hash(findpassword(request.form['username']), request.form['password']):
			error = 'Invalid password'
		else:
			session['username'] = request.form['username']
			flash('You were logged in')
			return redirect(url_for('public_timeline'))
	return render_template('login.html', error=error)
   

@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Registers the user."""
	if g.uid:
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
			cur.execute(query, (request.form['username'],generate_password_hash(request.form['password']),request.form['email']))
			g.db.commit()
			flash('You were successfully registered and can login now')
			return redirect(url_for('login'))
	return render_template('register.html', error=error)
	
	
	
@app.route('/profile',methods=['GET', 'POST'])
def profile():
	if not g.uid:
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
	if not g.uid:
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
		and uid <> %s \
		and username NOT IN (SELECT U2.username \
		FROM FRIENDSHIP as F join USER AS U1 join USER AS U2 \
		WHERE F.from_uid = U1.uid and F.to_uid = U2.uid \
		and U1.username = '%s'  and  F.response_status=1 \
		UNION\
		(SELECT U1.username\
		FROM FRIENDSHIP as F join USER AS U1 join USER AS U2     \
		WHERE F.from_uid = U1.uid and F.to_uid = U2.uid \
		and U2.username = '%s'  and  F.response_status=1))" % (request.form['search'], g.uid, session['username'],session['username'])
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
	
@app.route('/comment?<noteid>', methods=['GET', 'POST'])
def comment(noteid):
	if not g.uid:
		flash("Please sign in first.")
		return redirect(url_for('login'))
	if request.method == 'POST':
		if request.form['comment_text']:
			cur = g.db.cursor()
			query_add_comment = "INSERT INTO COMMENT (uid, note_id, content) \
				VALUES (%s, %s, %s)"
			cur.execute(query_add_comment, (g.uid, noteid, request.form['comment_text']))
			g.db.commit()
			flash("Commented a note.")
		else:
			flash("Please write something.")
	cur = g.db.cursor()
	query_data = "SELECT email, username, words, NOTE.created_at, note_id FROM NOTE, USER WHERE NOTE.uid = USER.uid \
		AND note_id = %s"
	cur.execute(query_data, (noteid))
	results = cur.fetchall()
	messages=[]
	for res in results:
		messages.append({'email': res[0], 'username': res[1], 'words': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M'), 'noteid': res[4]})

	query_data = "SELECT email, username, content, COMMENT.created_at FROM COMMENT, USER WHERE COMMENT.uid = USER.uid \
		AND note_id = %s ORDER BY COMMENT.created_at DESC LIMIT %s"
	cur.execute(query_data, (noteid, PER_PAGE,))
	results = cur.fetchall()
	comments=[]
	for res in results:
		comments.append({'email': res[0], 'username': res[1], 'content': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M')})
	return render_template('comment.html',
		 messages = messages,
		 comments = comments,
		 noteid = noteid)

@app.route('/popular?<noteid>')
def popular(noteid):
	if not g.uid:
		flash("Please sign in first.")
		return redirect(url_for('login'))
	cur = g.db.cursor()
	if noteid != '-1': # noteid=-1 means press the 'popular' tag
		query = "SELECT * FROM `Jingo_DB`.`LIKE` WHERE uid = %s AND note_id = %s"
		cur.execute(query, (g.uid, noteid))
		results = cur.fetchall()
		if results:
			flash("You already liked this note before.")
		else:
			query = "INSERT INTO `Jingo_DB`.`LIKE` (uid, note_id) VALUES (%s, %s)"
			cur.execute(query, (g.uid, noteid))
			g.db.commit()
			flash("You liked this note, like + 1.")

	query_data = "SELECT DISTINCT USER.email, USER.username, NOTE.words, NOTE.created_at, NOTE.note_id, COUNT(L.like_id) AS cnt FROM USER, NOTE LEFT JOIN `Jingo_DB`.`LIKE` AS L ON L.note_id = NOTE.note_id \
		WHERE NOTE.uid = USER.uid GROUP BY USER.email, USER.username, NOTE.words, NOTE.created_at, NOTE.note_id ORDER BY cnt DESC, NOTE.created_at DESC LIMIT %s"
	cur.execute(query_data, (PER_PAGE))
	results = cur.fetchall()
	messages=[]
	for res in results:
		messages.append({'email': res[0], 'username': res[1], 'words': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M'), 'noteid': res[4], 'cnt': res[5]})
	return render_template('popular.html', messages = messages)

@app.route('/<username>')
def user_timeline(username):
	profile_user = query_db('select uid from USER where username = %s',
							[username], one=True)
	if profile_user is None:
		abort(404)
	cur = g.db.cursor()
	query_data = "SELECT email, username, words, NOTE.created_at, note_id FROM NOTE, USER WHERE NOTE.uid = USER.uid \
		AND username = %s ORDER BY NOTE.created_at DESC LIMIT %s"
	cur.execute(query_data, (username, PER_PAGE))
	results = cur.fetchall()
	messages=[]
	for res in results:
		messages.append({'email': res[0], 'username': res[1], 'words': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M'), 'noteid': res[4]})
	return render_template('timeline.html', messages=messages,
		profile_user=profile_user, profile_username=username)


@app.route('/friendsreq/<uname>')
def friendsreq(uname):
	if not g.uid:
		abort(401)
	flash('Friend Request Sent.')
	cur = g.db.cursor()
	query = "SELECT * FROM FRIENDSHIP WHERE from_uid = %s AND to_uid = (select uid from USER where username = %s)"
	cur.execute(query, (g.uid, uname))
	res = cur.fetchall()
	if not res:
		query = "INSERT INTO `Jingo_DB`.`FRIENDSHIP` (`from_uid`, `to_uid`, `request_time`, `response_time`, `response_status`) \
		 VALUES ((select uid from USER where username = '%s'), (select uid from USER where username = '%s'), CURRENT_TIMESTAMP, '0000-00-00 00:00:00', '0')" % (session['username'],uname)
		cur.execute(query)
		g.db.commit()
	
	return redirect(url_for('friends'))


@app.route('/rejectreq/<uname>')
def rejectreq(uname):
	if not g.uid:
		abort(401)
	flash('Rejected the Friend Request.')
	cur = g.db.cursor()
	query = "DELETE FROM FRIENDSHIP WHERE from_uid = \
		(SELECT  uid FROM USER      WHERE username = '%s' )" % uname
	# flash(query)
	cur.execute(query)
	g.db.commit()
	return redirect(url_for('friends'))
	
@app.route('/agreereq/<uname>')
def agreereq(uname):
	if not g.uid:
		abort(401)
	flash('Friend Request Accepted.')
	cur = g.db.cursor()
	query = "update FRIENDSHIP SET RESPONSE_STATUS = 1 \
	WHERE from_uid = (SELECT  uid FROM USER      WHERE username = '%s' )" % uname
	# flash(query)
	cur.execute(query)
	g.db.commit()
	return redirect(url_for('friends'))



@app.route('/logout')
def logout():
	"""Logs the user out."""
	session.pop('username', None)
	flash('You were logged out')
	return redirect(url_for('timeline'))


@app.route('/write_notes', methods=['POST'])
def write_notes():
	if not g.uid:
		abort(401)
	form_content = {'words': '',
					'startdatetime': '',
					'enddatetime': '',
					'starttime': '',
					'endtime': '',
					'radius': 500,
					'selecttag': '',
					'addtag': ''}
	if request.method == 'POST':
		if 'shareBtn' in request.form:
			if not request.form['words']:
				flash("Please input some words.")
			elif not request.form['loc']:
				form_content['words'] = request.form['words']
				flash("Location is required.")
			elif not ((request.form['startdatetime'] and request.form['enddatetime']) or (request.form['starttime'] and request.form['endtime'])):
				form_content['words'] = request.form['words']
				flash("Schedule is required.")
			elif not (request.form['jquery-tagbox-select'] or request.form['jquery-tagbox-text']):
				form_content['words'] = request.form['words']
				flash("Tag is required.")
			else:
				selecttag = request.form['jquery-tagbox-select'].split(',')
				addtag = request.form['jquery-tagbox-text'].split(',')
				loc_id = process.get_location_id(loc=request.form['loc'])
				process.update_loc(g.uid, loc_id)
				schedule_id = process.get_schedule_id(repeat=request.form['repeat_sel'], startdatetime=request.form['startdatetime'],
													  enddatetime=request.form['enddatetime'], starttime=request.form['starttime'], 
													  endtime=request.form['endtime'], dow=request.form['dow_sel'])
				process.insert_note(uid=g.uid, words=request.form['words'], link=request.form['link'], loc_id=loc_id, 
									radius=request.form['radius'], schedule_id=schedule_id, selecttag=selecttag, addtag=addtag)
				flash('Your note was recorded')
				# return redirect(url_for('timeline'))
		elif 'searchBtn' in request.form:
			if request.form['search']:
				cur = g.db.cursor()
				query_data = "SELECT email, username, words, NOTE.created_at, note_id FROM NOTE, USER WHERE NOTE.uid = USER.uid \
					AND words LIKE %s ORDER BY NOTE.created_at DESC LIMIT %s"
				cur.execute(query_data, (("%" + request.form['search'] + "%"), PER_PAGE,))
				results = cur.fetchall()
				messages=[]
				for res in results:
					messages.append({'email': res[0], 'username': res[1], 'words': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M'), 'noteid': res[4]})
				return render_template('timeline.html',
					dayofweek = dayofweek,
					repeat = repeat,
					tags = tags,
					form_content = form_content,
					messages=messages)
			else:
				flash("Empty search.")
	cur = g.db.cursor()
	query_data = "SELECT email, username, words, NOTE.created_at, note_id FROM NOTE, USER WHERE NOTE.uid = USER.uid \
		ORDER BY NOTE.created_at DESC LIMIT %s"
	cur.execute(query_data, (PER_PAGE,))
	results = cur.fetchall()
	messages=[]
	for res in results:
		messages.append({'email': res[0], 'username': res[1], 'words': res[2], 'created_at': res[3].strftime('%Y-%m-%d @ %H:%M'), 'noteid': res[4]})
	return render_template('timeline.html',
		dayofweek = dayofweek,
		repeat = repeat,
		tags = tags,
		form_content = form_content,
		messages=messages)


@app.route('/filter', methods=['GET', 'POST'])
def filter():
	cur = g.db.cursor()
	if request.method == 'POST':
		valid = True
		state_id = None
		if not request.form['newstate'] and not request.form['state_sel']:
			flash("State is required.")
			valid = False
		elif request.form['state_sel']:
			cur.execute("SELECT state_id FROM STATE WHERE uid = %s AND state_name = %s", (g.uid, request.form['state_sel']))
			results = cur.fetchone()
			if results is not None:
				state_id = results[0]
			else:
				state_id = process.add_state(g.uid, request.form['state_sel'])    # add state to db
			process.update_state(g.uid, state_id)
			g.state = request.form['state_sel']
		elif request.form['newstate']:
			cur.execute("SELECT state_id FROM STATE WHERE uid = %s AND state_name = %s", (g.uid, request.form['newstate']))
			results = cur.fetchone()
			if results is not None:
				state_id = results[0]
			else:
				state_id = process.add_state(g.uid, request.form['newstate']) # add state to db
				state.append(request.form['newstate'])
			process.update_state(g.uid, state_id)
			g.state = request.form['newstate']

		if not ((request.form['startdatetime'] and request.form['enddatetime']) or (request.form['starttime'] and request.form['endtime'])):
			valid = False
			flash("Schedule is required.")

		if valid:
			# add schedule to db
			schedule_id = process.get_schedule_id(repeat=request.form['repeat_sel'], startdatetime=request.form['startdatetime'],
												  enddatetime=request.form['enddatetime'], starttime=request.form['starttime'], 
												  endtime=request.form['endtime'], dow=request.form['dow_sel'])
			if request.form['loc']:
				loc_id = process.get_location_id(loc=request.form['loc'])
			else:
				loc_id = None
			process.update_loc(g.uid, loc_id)
			selecttag = request.form['jquery-tagbox-select'].split(',')
			addtag = request.form['jquery-tagbox-text'].split(',')
			# add a new filter
			process.add_filter(state_id=state_id, schedule_id=schedule_id, loc_id=loc_id, selecttag=selecttag, addtag=addtag)
	fields = ['NAME', 'STATE', 'START', 'END', 'DAYOFWEEK', 'LOCATION', 'TAG']
	query_filter = "SELECT username, state_name, starttime, endtime, dow_name, location_name, tag_name \
		FROM USER NATURAL JOIN STATE NATURAL JOIN FILTER NATURAL JOIN SCHEDULE NATURAL LEFT JOIN LOCATION NATURAL JOIN DAYOFWEEK NATURAL LEFT JOIN TAGS_IN_FILTER NATURAL LEFT JOIN TAG \
		WHERE dayofweek = dow_id AND uid = %s"
	cur.execute(query_filter, (g.uid,))
	results = cur.fetchall()
	return render_template('filter.html',
		dayofweek = dayofweek,
		repeat = repeat,
		tags = tags,
		state = state,
		results = results,
		fields = fields)

@app.route('/map')
def map():
	return render_template('map.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
	distance = None
	if request.method == 'POST':
		distance = process.cal_distance(39, 40)
	return render_template('test.html', distance=distance)

# add some filters to jinja
# app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url