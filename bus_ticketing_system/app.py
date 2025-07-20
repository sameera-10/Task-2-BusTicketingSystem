from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# Flask app setup
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Firebase Admin SDK setup
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# ───── ROUTES ─────────────────────────────────────────────

# Welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html')


# ───── AUTH ───────────────────────────────────────────────

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        users_ref = db.collection('users')
        existing = users_ref.where('email', '==', email).stream()

        if any(existing):
            return render_template('signup.html', error="Email already exists.")

        users_ref.add({
            'email': email,
            'password': password
        })

        return redirect(url_for('login'))

    return render_template('signup.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).where('password', '==', password).stream()

        user_found = None
        for user in query:
            user_found = user
            break

        if user_found:
            session['user'] = user_found.id
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials.")

    return render_template('login.html')


# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ───── DASHBOARD ──────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# ───── SEARCH BUSES ──────────────────────────────────────

@app.route('/search', methods=['GET', 'POST'])
def search_bus():
    if request.method == 'POST':
        from_city = request.form['from']
        to_city = request.form['to']
        travel_date = request.form['date']
        seats = request.form['seats']

        # Simulated available buses
        available_buses = [
            {"bus_name": "GreenLine Travels", "bus_id": "G123", "time": "10:00 AM", "price": "300"},
            {"bus_name": "RedBus Express", "bus_id": "R456", "time": "2:30 PM", "price": "450"},
            {"bus_name": "Blue Star", "bus_id": "B789", "time": "6:45 PM", "price": "350"}
        ]

        return render_template("available_buses.html",
                               buses=available_buses,
                               from_city=from_city,
                               to_city=to_city,
                               seats=seats,
                               travel_date=travel_date)

    return render_template("search_bus.html")


# ───── SELECT BUS → PAYMENT ──────────────────────────────

@app.route('/select_bus', methods=['POST'])
def select_bus():
    selected_data = {
        'bus_id': request.form['bus_id'],
        'bus_name': request.form['bus_name'],
        'from_city': request.form['from_city'],
        'to_city': request.form['to_city'],
        'travel_date': request.form['travel_date'],
        'price': request.form['price'],
        'seats': request.form['seats']  # ✅ Add this line
    }

    return render_template('payment.html', booking=selected_data)


# ───── CONFIRM PAYMENT ───────────────────────────────────
@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    booking_data = {
        'bus_name': request.form['bus_name'],
        'from_city': request.form['from_city'],
        'to_city': request.form['to_city'],
        'travel_date': request.form['travel_date'],
        'price': request.form['price'],
        'seats': request.form['seats'],  # ✅ Add this line
        'card_number': request.form['card_number'],
        'card_holder': request.form['card_holder']
    }

    db.collection('bookings').add(booking_data)

    return render_template('success.html', booking=booking_data)



# ───── VIEW BOOKINGS ─────────────────────────────────────

@app.route('/view_bookings')
def view_bookings():
    bookings_snapshot = db.collection('bookings').get()
    bookings = []

    for record in bookings_snapshot:
        data = record.to_dict()
        bookings.append({
    'from': data.get('from_city', data.get('from', '')),
    'to': data.get('to_city', data.get('to', '')),
    'date': data.get('travel_date', data.get('date', '')),
    'seats': data.get('seats', ''),
    'bus': data.get('bus_name', ''),
    'price': data.get('price', '')
})


    return render_template('view_bookings.html', bookings=bookings)


# ───── BOOK TICKET (Optional legacy) ─────────────────────

@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket():
    if request.method == 'POST':
        from_city = request.form['from']
        to_city = request.form['to']
        travel_date = request.form['date']
        seats = int(request.form['seats'])

        ticket_data = {
            'from': from_city,
            'to': to_city,
            'date': travel_date,
            'seats': seats
        }

        db.collection('tickets').add(ticket_data)

        return redirect(url_for('dashboard'))

    return render_template('book_ticket.html')


# ───── MAIN ──────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
