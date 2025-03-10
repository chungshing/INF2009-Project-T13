from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    api_key = db.Column(db.String(40), unique=True, nullable=True)

    # One-to-many relationship to Image
    images = db.relationship('Image', backref='uploader', lazy=True)

    # Optional: One-to-many relationship to NutritionalIntake
    # (Requires the `user` relationship in NutritionalIntake)
    nutritional_intakes = db.relationship('NutritionalIntake', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Image('{self.filename}')"

class NutritionalIntake(db.Model):
    __tablename__ = 'nutritional_intake'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dish_name = db.Column(db.String(255), nullable=False)
    date_consumed = db.Column(db.DateTime, default=datetime.utcnow)
    energy_kcal = db.Column(db.Float, default=0.0)
    protein_g = db.Column(db.Float, default=0.0)
    carbohydrate_g = db.Column(db.Float, default=0.0)
    sodium_mg = db.Column(db.Float, default=0.0)
    total_fat_g = db.Column(db.Float, default=0.0)
    saturated_fat_g = db.Column(db.Float, default=0.0)
    dietary_fibre_g = db.Column(db.Float, default=0.0)
    cholesterol_mg = db.Column(db.Float, default=0.0)
    cholesterol_g = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return (f"NutritionalIntake(User ID: {self.user_id}, Dish: '{self.dish_name}', "
                f"Energy: {self.energy_kcal} kcal, Protein: {self.protein_g} g, "
                f"Carbs: {self.carbohydrate_g} g, Sodium: {self.sodium_mg} mg, "
                f"Total Fat: {self.total_fat_g} g, Saturated Fat: {self.saturated_fat_g} g, "
                f"Fibre: {self.dietary_fibre_g} g, Cholesterol: {self.cholesterol_mg} mg/{self.cholesterol_g} g)")