from app import db, ma
from flask_marshmallow import Marshmallow

# Model for Sales
class Sales(db.Model):

    __tablename__ = 'sales'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    filnr = db.Column(db.Integer, nullable=False)
    artnr = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Integer, nullable=True)
    date = db.Column(db.Date)
    amount = db.Column(db.Integer, nullable=True)
    prediction = db.Column(db.Integer)

    def __init__(self, filnr, artnr, discount, date, amount, prediction):
        
        self.filnr = filnr
        self.artnr = artnr
        self.discount = discount
        self.date = date
        self.amount = amount
        self.prediction = prediction

class SalesSchema(ma.Schema):
    class Meta:
        fields = ('id', 'filnr', 'artnr', 'discount', 'date', 'amount', 'prediction')

sale_schema = SalesSchema()
sales_schema = SalesSchema(many=True)

# Model for Prediction
class Prediction(db.Model):

    __tablename__ = 'prediction'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    filnr = db.Column(db.Integer, nullable=False)
    artnr = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date)
    prediction = db.Column(db.Integer, nullable=True)
    base_value = db.Column(db.Integer)
    dayspecific = db.Column(db.Integer)
    weather = db.Column(db.Integer)
    lastmonth = db.Column(db.Integer)
    safetystock = db.Column(db.Integer)

    def __init__(self, filnr, artnr, date, prediction, base_value, dayspecific, weather, lastmonth, safetystock):
        self.filnr = filnr
        self.artnr = artnr
        self.date = date
        self.prediction = prediction
        self.base_value = base_value
        self.dayspecific = dayspecific
        self.weather = weather
        self.lastmonth = lastmonth
        self.safetystock = safetystock

class PredictionSchema(ma.Schema):
    class Meta:
        fields = ('id', 'filnr', 'artnr', 'date', 'prediction', 'base_value', 'dayspecific', 'weather', 'lastmonth', 'safetystock')

prediction_schema = PredictionSchema()
predictions_schema = PredictionSchema(many=True)

# Model for Location
class Location(db.Model):

    __tablename__ = 'location'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    filnr = db.Column(db. Integer, nullable=False)
    street = db.Column(db.Text)
    zipcode = db.Column(db.Integer, nullable=False)
    city = db.Column(db.Text)
    state = db.Column(db.Text)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

    def __init__(self, filnr, street, zipcode, city, state, lat, lon):
        self.filnr = filnr
        self.steet = street
        self.zipcode = zipcode
        self.city = city
        self.state = state
        self.lat = lat
        self.lon = lon

class LocationSchema(ma.Schema):
    class Meta:
        fields = ('id', 'filnr', 'street', 'zipcode', 'city', 'state', 'lat', 'lon')

location_schema = LocationSchema()
locations_schema = LocationSchema(many=True)