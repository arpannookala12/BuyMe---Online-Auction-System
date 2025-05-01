# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate   import Migrate
from flask_apscheduler import APScheduler

db        = SQLAlchemy()
migrate   = Migrate()
scheduler = APScheduler()
