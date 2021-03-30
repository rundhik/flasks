from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_rbac import RBAC
from flask_bcrypt import Bcrypt

apl = Flask(__name__, template_folder='../', static_folder='../assets/')
apl.config['SECRET_KEY'] = 'R4H4514_B4N633DD!@#$'
apl.config['CSRF_ENABLED'] = True
apl.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/flasks?charset=utf8mb4'
apl.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
apl.config['RBAC_USE_WHITE'] = False

#### Constanta ####

db = SQLAlchemy(apl)
rbac = RBAC(apl)
bcrypt = Bcrypt()

login_manager = LoginManager(apl)
## I'ts automatically redirect to default set auth page when 
## views controller added @login_required decorator
login_manager.login_view = 'login'




#### Models ####

from flask_login import (
    UserMixin,
)

class Users(db.Model, UserMixin):
    __tablename__ = 'frbac_users'

    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(25), index=True)
    password = db.Column('password', db.String(191))

    def set_password(self, katasandi):
        self.password = bcrypt.generate_password_hash(katasandi).decode('utf-8')

    def check_password(self, katasandi):
        return bcrypt.check_password_hash(self.password, katasandi)


#### Forms ####

from flask_wtf import Form as Formulir
from wtforms import ( 
    StringField, PasswordField, SubmitField, HiddenField, BooleanField,
)
from wtforms.validators import (
    DataRequired,
)

class LoginFormulir(Formulir):
    username = StringField('username', validators=[DataRequired(message='Wajib diisi')])
    password = PasswordField('password', validators=[DataRequired(message='Wajib diisi')])
    submit = SubmitField('masuk')


#### Controllers ####

from flask import (
    request, render_template, flash, redirect, url_for, jsonify,
)
from flask_login import ( 
    login_required, login_user, logout_user
)


## Flask-Login Need user_loader first ##
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@apl.route('/login', methods=['GET', 'POST'])
def login():
    formulir = LoginFormulir()
    return render_template('flask-rbac/login.html', formulir=formulir)

@apl.route('/')
@login_required
def index():
    return render_template('flask-rbac/index.html')



#### Customizing ####

@apl.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

#### Execute App ####

if __name__ == '__main__':
    apl.run(debug=True)