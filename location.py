from flask import Flask, render_template, g, request, redirect, flash, url_for
import MySQLdb as mdb

SECRET_KEY = 'development key'
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
	return mdb.connect('127.0.0.1', 'root', 'root', 
		'Jingo_DB', port=8889);

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	g.db.close()

@app.route('/', methods=['GET', 'POST'])
def show_tables():
	return render_template('open.html')

@app.route('/map')
def map():
    return render_template('map.html')
    
@app.route('/location', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        results = request.form['location'].split(';')
        cur = g.db.cursor()
        query = "INSERT INTO `Jingo_DB`.`LOCATION` (`location_id`, `latitude`, `longitude`, `location_name`) VALUES (NULL, %s, %s, %s);"
        cur.execute(query, (results[1],results[2],results[0]))
        g.db.commit()
       
    return render_template('open.html')
    