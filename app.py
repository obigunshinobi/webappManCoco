from flask import Flask, request, render_template, redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import qrcode
from flask import send_file
from io import BytesIO
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from flask_login import UserMixin
import base64
import random




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Use SQLite for development
app.config['SECRET_KEY'] = '123456789'  # Add this line


db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    stamps = db.relationship('Stamp', backref='user', lazy='dynamic')
    is_merchant = db.Column(db.Boolean)

class Stamp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    collected = db.Column(db.Boolean, default=False)

    # Add any other fields you want for the stamp


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user is not None:
            login_user(user)
            if user.is_merchant:
                return redirect(url_for('merchant'))  # Redirect merchant users to the merchant page
            else:
                return redirect(url_for('home'))  # Redirect customer users to the home page
        else:
            return "Invalid username"
    else:
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')  # You'll need to handle passwords securely in a real application
        user = User.query.filter_by(username=username).first()
        if user is None:
            # The username is available, so create a new user
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully!')  # Flash a success message
            return redirect(url_for('home'))  # Redirect to the home page after successful registration
        else:

            return "Username is already taken"
    else:
        # render the registration page
        return render_template('register.html')



@app.route('/stamps')
@login_required
def stamps():
    # This is just a placeholder - you'll need to get the actual current user's ID
    current_user_id = 1
    stamps = Stamp.query.filter_by(user_id=current_user_id).all()
    return render_template('stamps.html', stamps=stamps)

@app.route('/add_stamp', methods=['GET', 'POST'])
def add_stamp():
    if request.method == 'POST':
        # Here you'd normally create a new stamp in your database
        # and get an ID for it. For this example, we'll just use a random number.
        stamp_id = random.randint(1000, 9999)

        # Create a new stamp and add it to the database
        new_stamp = Stamp(id=stamp_id, user_id=current_user.id)
        db.session.add(new_stamp)
        db.session.commit()

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(stamp_id)
        qr.make(fit=True)

        img = qr.make_image(fill_color="orange", back_color="#1f2951")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Pass the base64 string to the template
        return render_template('add_stamp.html', img_data=img_str)
    else:
        return render_template('add_stamp.html')

@app.route('/generate_qr/', defaults={'stamp_id': None})
@app.route('/generate_qr/<stamp_id>')
@login_required
def generate_qr(stamp_id):
    # Get the stamp
    if stamp_id is None:
        # If no stamp_id is provided, create a new stamp
        stamp = Stamp.query.filter_by(user_id=current_user.id, collected=False).first()
        if stamp is None:
            stamp = Stamp(user_id=current_user.id, collected=False)
            db.session.add(stamp)
            db.session.commit()
    else:
        stamp = Stamp.query.get(stamp_id)
        if stamp is None:
            return "Stamp not found", 404

    # Check if the logged-in user is the owner of the stamp
    if stamp.user_id != current_user.id:
        return "Access denied", 403

    # Generate a QR code with the stamp ID
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_data = f"{stamp.id}-{current_user.id}"
    qr.add_data(qr_data)
    qr.make(fit=True)

    print(f"Generated QR code with data: {qr_data}")

    img = qr.make_image(fill='black', back_color='white')

    # Convert the image to a base64 string
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return render_template('generate_qr.html', qr_code=img_str)


@app.route('/scan_qr', methods=['GET'])
@login_required
def scan_qr():
    if not current_user.is_merchant:
        return redirect(url_for('error'))  # Redirect non-merchant users to the error page
    return render_template('scan.html')  # Render the page with a QR code scanner



@app.route('/validate_stamp/<int:stamp_id>-', defaults={'user_id': None})
@app.route('/validate_stamp/<int:stamp_id>-<int:user_id>', methods=['POST'])
def validate_stamp(stamp_id, user_id):
    # Look up the stamp by ID
    stamp = Stamp.query.get(stamp_id)

    if stamp is None:
        # The stamp doesn't exist
        return 'Stamp not found', 404

    if stamp.collected:
        # The stamp has already been collected
        return 'Stamp already collected', 409

    # Check if the provided user_id matches the stamp's user_id
    if user_id is not None and user_id != stamp.user_id:
        return 'Incorrect user ID', 403

    # Validate and collect the stamp
    stamp.collected = True
    db.session.commit()

    return 'Stamp collected', 200

@app.route('/error')
def error():
    error_message = "An error occurred."  # Replace this with the actual error message
    return render_template('error.html', error_message=error_message)

@app.route('/success')
def success():
    success_message = "Operation successful."  # Replace this with the actual success message
    return render_template('success.html', success_message=success_message)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/merchant')
@login_required
def merchant():
    if not current_user.is_merchant:
        return redirect(url_for('error'))
    return render_template('merchant.html', merchant=current_user)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:  # You'll need to add an 'is_admin' field to your User model
        return redirect(url_for('error'))
    return render_template('admin.html')

@app.route('/')
@login_required
def home():
    if current_user.is_merchant:
        return render_template('merchant.html', merchant=current_user)
    else:
        # Get the current user's collected stamps
        stamps = Stamp.query.filter_by(user_id=current_user.id, collected=True).all()

        # Pass the stamps to the template
        return render_template('home.html', stamps=stamps)




@app.route('/debug')
def debug():
    users = User.query.all()  # Get all users
    for user in users:
        print(f'User {user.id}: {user.username}')  # Print user details

    stamps = Stamp.query.all()  # Get all stamps
    for stamp in stamps:
        print(f'Stamp {stamp.id} for user {stamp.user_id}')  # Print stamp details

    return 'Check your console for output'


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc')