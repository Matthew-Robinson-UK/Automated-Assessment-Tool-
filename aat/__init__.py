import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .models import db, login_manager, QuestionT2
from .assessments import assessments
from .auth import auth
from .stats import stats
from .student_stats import student_stats

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "aat.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#Make sure to install python-dotenv, and check the .env.example file
#Then simply make your own .env file with the same format
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

app.register_blueprint(assessments, url_prefix="/assessments")
app.register_blueprint(stats, url_prefix="/stats")
app.register_blueprint(student_stats, url_prefix="/student-stats")
app.register_blueprint(auth)

db.init_app(app)
login_manager.init_app(app)


from . import routes
