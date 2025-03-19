from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash



app=Flask(__name__) 

app.secret_key='your_secret_key' 

# MongoDB Setup
app.config["MONGO_URI"] = "mongodb://localhost:27017/bank_system"
mongo = PyMongo(app)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        
        if not email or not password:
            flash("Email and password are required!", "danger")
            return redirect(url_for('signup'))

        
        hashed_password = generate_password_hash(password)

        
        if mongo.db.users.find_one({'email': email}):
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('login'))  

        
        try:
            mongo.db.users.insert_one({
                'email': email,
                'password': hashed_password,
                'balance': 0  
            })
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error signing up: {str(e)}", "danger")
            return redirect(url_for('signup'))

    return render_template('index.html')  





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
            return redirect(url_for('login'))  
    return render_template('index.html')  




@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        flash("You must log in first!", "danger")
        return redirect(url_for('home'))

    user = mongo.db.users.find_one({'email': session['user_email']})
    user_balance = user.get('balance', 0)  
    return render_template('dashboard.html', user_balance=user_balance)




@app.route('/')
def home():
    return render_template('index.html')


@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user_email' not in session:
        flash("You must log in first!", "danger")
        return redirect(url_for('home'))

    email = session['user_email']
    deposit_amount = float(request.form['amount'])

   
    if deposit_amount <= 0:
        flash("Deposit amount must be greater than zero.", "danger")
        return redirect(url_for('dashboard'))

    
    user = mongo.db.users.find_one({'email': email})

    if 'balance' not in user:
        user['balance'] = 0  

    
    new_balance = user['balance'] + deposit_amount

   
    mongo.db.users.update_one({'email': email}, {'$set': {'balance': new_balance}})

    flash(f"Deposited ${deposit_amount}. New balance: ${new_balance}", "success")
    return redirect(url_for('dashboard'))






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

    
    new_balance = user['balance'] - withdraw_amount
    mongo.db.users.update_one({'email': session['user_email']}, {'$set': {'balance': new_balance}})

    flash(f"Successfully withdrew ${withdraw_amount}.", "success")
    return redirect(url_for('dashboard'))




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

    
    new_balance = user['balance'] - transfer_amount
    mongo.db.users.update_one({'email': session['user_email']}, {'$set': {'balance': new_balance}})
    
    new_recipient_balance = recipient['balance'] + transfer_amount
    mongo.db.users.update_one({'email': recipient_email}, {'$set': {'balance': new_recipient_balance}})

    flash(f"Successfully transferred ${transfer_amount} to {recipient_email}.", "success")
    return redirect(url_for('dashboard'))



@app.route('/logout')
def logout():
    session.pop('user_email', None)  
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))




if __name__ == '__main__':
    app.run(debug=True)
