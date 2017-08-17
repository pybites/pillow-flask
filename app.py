from collections import namedtuple
from functools import wraps
import logging
import os

from flask import abort, render_template, flash, redirect
from flask import request, send_file, session, url_for

from forms import ImageForm
from model import app, db, Banner

from banner.banner import generate_banner
from banner.banner import DEFAULT_OUTPUT_FILE as outfile


logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)

ImgBanner = namedtuple('Banner', 'image1 image2 text background')


def login_required(test):
    '''From RealPython Flask course'''
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to log in first')
            return redirect(url_for('login'))
    return wrap


def _store_banner(data):
    banner = Banner.query.filter_by(text=data.text).first()
    # if banner in db, update record, if not add it
    if banner:
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


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/<bannerid>', methods=['GET', 'POST'])
def index(bannerid=None):
    form = ImageForm(request.form)
    cached_banners = Banner.query.all()

    # if a get request with valid banner id prepopulate form
    if request.method == 'GET':
        if bannerid:
            if not bannerid.isdigit():
                abort(400)

            banner = Banner.query.filter_by(id=bannerid).first()
            if not banner:
                abort(404)

            form.image_url1.data = banner.image_url1
            form.image_url2.data = banner.image_url2
            form.text.data = banner.text
            form.background.data = banner.background

    # else if post request validate and generate banner image
    elif request.method == 'POST' and form.validate():
        image1 = form.image_url1.data
        image2 = form.image_url2.data
        text = form.text.data
        background = form.background.data

        banner = ImgBanner(image1=image1,
                           image2=image2,
                           text=text,
                           background=background)

        if session['logged_in']:
            _store_banner(banner)

        try:
            generate_banner(banner)
        except Exception as exc:
            logger.error('Error generating banner, exc: {}'.format(exc))

        if os.path.isfile(outfile):
            return send_file(outfile, mimetype='image/png', cache_timeout=1)
        else:
            logger.error('No output file {}'.format(outfile))
            abort(400)

    return render_template('imageform.html', form=form, banners=cached_banners)


if __name__ == "__main__":
    app.run(debug=True)
