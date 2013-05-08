from flask import g, flash, render_template
import MySQLdb as mdb
from datetime import date
from config import tags
import math

class dbprocess():
	def insert_note(self, uid=None, words='', link=None, loc_id=None,
					radius=None, schedule_id=None, selecttag=[], addtag=[]):
		cur = g.db.cursor()
		# add tag
		tag_id = []
		if addtag and addtag[0] is not u'':
			for a in addtag:	# remove same tags
				if a in selecttag:
					addtag.remove(a)
		if selecttag and selecttag[0] is not u'':
			for s in selecttag:	# predefined tag id
				for row in tags:
					if s in row['name']:
						tag_id.append(row['id'])
		if addtag and addtag[0] is not u'': 	# use this condition for unicode empty list
			query_show_tag = "SELECT * FROM TAG"
			cur.execute(query_show_tag)
			results = cur.fetchall()
			for a in addtag:
				exist = False
				for i,n in results:
					if a == n:	# exist
						tag_id.append(i)
						exist = True
						break
				if not exist:	# new
					query_add_tag = "INSERT INTO TAG (tag_name) VALUES (%s)"
					cur.execute(query_add_tag, (a))
					tag_id.append(g.db.insert_id())

		# add note
		query_add_note = "INSERT INTO NOTE (uid, words, hyperlink, location_id, radius, schedule_id) VALUES (%s, %s, %s, %s, %s, %s)"
		cur.execute(query_add_note, (uid, words, link, loc_id, radius, schedule_id))
		note_id = g.db.insert_id()
		flash("Write a new note: " + str(note_id))
		# flash(cur.lastrowid)

		# add tags_in_note
		query_add_tags_in_note = "INSERT INTO TAGS_IN_NOTE (note_id, tag_id) VALUES (%s, %s)"
		for t in tag_id:
			cur.execute(query_add_tags_in_note, (note_id, t))
		g.db.commit()
		# flash("Add tags_in_note.")

	def add_filter(self, state_id=None, schedule_id=None, loc_id=None, 
					filter_radius=None, selecttag=[], addtag=[]):
		cur = g.db.cursor()
		# add tag
		tag_id = []
		if addtag and addtag[0] is not u'':
			for a in addtag:	# remove same tags
				if a in selecttag:
					addtag.remove(a)
		if selecttag and selecttag[0] is not u'':
			for s in selecttag:	# predefined tag id
				for row in tags:
					if s in row['name']:
						tag_id.append(row['id'])
		if addtag and addtag[0] is not u'': 	# use this condition for unicode empty list
			query_show_tag = "SELECT * FROM TAG"
			cur.execute(query_show_tag)
			results = cur.fetchall()
			for a in addtag:
				exist = False
				for i,n in results:
					if a == n:	# exist
						tag_id.append(i)
						exist = True
						break
				if not exist:	# new
					query_add_tag = "INSERT INTO TAG (tag_name) VALUES (%s)"
					cur.execute(query_add_tag, (a))
					tag_id.append(g.db.insert_id())
		print "selecttag: " 
		print selecttag
		print "addtag: "
		print addtag
		print "tag_id[]: "
		print tag_id

		# add filter
		query_add_filter = "INSERT INTO FILTER (state_id, location_id, filter_radius, schedule_id) VALUES (%s, %s, %s, %s)"
		cur.execute(query_add_filter, (state_id, loc_id, filter_radius, schedule_id))
		filter_id = g.db.insert_id()
		flash("Add a new filter: " + str(filter_id))

		# add tags_in_filter
		query_add_tags_in_filter = "INSERT INTO TAGS_IN_FILTER (filter_id, tag_id) VALUES (%s, %s)"
		for t in tag_id:
			cur.execute(query_add_tags_in_filter, (filter_id, t))
		g.db.commit()
		flash("Succeeded to add tags_in_filter.")


	def get_location_id(self, loc=None):
		# add location to db and get location id
		results = loc.split(';')
		if not results or results[0] is u'':
			loc_id = None
			return loc_id
		cur = g.db.cursor()
		query = "INSERT INTO `Jingo_DB`.`LOCATION` (`location_id`, `latitude`, `longitude`, `location_name`) VALUES (NULL, %s, %s, %s);"
		cur.execute(query, (results[1],results[2],results[0]))
		loc_id = g.db.insert_id()
		flash("Add location: " + results[0] + ": " + str(loc_id))
		return loc_id

	def get_schedule_id(self, repeat='0', startdatetime=None, enddatetime=None, 
						starttime=None, endtime=None, dow=None,):
		# add schedule to db and get schedule id
		if (repeat == '0'):	# Never repeat
			start = str(startdatetime) + ':00'
			end = str(enddatetime) + ':00'
		else:	# Every Day or Every Week
			start = str(date.today()) + ' ' + str(starttime) + ':00'
			end = str(date.today()) + ' ' + str(endtime) + ':00'
		cur = g.db.cursor()
		query_add_schedule = "INSERT INTO SCHEDULE (starttime, endtime, repeat_id, dayofweek) VALUES (%s, %s, %s ,%s)"
		cur.execute(query_add_schedule, (start, end, repeat, dow))
		schedule_id = g.db.insert_id()
		flash("Add new schedule: " + str(schedule_id))
		return schedule_id

	def add_state(self, uid, newstate):
		cur = g.db.cursor()
		query_add_state = "INSERT INTO STATE (uid, state_name) VALUES (%s ,%s)"
		cur.execute(query_add_state, (uid, newstate))
		state_id = g.db.insert_id()
		g.db.commit()
		flash("Add new state: " + newstate + ", id: " + str(state_id))
		return state_id

	def cal_distance(self, loc_id1, loc_id2):
		cur = g.db.cursor()
		query_get_loc_id = "SELECT latitude, longitude FROM LOCATION WHERE location_id = %s"
		cur.execute(query_get_loc_id, (loc_id1,))
		results = cur.fetchone()
		if results:
			lat1 = float(results[0])
			long1 = float(results[1])
		cur.execute(query_get_loc_id, (loc_id2,))
		results = cur.fetchone()
		if results:
			lat2 = float(results[0])
			long2 = float(results[1])
			
		# Convert latitude and longitude to 
		# spherical coordinates in radians.
		degrees_to_radians = math.pi/180.0
			
		# phi = 90 - latitude
		phi1 = (90.0 - lat1)*degrees_to_radians
		phi2 = (90.0 - lat2)*degrees_to_radians
			
		# theta = longitude
		theta1 = long1*degrees_to_radians
		theta2 = long2*degrees_to_radians
			
		# Compute spherical distance from spherical coordinates.
			
		# For two locations in spherical coordinates 
		# (1, theta, phi) and (1, theta, phi)
		# cosine( arc length ) = 
		#    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
		# distance = rho * arc length
		
		cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
			   math.cos(phi1)*math.cos(phi2))
		arc = math.acos( cos )

		# Remember to multiply arc by the radius of the earth 
		# in your favorite set of units to get length.
		# To get the distance in miles, multiply by 3960. To get the distance in kilometers, multiply by 6373.
		return arc * 6373 * 1000	# use meters

if __name__ == '__main__':
	# db = mdb.connect('127.0.0.1', 'root', 'root', 
	# 	'Jingo_DB', port=8889);
	# cur = db.cursor()
	# cur.execute("SELECT state_id FROM STATE WHERE uid = %s AND state_name = %s", (1, 'lunch break'))
	# results = [row[0] for row in cur.fetchall()]
	# if cur.fetchone():
	# 	result = cur.fetchone()[0]
	# else:
	# 	result = None
	# print result
	process = dbprocess()
	# print process.cal_distance(40.694074, -73.98693, 40.694461, -73.98576)
