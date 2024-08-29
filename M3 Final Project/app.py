from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banking.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    balance = db.Column(db.Float, default=0.0)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return jsonify({'message': 'Login successful!'})
    else:
        return jsonify({'message': 'Login failed!'}), 401

@app.route('/deposit', methods=['POST'])
def deposit():
    username = request.form.get('username')
    password = request.form.get('password')
    amount = float(request.form.get('amount'))
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        user.balance += amount
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return jsonify({'message': 'Transaction failed!'}), 401

@app.route('/withdraw', methods=['POST'])
def withdraw():
    username = request.form.get('username')
    password = request.form.get('password')
    amount = float(request.form.get('amount'))
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        if user.balance >= amount:
            user.balance -= amount
            db.session.commit()
            return redirect(url_for('home'))
        else:
            return jsonify({'message': 'Insufficient funds!'}), 400
    else:
        return jsonify({'message': 'Transaction failed!'}), 401

@app.route('/balance', methods=['POST'])
def balance():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return jsonify({'balance': user.balance})
    else:
        return jsonify({'message': 'Failed to retrieve balance!'}), 401
    
@app.route('/view_users')
def view_users():
    users = User.query.all()
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'username': user.username,
            'balance': user.balance
        })
    return jsonify(user_data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
