from collections import namedtuple
from functools import wraps
import logging
import os

from flask import abort, render_template, flash, redirect
from flask import request, send_file, session, url_for

from forms import ImageForm, get_logos
from model import app, db, Banner

from banner.banner import generate_banner


logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)

PYBITES_SUBDIR = 'pybites'

ImgBanner = namedtuple('Banner', 'name image1 image2 text background')


def login_required(test):
    '''From RealPython Flask course'''
    @wraps(test)
    def wrap(*args, **kwargs):
        if session.get('logged_in'):
            return test(*args, **kwargs)
        else:
            flash('You need to log in first')
            return redirect(url_for('login'))
    return wrap


def _store_banner(data):
    banner = Banner.query.filter_by(name=data.name).first()
    # if banner in db, update record, if not add it
    if banner:
        banner.name = data.name
        banner.image_url1 = data.image1
        banner.image_url2 = data.image2
        banner.text = data.text
        banner.background = data.background
    else:
        banner = Banner(data)
        db.session.add(banner)
    db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
def login():
    user = None
    status_code = 200
    if request.method == 'POST':
        user = request.form.get('username')
        password = request.form.get('password')
        if user != os.getenv('USER') or password != os.getenv('PASSWORD'):
            flash('Invalid credentials')
            status_code = 401
        else:
            session['logged_in'] = user
            return redirect(url_for('index'))
    return render_template('login.html', user=user), status_code


def _get_form():
    '''Get form. Logged out = python logo, logged in pybites logos'''
    form = ImageForm(request.form)

    # https://stackoverflow.com/a/16392248
    if session.get('logged_in'):
        logos = get_logos(subdir=PYBITES_SUBDIR)
        form.image_url1.choices = logos

    return form


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/<bannerid>', methods=['GET', 'POST'])
def index(bannerid=None):
    form = _get_form()
    cached_banners = Banner.query.all()

    # if a get request with valid banner id prepopulate form
    if request.method == 'GET':
        if bannerid:
            if not bannerid.isdigit():
                abort(400)

            banner = Banner.query.filter_by(id=bannerid).first()
            if not banner:
                abort(404)

            form.name.data = banner.name
            form.image_url1.data = banner.image_url1
            form.image_url2.data = banner.image_url2
            form.text.data = banner.text
            form.background.data = banner.background

    # else if post request validate and generate banner image
    elif request.method == 'POST' and form.validate():
        name = form.name.data
        image1 = form.image_url1.data
        image2 = form.image_url2.data
        text = form.text.data
        background = form.background.data

        banner = ImgBanner(name=name,
                           image1=image1,
                           image2=image2,
                           text=text,
                           background=background)

        if session.get('logged_in'):
            _store_banner(banner)

        try:
            outfile = generate_banner(banner)
        except Exception as exc:
            logger.error('Error generating banner, exc: {}'.format(exc))
            abort(400)

        if os.path.isfile(outfile):
            return send_file(outfile, mimetype='image/png', cache_timeout=1)
        else:
            logger.error('No output file {}'.format(outfile))
            abort(400)

    return render_template('imageform.html', form=form, banners=cached_banners)


if __name__ == "__main__":
    app.run(debug=True)
