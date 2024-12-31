# Import the dependencies.
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import sqlite3

#Create app instance
app = Flask(__name__)

#Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Resources/hawaii.sqlite' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#Initialize SQLAlchemy
db = SQLAlchemy(app)

#Test database connection
def connect_to_database():
    try:
        conn = sqlite3.connect('Resources/hawaii.sqlite')
        print("Database opened successfully")
        return conn
    except sqlite3.Error as e:
        print(f"Error opening database: {e}")

#Connect to database
connection = connect_to_database()

#Define classes
class Precipitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    prcp = db.Column(db.Float, nullable=False)
    __table_args__ = {'extend_existing': True}
    def __repr__(self):
        return f'<Precipitation {self.date}: {self.prcp}>'
    
class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    __table_args__ = {'extend_existing': True}
    def __repr__(self):
        return f'<Station {self.name}>'
    
# Define a model for temperature observations
class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    __table_args__ = {'extend_existing': True}
    def __repr__(self):
        return f'<Temperature {self.name}>'

#Connect station and temperature databases   
station = db.relationship('Station', backref=db.backref('temperatures', lazy=True))

#Define routes
@app.route("/")
def home():
    routes = {
        "About": "/about",
        "Precipitation": "/api/v1.0/precipitation",
        "Stations": "/api/v1.0/stations",
        "Temperature at most active station": "/api/v1.0/tobs",
        "Temperature on specified start date": "/api/v1.0/<start>",
        "Temperature between two specified dates": "/api/v1.0/<start>/<end>"
    }
    return jsonify(routes)

@app.route("/about")
def about():
    return "This is the About page."

@app.route("/api/v1.0/precipitation")
def get_precipitation():
    # Calculate the date 12 months ago from today
    last_year_date = datetime.now() - timedelta(days=365)

    # Query the database for precipitation data from the last 12 months
    results = Precipitation.query.filter(Precipitation.date >= last_year_date).all()

    # Convert query results to a dictionary
    precipitation_data = {record.date.strftime("%Y-%m-%d"): record.prcp for record in results}

    # Return the JSON representation of the dictionary
    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def get_stations():
    # Query all stations
    stations = Station.query.all()

    # Convert query results to a list of dictionaries
    station_list = [
        {
            "id": station.id,
            "name": station.name,
            "latitude": station.latitude,
            "longitude": station.longitude
        }
        for station in stations
    ]

    # Return the JSON representation of the list
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def get_most_active_station_temperatures():
    # Calculate the date for one year ago
    one_year_ago = datetime.now() - timedelta(days=365)

    # Find the most active station (the one with the most temperature records)
    most_active_station = db.session.query(
        Temperature.station_id,
        db.func.count(Temperature.id).label('count')
    ).filter(Temperature.date >= one_year_ago).group_by(Temperature.station_id).order_by(db.desc('count')).first()

    if not most_active_station:
        return jsonify({"error": "No temperature data available for the previous year."}), 404

    # Retrieve temperature observations for the most active station for the previous year
    temperatures = Temperature.query.filter(
        Temperature.station_id == most_active_station.station_id,
        Temperature.date >= one_year_ago
    ).all()

    # Convert query results to a list of dictionaries
    temperature_list = [
        {
            "date": temp.date.strftime("%Y-%m-%d"),
            "temperature": temp.temperature
        }
        for temp in temperatures
    ]

    # Return the JSON representation of the list
    return jsonify(temperature_list)

# Route to retrieve temperature statistics for a specified date range
@app.route('/api/v1.0/<start>', methods=['GET'])
def get_temperature_stats(start):
    # Convert string date to datetime object
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid start date format. Use YYYY-MM-DD."}), 400

    # Query the temperature data based on the specified start date
    temperatures = Temperature.query.filter(Temperature.date >= start_date).all()

    if not temperatures:
        return jsonify({"error": "No temperature data available for the specified date range."}), 404

    # Calculate TMIN, TAVG, and TMAX
    temp_values = [temp.temperature for temp in temperatures]
    tmin = min(temp_values)
    tavg = sum(temp_values) / len(temp_values)
    tmax = max(temp_values)

    # Prepare the result as a dictionary
    result = {
        "TMIN": tmin,
        "TAVG": tavg,
        "TMAX": tmax
    }

    # Return the JSON representation of the result
    return jsonify(result)

@app.route('/api/v1.0/<start>/<end>', methods=['GET'])
def get_temperature_stats_range(start, end):
    # Convert string dates to datetime objects
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Query the temperature data based on the specified date range
    temperatures = Temperature.query.filter(Temperature.date >= start_date, Temperature.date <= end_date).all()

    if not temperatures:
        return jsonify({"error": "No temperature data available for the specified date range."}), 404

    # Calculate TMIN, TAVG, and TMAX
    temp_values = [temp.temperature for temp in temperatures]
    tmin = min(temp_values)
    tavg = sum(temp_values) / len(temp_values)
    tmax = max(temp_values)

    # Prepare the result as a dictionary
    result = {
        "TMIN": tmin,
        "TAVG": tavg,
        "TMAX": tmax
    }

    # Return the JSON representation of the result
    return jsonify(result)
#################################################
#
if __name__ == "__main__":
    app.run(debug=True)