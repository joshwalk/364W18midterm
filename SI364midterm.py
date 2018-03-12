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
app.config['SECRET_KEY'] = 'mysecretkey'
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
	state_id = db.Column(db.Integer,db.ForeignKey("states.id"))

	def __repr__(self):
		return "City: {}".format(self.name)

class State(db.Model):
	__tablename__ = "states"
	id = db.Column(db.Integer,primary_key=True)
	name = db.Column(db.String(64))
	abbrev = db.Column(db.String(64))

	def __repr__(self):
		return "State name:{} ({})".format(self.name, self.abbrev)


###################
###### FORMS ######
###################

def check_valid_state(form,field):
	states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
		  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
		  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
		  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
		  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"] # I got this list from https://gist.github.com/JeffPaine/3083347
	if field.data.upper() not in states:
		raise ValidationError("Error: must be valid state abbreviation")

class ZIPForm(FlaskForm):
	name = StringField("Enter the name of a US city:",validators=[Required()])
	state = StringField("Enter state abbreviation:", validators=[Required(), check_valid_state])
	submit = SubmitField()

class UserForm(FlaskForm):
	username = StringField("Enter your user name:",validators=[Required()])
	fullname = StringField("Enter your full name:",validators=[Required()])
	submit = SubmitField()

class StateToZIPSForm(FlaskForm):
	state = StringField("Enter state (full name, not abbrev):", validators=[Required()])
	submit = SubmitField()

#######################
###### VIEW FXNS ######
#######################

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.route('/', methods=['GET', 'POST'])
def home():
	form = ZIPForm()
	if form.validate_on_submit():
		city_entered = form.name.data
		state_entered  = form.state.data
		response = requests.get("http://api.zippopotam.us/us/" + state_entered.lower() + "/" + city_entered.lower())
		data = json.loads(response.text)

		state_fullname = data["state"]
		state_abbrev = data["state abbreviation"]
		state = State.query.filter_by(abbrev=state_abbrev).first()
		if state:
			state_id = state.id
		else:
			newstate = State(name=state_fullname,abbrev=state_abbrev)
			db.session.add(newstate)
			db.session.commit()
			state_id = State.query.filter_by(name=state_fullname).first().id

		city_name = data["place name"]
		if City.query.filter_by(name=city_name, state_id=state_id).first():
			flash("the city and state entered is already in the database")
			return redirect(url_for("all_cities"))
		else:
			newcity =  City(name=city_name, state_id=state_id)
			db.session.add(newcity)
			db.session.commit()

		for place in data['places']:
			zip_code = place["post code"]
			city_id = City.query.filter_by(name=city_name).first().id
			newzip = ZIP(zip_code=zip_code, city_id=city_id)
			db.session.add(newzip)
			db.session.commit()
		return redirect(url_for('all_zips'))
	return render_template('index.html',form=form)

@app.route('/cities')
def all_cities():
	names = City.query.all()
	return render_template('cities.html',names=names)

@app.route('/zips')
def all_zips():
	zips = ZIP.query.all()
	return render_template('zips.html', names=zips)

@app.route('/states')
def all_states():
	states = State.query.all()
	return render_template('states.html', names=states)

@app.route('/userform')
def user_form():
	form = UserForm()
	return render_template('userform.html', form=form)

@app.route('/userresults', methods = ["GET","POST"])
def user_results():
	if request.args:
		username = request.args.get('username')
		fullname = request.args.get('fullname')
		return render_template('userresults.html', username=username,fullname=fullname)
	flash(form.errors)
	return redirect(url_for('user_form'))

@app.route('/statetozips', methods = ["GET","POST"])
def state_to_zips():
	form = StateToZIPSForm()
	zip_list = []
	if form.validate_on_submit():
		state = form.state.data
		state_id = State.query.filter_by(name=state).first().id
		for city in City.query.filter_by(state_id=state_id):
			for zip in ZIP.query.filter_by(city_id=city.id):
				zip_list.append(zip.zip_code)
	return render_template('state_to_zips.html', zip_list=zip_list, form=form)


## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
	db.create_all() # Will create any defined models when you run the application
	app.run(use_reloader=True,debug=True) # The usual
