import glob
import os

from wtforms import Form, BooleanField, StringField
from wtforms import SelectField, TextAreaField, validators

EXTENSION = '.png'


def get_basename(img):
    return os.path.splitext(os.path.basename(img))[0]


def get_logos(subdir='python'):
    logos = glob.glob(os.path.join('assets', subdir, '*' + EXTENSION))
    return [(logo, get_basename(logo)) for logo in logos]


DEFAULT_LOGOS = get_logos()


class ImageForm(Form):
    name = StringField('Banner Name', [
        validators.DataRequired(),
        validators.Length(max=100)
    ])
    image_url1 = SelectField(
        'Pick a Logo',
        choices=DEFAULT_LOGOS
    )
    image_url2 = StringField('Second Image URL', [
        validators.DataRequired(),
        validators.Length(max=500)
    ])
    text = TextAreaField('Text for Banner', [
        validators.DataRequired(),
        validators.Length(max=500)
    ])
    background = BooleanField('Use Second Image as Background?', default=True)
