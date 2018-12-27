# -*- coding: utf-8 -*-
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate

bootstrap = Bootstrap()
db = SQLAlchemy()
#login_manager = LoginManager()
login = LoginManager()
csrf = CSRFProtect()
ckeditor = CKEditor()
mail = Mail()
moment = Moment()
toolbar = DebugToolbarExtension()
migrate = Migrate()


#@login.user_loader
#def load_user(user_id):
#    from app.models import User
#    user = User.query.get(int(user_id))
#    return user


login.login_view = 'auth.login'
#login.login_message = 'Please log in to access this page.'
login.login_message_category = 'warning'
