import os
import psycopg2

# General configuration
basedir = os.path.abspath(os.path.dirname(__file__))

# Connection to other services
operational_link = os.environ.get('OPERATIONAL_SERVICE')

# Setting various programming environments (usage in /app/__init__.py)
class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'secretkey'

    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql+psycopg2://postgres:hallolevel3@localhost:5432/webers')
    SQLALCHEMY_HOST = os.environ.get('SQLALCHEMY_HOST')
    SQLALCHEMY_USERNAME = os.environ.get('SQLALCHEMY_USERNAME')
    SQLALCHEMY_PASSWORD = os.environ.get('SQLALCHEMY_PASSWORD')
    SQLALCHEMY_DATABASE_NAME = 'webers'
    SQLALCHEMY_DB_SCHEMA = 'public'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True