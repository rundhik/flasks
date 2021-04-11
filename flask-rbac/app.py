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
from flask_rbac import (
    UserMixin, RoleMixin,
)

# # Define many-to-many relationships
roles_parents = db.Table(
    'frbac_roles_parents',
    db.Column('role_id', db.Integer(), db.ForeignKey('frbac_roles.id')),
    db.Column('parent_id', db.Integer(), db.ForeignKey('frbac_roles.id')),
)

class Roles(db.Model, RoleMixin):
    __tablename__ = 'frbac_roles'

    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(50))
    parents = db.relationship(
        'Roles',
        secondary=roles_parents,
        primaryjoin=( id == roles_parents.c.role_id ),
        secondaryjoin=( id == roles_parents.c.parent_id),
        backref=db.backref('children', lazy='dynamic')
    )

    def __init__(self, name):
        RoleMixin.__init__(self)
        self.name = name

    def get_name(self):
        """Return the name of this role"""
        return self.name

    def add_parent(self, parent):
        # # You don't need to add this role to parent's children set,
        # # relationship between roles would do this work automatically
        self.parents.append(parent)

    def add_parents(self, *parents):
        for parent in parents:
            self.add_parent(parent)

    def get_children(self):
        for child in self.children:
            yield child
            for grandchild in child.get_children():
                yield grandchild

    @staticmethod
    def get_by_name(name):
        return Roles.query.filter_by(name=name).first()

    @classmethod
    def get_all(cls):
        """Return all existing roles
        """
        return cls.roles



# # Define many-to-many relationships
users_roles = db.Table(
    'frbac_users_roles',
    db.Column('user_id', db.Integer(), db.ForeignKey('frbac_users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('frbac_roles.id')),
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

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.id)

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        for role in roles:
            self.add_role(role)

    def get_roles(self):
        for role in self.roles:
            yield role

    roles = db.relationship(
        'Roles',
        secondary=users_roles,
        backref=db.backref('roles', lazy='dynamic')
    )


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
    render_template_string,
)
from flask_login import ( 
    login_required, login_user, logout_user, current_user,
)


## Flask-Login Need user_loader first ##
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

## Now lets flask-rbac recognizing user_loader from flask-login
rbac.set_user_loader(lambda: current_user)
rbac.set_role_model(Roles)
rbac.set_user_model(Users)

@apl.route('/login', methods=['GET', 'POST'])
@rbac.allow(['anonymous'],methods=['GET'])
def login():
    formulir = LoginFormulir()
    if formulir.validate_on_submit():
        data = Users.query.filter_by(username=formulir.username.data).first()

        if data and data.check_password(formulir.password.data):
            login_user(data)
            flash('Login berhasil', category='success')
            return redirect( url_for('index') )
        elif not data:
            logout_user()
            flash('Username tidak ditemukan', category='error')
        else:
            logout_user()
            flash('Password salah', category='error')

    return render_template('flask-rbac/login.html', formulir=formulir)

@apl.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('flask-rbac/index.html')

@apl.route('/admin', methods=['GET', 'POST'])
@rbac.allow(['superadmin'], ['GET', 'POST'])
def admin_page():
    return render_template_string("""
    Halaman Admin
    """)

@apl.route('/logout')
def logout():
    formulir = LoginFormulir()
    logout_user()
    return redirect( url_for('login') )


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
