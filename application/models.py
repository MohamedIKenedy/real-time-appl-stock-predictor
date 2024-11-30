from application import db, bcrypt, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    
    @property 
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    
    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)



# def init_db():
#     db.create_all()

#     # Create a test user
#     new_user = User('a@a.com', 'aaaaaaaa')
#     new_user.display_name = 'Nathan'
#     db.session.add(new_user)
#     db.session.commit()

#     new_user.datetime_subscription_valid_until = datetime.datetime(2019, 1, 1)
#     db.session.commit()


# if __name__ == '__main__':
#     init_db()
