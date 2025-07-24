from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ✅ MongoDB Configuration
app.config['MONGO_URI'] = "mongodb+srv://Charlesjnr:Okorochidozie7%40@cluster0.e2m9njj.mongodb.net/crypto_wallet?retryWrites=true&w=majority"
mongo = PyMongo(app)

# ✅ File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ Home & User Routes -------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        filename = 'default.png'
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic and allowed_file(profile_pic.filename):
                filename = secure_filename(profile_pic.filename)
                profile_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(profile_path)

        user = {
            'name': request.form['name'],
            'username': request.form['username'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'password': generate_password_hash(request.form['password']),
            'preferred_coin': request.form['preferred_coin'],
            'profile_pic': filename,
            'status': 'pending',
            'wallet_balance': 5.0
        }

        mongo.db.users.insert_one(user)
        flash("Account created! Awaiting approval.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check for status field, not "approved"
        user = mongo.db.users.find_one({'email': email, 'status': 'approved'})

        if user and check_password_hash(user['password'], password):
            session['user'] = user['email']
            flash('Login successful', 'success')
            return redirect(url_for('wallet'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/wallet')
def wallet():
    if 'user' not in session:
        flash("Please login.")
        return redirect(url_for('login'))

    # Get user from the database using session
    user = mongo.db.users.find_one({'email': session['user']})
    
    return render_template('wallet.html', user=user)


@app.route('/dashboardd')
def dashboard():
    if 'user' not in session:
        flash("Please login.", "warning")
        return redirect(url_for('login'))

    user = mongo.db.users.find_one({'email': session['user']})
    user_balance = user.get('wallet_balance', 0.00)
    return render_template('wallettt.html', user=user, user_balance=user_balance)

# ------------------ Admin Auth & Dashboard -------------------

ADMIN_CREDENTIALS = {
    "email": "admin@crypto.com",
    "password": "admin123"
}

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == ADMIN_CREDENTIALS["email"] and password == ADMIN_CREDENTIALS["password"]:
            session['admin_logged_in'] = True
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        flash("Invalid admin credentials.", "danger")
    return render_template('admin_login.html')

@app.route('/admin/settings')
def admin_settings():
    # Your logic here (e.g., render settings page)
    return render_template('admin_settings.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Logged out.", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash("Admin login required.", "warning")
        return redirect(url_for('admin_login'))
    users = mongo.db.users.find()
    return render_template('admin_dashboard.html', users=users)

# ------------------ Admin: Users Management -------------------

@app.route('/admin/users')
def admin_users():
    users = mongo.db.users.find()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        updated_data = {
            "username": request.form['username'],
            "email": request.form['email'],
            "wallet_balance": float(request.form['wallet_balance'])
        }

        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updated_data}
        )

        flash("User updated successfully.", "success")
        return redirect(url_for('admin_users'))

    return render_template('edit_user.html', user=user)

@app.route('/dashboard/update_balance', methods=['POST'])
def update_balance():
    if 'user' not in session:
        flash("Please login.", "warning")
        return redirect(url_for('login'))

    new_balance = float(request.form['wallet_balance'])

    mongo.db.users.update_one(
        {'email': session['user']},
        {'$set': {'wallet_balance': new_balance}}
    )

    flash("Wallet balance updated!", "success")
    return redirect(url_for('dashboard'))

@app.route('/admin/user/<user_id>/view')
def view_user(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    return render_template('view_user.html', user=user)

@app.route('/admin/user/<user_id>/delete')
def delete_user(user_id):
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    flash("User deleted.", "danger")
    return redirect(url_for('admin_users'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form['username']
    email = request.form['email']
    theme = request.form.get('theme')

    file = request.files.get('profile_pic')
    filename = 'default.png'

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join('static/uploads', filename))

    mongo.db.users.update_one(
        {'email': session['user']},
        {'$set': {
            'username': username,
            'email': email,
            'theme': theme,
            'profile_pic': filename
        }}
    )

    flash('Profile updated successfully.')
    return redirect(url_for('settings'))

# ------------------ Admin: Approval System -------------------

@app.route('/admin/approvals')
def admin_approvals():
    pending_users = mongo.db.users.find({"status": "pending"})
    return render_template('admin_approvals.html', users=pending_users)

@app.route('/admin/approvals/<user_id>/approve')
def approve_user(user_id):
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": "approved"}}
    )
    flash("User approved.", "success")
    return redirect(url_for('admin_approvals'))

@app.route('/admin/approvals/<user_id>/reject')
def reject_user(user_id):
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": "rejected"}}
    )
    flash("User rejected.", "danger")
    return redirect(url_for('admin_approvals'))

# ------------------ Messages / Contact -------------------

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        mongo.db.messages.insert_one({
            "name": request.form['name'],
            "email": request.form['email'],
            "content": request.form['message']
        })
        flash("Message sent!", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/messages')
def admin_messages():
    messages = mongo.db.messages.find()
    return render_template('admin_messages.html', messages=messages)

@app.route('/admin/messages/<msg_id>/reply', methods=['GET', 'POST'])
def reply_message(msg_id):
    msg = mongo.db.messages.find_one({"_id": ObjectId(msg_id)})
    if request.method == 'POST':
        reply_text = request.form['reply']
        mongo.db.messages.update_one(
            {"_id": ObjectId(msg_id)},
            {"$set": {"reply": reply_text}}
        )
        send_email_reply(msg['email'], reply_text)
        flash("Reply sent!", "success")
        return redirect(url_for('admin_messages'))
    return render_template('reply_message.html', message=msg)

def send_email_reply(to_email, content):
    EMAIL_ADDRESS = 'your@email.com'
    EMAIL_PASSWORD = 'yourpassword'
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = 'Reply from Admin'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ------------------ Other Routes -------------------
# Home Page
@app.route('/home')
def index():
    return render_template('index.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Market Page
@app.route('/market')
def market():
    return render_template('market.html')

# Service Page
@app.route('/service')
def service():
    return render_template('service.html')

# Roadmap Page
@app.route('/roadmap')
def roadmap():
    return render_template('roadmap.html')

@app.route('/assets')
def assets(): return render_template('assets.html')

@app.route('/deposit')
def deposit(): return render_template('deposit.html')

@app.route('/buy')
def buy(): return render_template('buy.html')

@app.route('/with')
def withdraw(): return render_template('with.html')

@app.route('/mining')
def mining(): return render_template('min.html')

@app.route('/portfolio')
def portfolio(): return render_template('portfolio.html')

@app.route('/transactions')
def transactions(): return render_template('history.html')

@app.route('/tools')
def tools(): return render_template('tools.html')

@app.route('/settings')
def settings(): return render_template('settings.html')

@app.route('/support')
def support(): return render_template('support.html')

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/market')
def market(): return render_template('market.html')

@app.route('/service')
def service(): return render_template('service.html')

@app.route('/roadmap')
def roadmap(): return render_template('roadmap.html')

@app.route('/feature')
def feature(): return render_template('feature.html')

@app.route('/token')
def token(): return render_template('token.html')

@app.route('/faq')
def faq(): return render_template('faq.html')

@app.route('/404')
def page_not_found(): return render_template('404.html')

# ------------------ Run App -------------------

if __name__ == '__main__':
    app.run(debug=True)
