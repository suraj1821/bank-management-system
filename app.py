from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash



app=Flask(__name__) # Let it use the default method

app.secret_key='your_secret_key' # Required for session management

# MongoDB Setup
app.config["MONGO_URI"] = "mongodb://localhost:27017/bank_system"
mongo = PyMongo(app)


#signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate input
        if not email or not password:
            flash("Email and password are required!", "danger")
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Check if the user already exists
        if mongo.db.users.find_one({'email': email}):
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('login'))  # Redirect to the login page

        # Insert user into MongoDB, ensuring balance is set to 0
        try:
            mongo.db.users.insert_one({
                'email': email,
                'password': hashed_password,
                'balance': 0  # Initial balance is 0
            })
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error signing up: {str(e)}", "danger")
            return redirect(url_for('signup'))

    return render_template('index.html')  # Assuming index.html has the signup form




# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = mongo.db.users.find_one({'email': email})
        
        if user and check_password_hash(user['password'], password):
            session['user_email'] = email
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))  # Stay on the login page for failed login attempts
    return render_template('index.html')  # Handle GET request to show the login form



# Dashboard Route (Protected)
@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        flash("You must log in first!", "danger")
        return redirect(url_for('home'))

    user = mongo.db.users.find_one({'email': session['user_email']})
    user_balance = user.get('balance', 0)  # Get balance, default to 0 if missing
    return render_template('dashboard.html', user_balance=user_balance)



# Home Route (Displays Login and Signup)
@app.route('/')
def home():
    return render_template('index.html')

#deposit route
@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user_email' not in session:
        flash("You must log in first!", "danger")
        return redirect(url_for('home'))

    email = session['user_email']
    deposit_amount = float(request.form['amount'])

    # Validate the deposit amount
    if deposit_amount <= 0:
        flash("Deposit amount must be greater than zero.", "danger")
        return redirect(url_for('dashboard'))

    # Find the user in the database
    user = mongo.db.users.find_one({'email': email})

    if 'balance' not in user:
        user['balance'] = 0  # Set default balance if it doesn't exist

    # Calculate new balance
    new_balance = user['balance'] + deposit_amount

    # Update the user's balance in MongoDB
    mongo.db.users.update_one({'email': email}, {'$set': {'balance': new_balance}})

    flash(f"Deposited ${deposit_amount}. New balance: ${new_balance}", "success")
    return redirect(url_for('dashboard'))





# Withdraw Route
@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user_email' not in session:
        flash("You must log in first!", "danger")
        return redirect(url_for('home'))

    withdraw_amount = float(request.form.get('withdraw_amount', 0))
    user = mongo.db.users.find_one({'email': session['user_email']})

    if withdraw_amount <= 0:
        flash("Withdraw amount must be greater than zero.", "danger")
        return redirect(url_for('dashboard'))

    if user['balance'] < withdraw_amount:
        flash("Insufficient balance.", "danger")
        return redirect(url_for('dashboard'))

    # Update the balance
    new_balance = user['balance'] - withdraw_amount
    mongo.db.users.update_one({'email': session['user_email']}, {'$set': {'balance': new_balance}})

    flash(f"Successfully withdrew ${withdraw_amount}.", "success")
    return redirect(url_for('dashboard'))



# Transfer Route
@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user_email' not in session:
        flash("You must log in first!", "danger")
        return redirect(url_for('home'))

    recipient_email = request.form['recipient_email']
    transfer_amount = float(request.form['transfer_amount'])
    user = mongo.db.users.find_one({'email': session['user_email']})

    if transfer_amount <= 0:
        flash("Transfer amount must be greater than zero.", "danger")
        return redirect(url_for('dashboard'))

    if user['balance'] < transfer_amount:
        flash("Insufficient balance.", "danger")
        return redirect(url_for('dashboard'))

    recipient = mongo.db.users.find_one({'email': recipient_email})
    if not recipient:
        flash("Recipient not found.", "danger")
        return redirect(url_for('dashboard'))

    # Update the balances of both user and recipient
    new_balance = user['balance'] - transfer_amount
    mongo.db.users.update_one({'email': session['user_email']}, {'$set': {'balance': new_balance}})
    
    new_recipient_balance = recipient['balance'] + transfer_amount
    mongo.db.users.update_one({'email': recipient_email}, {'$set': {'balance': new_recipient_balance}})

    flash(f"Successfully transferred ${transfer_amount} to {recipient_email}.", "success")
    return redirect(url_for('dashboard'))


# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_email', None)  # Clear session
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))




if __name__ == '__main__':
    app.run(debug=True)
