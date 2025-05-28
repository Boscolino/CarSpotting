from flask import Flask, render_template, request, redirect, url_for, flash, session # Added session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, gettext as _ # Added Babel and gettext
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/cars.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'your secret key here' # Needed for flash messages and session
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Create upload folder

# Babel Configuration
LANGUAGES = ['en', 'it']
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
babel = Babel(app)

db = SQLAlchemy(app)

@babel.localeselector
def get_locale():
    language = session.get('language')
    if language and language in LANGUAGES:
        return language
    return request.accept_languages.best_match(LANGUAGES)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String, nullable=False)
    model = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer)
    engine = db.Column(db.String)
    horsepower = db.Column(db.Integer)
    other_specs = db.Column(db.Text)

class CarImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    image_filename = db.Column(db.String, nullable=False)
    caption = db.Column(db.String)

def add_car(make, model, year=None, engine=None, horsepower=None, other_specs=None):
    new_car = Car(
        make=make,
        model=model,
        year=year,
        engine=engine,
        horsepower=horsepower,
        other_specs=other_specs
    )
    db.session.add(new_car)
    db.session.commit()
    return new_car

@app.route('/')
def index_route():
    all_cars = Car.query.all()
    greeting = _("Welcome to Car Specs")
    return render_template('index.html', cars=all_cars, greeting=greeting)

@app.route('/setlang/<lang_code>')
def set_language(lang_code):
    if lang_code in LANGUAGES:
        session['language'] = lang_code
    return redirect(request.referrer or url_for('index_route'))

@app.route('/car/<int:car_id>')
def car_detail_route(car_id):
    selected_car = Car.query.get_or_404(car_id)
    car_images = CarImage.query.filter_by(car_id=car_id).all()
    return render_template('car_detail.html', car=selected_car, images=car_images)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['GET', 'POST'])
def upload_route():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            car_id = request.form.get('car_id')
            caption = request.form.get('caption', '') # Get caption, default to empty string

            if not car_id:
                flash('Car ID is missing.')
                return redirect(request.url)
            
            selected_car = Car.query.get(car_id)
            if not selected_car:
                flash('Invalid Car ID.')
                return redirect(request.url)

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            new_image = CarImage(car_id=car_id, image_filename=filename, caption=caption)
            db.session.add(new_image)
            db.session.commit()

            flash('Image uploaded and associated with car successfully!')
            return redirect(url_for('car_detail_route', car_id=car_id))
        else:
            flash('Allowed image types are: png, jpg, jpeg, gif')
            return redirect(request.url)

    all_cars = Car.query.all() # For GET request, pass cars to template
    return render_template('upload_image.html', cars=all_cars)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Car.query.first(): # Check if db is empty
            add_car('Toyota', 'Camry', 2023, '2.5L 4-Cylinder', 203, '{"trim": "LE", "color": "White"}')
            add_car('Honda', 'Civic', 2022, '1.5L Turbo', 180)
            add_car('Ford', 'Mustang', 2024, '5.0L V8', 450, '{"trim": "GT", "color": "Red"}')
    app.run(debug=True)
