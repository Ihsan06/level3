from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
import os

# Initialize core application
app = Flask(__name__, instance_relative_config=False)
config = app.config.from_object('config.DevelopmentConfig')

# Initialize database
db = SQLAlchemy(app)

# Initialize marshamllow
ma = Marshmallow(app)

# Initialize migration
migrate = Migrate(app, db)

from . import models, routes