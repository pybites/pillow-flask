import glob
import os

from wtforms import Form, BooleanField, StringField
from wtforms import SelectField, TextAreaField, validators

pybites_logos = glob.glob(os.path.join('assets', 'pybites', '*png'))


def get_basename(img):
    return os.path.splitext(os.path.basename(img))[0]


class ImageForm(Form):
    name = StringField('Banner Name', [validators.DataRequired()])
    image_url1 = SelectField(
        'PyBites Logo Theme',
        choices=[(img, get_basename(img)) for img in pybites_logos]
    )
    image_url2 = StringField('Second Image URL', [validators.DataRequired()])
    text = TextAreaField('Text for Banner', [validators.DataRequired()])
    background = BooleanField('Use Second Image as Background?', default=True)
