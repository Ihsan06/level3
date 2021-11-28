from flask import request, jsonify, render_template, Response
from . import app, db
from app.models import Sales, SalesSchema, sale_schema, sales_schema, Prediction, PredictionSchema, prediction_schema, predictions_schema, Location, LocationSchema, location_schema, locations_schema
from config import operational_link
import requests

# API-Documentation
@app.route('/docs')
def docs():
    return render_template('swaggerui.html')

# Defining home endpoint
@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

# Get all sales paginated to 100 objects per page
@app.route('/api/sales/all', methods=['GET'])
@app.route('/api/sales/all/<int:page>', methods=['GET'])
def get_sales(page=1):
    per_page = 100
    all_sales = Sales.query.paginate(page, per_page, error_out = False)
    result = sales_schema.dump(all_sales.items)
    return jsonify(result)

# Get all unique entries of class sales
@app.route('/api/sales/unique/<unique>', methods=['GET'])
def get_unique_sales(unique):
    unique_entries = db.session.query(Sales).distinct(unique)
    unique_schema = SalesSchema(only=(str(unique),), many=True)
    return unique_schema.jsonify(unique_entries)

# Get single sale queried by id
@app.route('/api/sales/id/<id>', methods=['GET'])
def get_sale_by_id(id):
    sale = Sales.query.get(id)
    return sale_schema.jsonify(sale)

# Post sales
@app.route('/api/sales', methods=['POST'])
def post_sales():
    for jsonObjects in request.json:
        filnr = jsonObjects['filnr']
        artnr = jsonObjects['artnr']
        discount = jsonObjects['discount']
        date = jsonObjects['date']
        amount = jsonObjects['amount']
        prediction = jsonObjects['prediction']

        new_sales = Sales(filnr, artnr, discount, date, amount, prediction)

        db.session.add(new_sales)
    db.session.commit()

    return sale_schema.jsonify(request.json)

# Update single sale queried by id
@app.route('/api/sales/id/<id>', methods=['PUT'])
def update_sale(id):
    sale = Sales.query.get(id)

    filnr = request.json['filnr']
    artnr = request.json['artnr']
    discount = request.json['discount']
    date = request.json['date']
    amount = request.json['amount']
    prediction = request.json['prediction']

    sale.filnr = filnr
    sale.artnr = artnr
    sale.discount = discount
    sale.date = date
    sale.amount = amount
    sale.prediction = prediction

    db.session.commit()

    return sale_schema.jsonify(sale)

# Update multiple historical Predictions queried by id
@app.route('/api/sales', methods=['PUT'])
def update_sales():
    for singleSaleJson in request.json:
        id = singleSaleJson['id']
        sale = Sales.query.get(id)
        sale.prediction = singleSaleJson['prediction']
    db.session.commit()

    return Response(status=200)

# Delete single Sale queried by id
@app.route('/api/sales/id/<id>', methods=['DELETE'])
def delete_sale(id):
    sale = Sales.query.get(id)

    db.session.delete(sale)
    db.session.commit()
    
    return sale_schema.jsonify(sale)

# Filtering sales for each parameter and paginated to 100 objects per page
@app.route('/api/sales', methods=['GET'])
def sales_filter():
    query_parameters = request.args

    page = int(query_parameters.get('page')) if query_parameters.get('page') else 1
    pageSize = int(query_parameters.get('pageSize')) if query_parameters.get('pageSize') else 100
    filnr = query_parameters.get('filnr')
    artnr = query_parameters.get('artnr')
    discount = query_parameters.get('discount')
    date = query_parameters.get('date')
    amount = query_parameters.get('amount')

    query = Sales.query

    if filnr:
        query = query.filter(Sales.filnr == filnr)
    if artnr:
        query = query.filter(Sales.artnr == artnr)
    if discount:
        query =  query.filter(Sales.discount == discount)
    if date:
        query = query.filter(Sales.date == date)
    if amount:
        query = query.filter(Sales.amount == amount)   

    paginated_sales = query.paginate(page, pageSize, error_out = False)
    result = sales_schema.dump(paginated_sales.items)

    return jsonify(result)

# Get daterange specific amounts paginated to 100 objects per page
@app.route('/api/sales/amount', methods=['GET'])
def date_range():
    query_parameters = request.args

    page = int(query_parameters.get('page')) if query_parameters.get('page') else 1
    pageSize = int(query_parameters.get('pageSize')) if query_parameters.get('pageSize') else 100
    filnr = query_parameters.get('filnr')
    artnr = query_parameters.get('artnr')
    dateFrom = query_parameters.get('dateFrom')
    dateTo = query_parameters.get('dateTo')

    query = Sales.query.filter(Sales.date.between(dateFrom, dateTo))

    if filnr:
        query = query.filter(Sales.filnr == filnr)
    if artnr:
        query = query.filter(Sales.artnr == artnr)

    paginated_amount = query.paginate(page, pageSize, error_out = False)
    amount_schema = SalesSchema(only=('id', 'filnr', 'artnr', 'date', 'amount'), many=True)
    result = amount_schema.dump(paginated_amount.items)

    return jsonify(result)

# Get all Predictions paginated to 100 objects per page
@app.route('/api/prediction/all', methods=['GET'])
@app.route('/api/prediction/all/<int:page>', methods=['GET'])
def get_prediction(page=1):
    per_page = 100
    all_prediction = Prediction.query.paginate(page, per_page, error_out=False)
    result = predictions_schema.dump(all_prediction.items)
    return jsonify(result)

# Get all unique entries of the class prediction
@app.route('/api/prediction/unique/<unique>', methods=['GET'])
def get_unique_prediction(unique):
    unique_entries = db.session.query(Prediction).distinct(unique)
    unique_schema = SalesSchema(only=(str(unique),), many=True)
    return unique_schema.jsonify(unique_entries)

# Post predictions
@app.route('/api/prediction', methods=['POST'])
def post_prediction():
    for jsonObjects in request.json:
        filnr = jsonObjects['filnr']
        artnr = jsonObjects['artnr']
        date = jsonObjects['date']
        prediction = jsonObjects['prediction']
        base_value = jsonObjects['base_value']
        dayspecific = jsonObjects['dayspecific']
        weather = jsonObjects['weather']
        lastmonth = jsonObjects['lastmonth']
        safetystock = jsonObjects['safetystock']

        new_prediction = Prediction(filnr, artnr, date, prediction, base_value, dayspecific, weather, lastmonth, safetystock)

        db.session.add(new_prediction)
    db.session.commit()

    return predictions_schema.jsonify(request.json)

# Update multiple predictions
@app.route('/api/prediction', methods=['PUT'])
def update_prediction():
    for singleJsonObject in request.json:
        id = singleJsonObject['id']
        prediction = Prediction.query.get(id)

        prediction.date = singleJsonObject['date']
        prediction.prediction = singleJsonObject['prediction']
        prediction.dayspecific = singleJsonObject['dayspecific']
        prediction.weather = singleJsonObject['weather']
        prediction.lastmonth = singleJsonObject['lastmonth']
        prediction.safetystock = singleJsonObject['safetystock']

    db.session.commit()

    return Response(status=200)

# Filter predictions for each parameter and paginated to 100 objects per page
@app.route('/api/prediction', methods=['GET'])
def prediction_filter():
    query_parameters = request.args

    page = int(query_parameters.get('page')) if query_parameters.get('page') else 1
    pageSize = int(query_parameters.get('pageSize')) if query_parameters.get('pageSize') else 100
    filnr = query_parameters.get('filnr')
    artnr = query_parameters.get('artnr')
    date = query_parameters.get('date')
    prediction = query_parameters.get('prediction')
    base_value = query_parameters.get('base_value')
    dayspecific = query_parameters.get('dayspecific')
    weather = query_parameters.get('weather')
    lastmonth = query_parameters.get('lastmonth')
    safetystock = query_parameters.get('safetystock')

    query = Prediction.query

    if filnr:
        query = query.filter(Prediction.filnr == filnr)
    if artnr:
        query = query.filter(Prediction.artnr == artnr)
    if date:
        query = query.filter(Prediction.date == date)
    if prediction:
        query = query.filter(Prediction.prediction == prediction)
    if base_value:
        query = query.filter(Prediction.base_value == base_value)
    if dayspecific:
        query = query.filter(Prediction.dayspecific == dayspecific)
    if weather:
        query = query.filter(Prediction.weather == weather)
    if lastmonth:
        query = query.filter(Prediction.lastmonth == lastmonth)
    if safetystock:
        query = query.filter(Prediction.safetystock == safetystock)      

    paginated_predictions = query.paginate(page, pageSize, error_out = False)
    result = predictions_schema.dump(paginated_predictions.items)

    return jsonify(result)

# Delete all predictions
@app.route('/api/prediction', methods=['DELETE'])
def delete_predictions():
    db.session.query(Prediction).delete()
    db.session.commit()
    return '<h1>Successfully deleted<h1>'

# Get all locations
@app.route('/api/location/all', methods=['GET'])
def get_location():
    all_locations = Location.query.all()
    result = locations_schema.dump(all_locations)
    return jsonify(result)

# Post locations
@app.route('/api/location', methods=['POST'])
def post_location():
    for singleJsonObject in request.json:
        filnr = singleJsonObject['filnr']
        street = singleJsonObject['street']
        zipcode = singleJsonObject['zipcode']
        city = singleJsonObject['city']
        state = singleJsonObject['state']
        lat = singleJsonObject['lat']
        lon = singleJsonObject['lon']

        new_location = Location(filnr, street, zipcode, city, state, lat, lon)

        db.session.add(new_location)
    db.session.commit()

    return location_schema.jsonify(request.json)

# Delete Location queried by id
@app.route('/api/location/id/<id>', methods=['DELETE'])
def delete_location(id):
    location = Location.query.get(id)

    db.session.delete(location)
    db.session.commit()
    
    return sale_schema.jsonify(location)

# Run pipelines for the defined duration
@app.route('/operational/run/<duration>')
def run(duration):
    requests.get(url = operational_link + '/run/' + duration)

    return ("<h1>Run Completed<h1>")

# Run piplelines and upload Predictions for the defined duration
@app.route('/operational/run/upload/<duration>')
def run_upload_days(duration):
    requests.get(url = operational_link + '/run/upload/' + duration)

    return ("<h1>Run & Upload Completed<h1>")

# Runs the pipelines for the initiation of the data from a new release
@app.route('/operational/initiate')
def initiate():
    requests.get(url = operational_link + '/initiate')

    return ("<h1>Initialization Completed<h1>")

# Initiation and run pipelines for the defined duration
@app.route('/operational/run/initiate/<duration>')
def run_init_days(duration):
    requests.get(url = operational_link + '/run/initiate/' + duration)

    return ('<h1>Run Completed<h1>')

# Initiation, run & upload predictions for the defined duration
@app.route('/operational/run/initiate/upload/<duration>')
def run_n_upload(duration):
    requests.get(url = operational_link + '/run/initiate/upload/' + duration)

    return ('<h1>Run & Upload Completed<h1>')

# Upload Predictions
@app.route('/operational/upload')
def upload():
    requests.get(url = operational_link + '/upload')

    return ("<h1>Upload Completed<h1>")