from flask import g, flash, render_template
import MySQLdb as mdb
from datetime import date
from config import tags

class dbprocess():
	def insert_note(self, uid=None, words='', link=None, loc_id=None,
					radius=None, repeat=0, startdatetime=None,
					enddatetime=None, starttime=None, endtime=None,
					dow=None, selecttag=[], addtag=[]):
		cur = g.db.cursor()
		# add schedule
		if (repeat == '0'):	# Never repeat
			start = str(startdatetime) + ':00'
			end = str(enddatetime) + ':00'
		else:	# Every Day or Every Week
			start = str(date.today()) + ' ' + str(starttime) + ':00'
			end = str(date.today()) + ' ' + str(endtime) + ':00'
		query_add_schedule = "INSERT INTO SCHEDULE (starttime, endtime, repeat_id, dayofweek) \
					VALUES (%s, %s, %s ,%s)"
		cur.execute(query_add_schedule, (start, end, repeat, dow))
		schedule_id = g.db.insert_id()
		flash("Add new schedule: " + str(schedule_id))

		# add tag
		tag_id = []
		for a in addtag:	# remove same tags
			if a in selecttag:
				addtag.remove(a)
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
		query_add_note = "INSERT INTO NOTE (uid, words, hyperlink, location_id, radius, schedule_id) \
				VALUES (%s, %s, %s, %s, %s, %s)"
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
		flash("Add location " + results[0] + ": " + str(loc_id))
		return loc_id

# if __name__ == '__main__':
	# db = mdb.connect('127.0.0.1', 'root', 'root', 
	# 	'Jingo_DB', port=8889);
	# cur = db.cursor()