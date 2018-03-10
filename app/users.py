"""Define User class template and behaviours"""
from flask_login import UserMixin
from flask import current_app
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
import os


class Users(UserMixin, db.Model):
    __table_name__ = "users"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80))
    user_name = db.Column(db.String(40))
    email = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(128))
    phone_number = db.Column(db.String(), nullable=True)
    admin = db.Column(db.Boolean())
    plan = db.Column(db.String(10), nullable=True)
    bankroll = db.Column(db.Float())


    def _set_password(self, password):
        """Generates the password hash"""
        self.password_hash = generate_password_hash(password)

    @property
    def password(self):
        """Enforces integrity, one cannot password"""
        raise AttributeError('Password is write only')

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, name, user_name, email, password, admin=False, phone_number=None, bankroll=None, plan=None):
        self.name = name
        self.email = email
        self.admin = admin
        self.user_name = user_name
        self._set_password(password)

    def __repr__(self):
        """__repr__"""
        return "<user{} {} {} {}>".format(self.id, self.user_name, self.email, self.admin)

    def set_plan(self, plan):
        """ Sets the plan as a string represetntations of the class name"""
        self.plan = plan

    def set_bankroll(self, bankroll):
        """called upon once a user decides to credit his acount with cash"""
        self.bankroll = bankroll

    def set_phone_number(self, phone_number):
        """ it is not all that imperative that a user acoount should hold the users phone number at registration
        this interface will facilitate such updates after the user has registered and he/she can update the information
        at their an arbitrary point in time
        :param: a phone number in form of a string
        :returns: None or raise error if input is not string"""
        if not isinstance(phone_number, str):
            raise ValueError("Unexpected input for phone number, should be string")
        self.phone_number = phone_number

    def insert_user(self):
        """Adds a new user object to the database"""
        db.session.add(self)
        db.session.commit()
        
    def update_email(self, email):
        """speaks for itself: parameter: a string representing the email"""
        self.email = email
        db.session.commit()
        return
    
    def update_plan(self, plan):
        """:parameter: plan as a string"""
        self.plan = plan
        db.session.commit()
        return
    
    def update_password(self, password):
        """:parameter: password as a string"""
        self._set_password(password)
        db.session.commit()
        return

    @staticmethod
    def insert_test_admin():
        """ add the super user admin"""
        app = current_app._get_current_object()
        name = app.config['EANMBLE_ADMIN_NAME']
        email = app.config['EANMBLE_ADMIN_EMAIL']
        password = app.config['EANMBLE_ADMIN_PASSWORD']
        user_name = app.config['EANMBLE_ADMIN_USER_NAME']
        admin = True
        phone_number = app.config['EANMBLE_ADMIN_PHONE_NUMBER']
        bankroll = None
        plan = None
        admin = Users(name = name, user_name=user_name, email=email, password=password,
                      admin=admin, phone_number=phone_number, bankroll=bankroll, plan=plan)
        try:
            db.session.add(admin)
            db.session.commit()
        except OperationalError as e:
            db.session.rollback()
            return False
        return True

    @staticmethod
    def insert_admin():
        """Add a test super user account"""
        name = os.environ.get('EANMBLE_ADMIN_NAME')
        email = os.environ.get('EANMBLE_ADMIN_EMAIL')
        password = os.environ.get('EANMBLE_ADMIN_PASSWORD')
        user_name = os.environ.get('EANMBLE_ADMIN_USER_NAME')
        admin = True
        phone_number = os.environ.get('EANMBLE_ADMIN_PHONE_NUMBER')
        bankroll = None
        plan = None
        admin = Users(name = name, user_name=user_name, email=email, password=password,
                      admin=admin, phone_number=phone_number, bankroll=bankroll, plan=plan)
        try:
            db.session.add(admin)
            db.session.commit()
        except OperationalError as e:
            db.session.rollback()
            return False
        return True


@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))
