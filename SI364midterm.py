###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy
import requests
import json

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/joshwalk364midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################




##################
##### MODELS #####
##################

class ZIP(db.Model):
	__tablename__ = "zips"
	id = db.Column(db.Integer, primary_key=True)
	zip_code = db.Column(db.Integer)
	city_id = db.Column(db.Integer,db.ForeignKey("cities.id"))

	def __repr__(self):
	    return "ZIP: {}".format(self.zip_code)

class City(db.Model):
	__tablename__ = "cities"
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64))
	state = db.Column(db.String(64))

	def __repr__(self):
	    return "{} (State: {})".format(self.name, self.state)


###################
###### FORMS ######
###################

class ZIPForm(FlaskForm):
	name = StringField("Enter the name of a city:",validators=[Required()])
	state = StringField("Enter state name:", validators=[Required()])
	submit = SubmitField()



#######################
###### VIEW FXNS ######
#######################

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.route('/', methods=['GET', 'POST'])
def home():
	form = ZIPForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
	if form.validate_on_submit():
		name = form.name.data
		state  = form.state.data
		city = City(name=name, state=state)
		db.session.add(city)
		db.session.commit()
		response = requests.get("http://api.zippopotam.us/us/" + state.lower() + "/" + name.lower())
		data = json.loads(response.text)
		results = data['places']
		for place in results:
			city_name = place["place name"]
			zip_code = place["post code"]
			cities_city = City.query.filter_by(name=city_name).first()
			newzip = ZIP(zip_code=zip_code, city_id=cities_city.id)
			db.session.add(newzip)
			db.session.commit()
		return redirect(url_for('all_cities'))
	return render_template('base.html',form=form)

@app.route('/cities')
def all_cities():
	names = City.query.all()
	return render_template('cities.html',names=names)

# @app.route('/zips')
# def all_zips():
#






## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
	db.create_all() # Will create any defined models when you run the application
	app.run(use_reloader=True,debug=True) # The usual
