from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banners.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # mute warnings

db = SQLAlchemy(app)


class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url1 = db.Column(db.String(30))
    image_url2 = db.Column(db.String(200))
    text = db.Column(db.String(200))
    background = db.Column(db.Boolean)

    def __init__(self, banner):
        self.image_url1 = banner.image1
        self.image_url2 = banner.image2
        self.text = banner.text
        self.background = banner.background

    def __repr__(self):
        return '<Banner %r>' % self.text


if __name__ == '__main__':
    db.create_all()
