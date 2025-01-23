from flask import Flask, render_template, request, redirect, flash, url_for
import json
from datetime import datetime, timedelta, date

app = Flask(__name__)
app.secret_key = "supersecretkey"

# File paths for data storage
FRIDGE_FILE = "fridge.json"
HISTORY_FILE = "history.json"

# Load data from JSON files
def load_data():
    try:
        with open(FRIDGE_FILE, "r") as f:
            fridge = json.load(f)
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except FileNotFoundError:
        fridge = {}
        history = []
    return fridge, history

# Save data to JSON files
def save_data(fridge, history):
    with open(FRIDGE_FILE, "w") as f:
        json.dump(fridge, f)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

# Load initial data
fridge, history = load_data()

def check_and_deduct_expired_items():
    expired_items = []
    today = date.today()

    for item, details in list(fridge.items()):
        expiry_date = datetime.strptime(details["expiry_date"], "%Y-%m-%d").date()

        if expiry_date < today:  # Item is expired
            expired_items.append(item)
            fridge[item]["quantity"] = 0  # Deduct quantity (set to 0)
            history.append({"item": item, "quantity": f"{details['quantity']} {details['unit']}", "action": "Expired", "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    save_data(fridge, history)  # Save the updated fridge data
    return expired_items

@app.route('/')
def index():
    expired_items = check_and_deduct_expired_items()  # Check and deduct expired items on loading the index page
    return render_template("index.html", fridge=fridge, expired_items=expired_items)

@app.route('/insert', methods=["GET", "POST"])
def insert():
    global fridge, history
    if request.method == "POST":
        item = request.form["item"]
        quantity = float(request.form["quantity"])
        unit = request.form["unit"]
        expiry_date = request.form["expiry_date"]

        if item not in fridge:
            fridge[item] = {"quantity": 0, "unit": unit, "expiry_date": expiry_date}

        fridge[item]["quantity"] += quantity
        fridge[item]["expiry_date"] = expiry_date
        history.append({"item": item, "quantity": f"{quantity} {unit}", "action": "Insert", "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

        save_data(fridge, history)
        flash(f"{quantity} {unit} of {item} inserted successfully!", "success")
        return redirect(url_for("index"))

    return render_template("insert.html")

@app.route('/consume', methods=["GET", "POST"])
def consume():
    global fridge, history
    if request.method == "POST":
        item = request.form["item"]
        quantity = float(request.form["quantity"])
        unit = request.form["unit"]

        if item not in fridge or fridge[item]["quantity"] <= 0:
            flash("Insufficient stock or item not found!", "error")
        elif unit != fridge[item]["unit"]:
            flash("Unit mismatch! Please check the unit.", "error")
        elif fridge[item]["quantity"] < quantity:
            flash(f"Not enough quantity to consume. Current stock: {fridge[item]['quantity']} {unit}", "error")
        else:
            fridge[item]["quantity"] -= quantity
            history.append({"item": item, "quantity": f"{quantity} {unit}", "action": "Consume", "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            save_data(fridge, history)
            flash(f"{quantity} {unit} of {item} consumed successfully!", "success")

        return redirect(url_for("index"))

    return render_template("consume.html", items=fridge)

@app.route('/shopping_list')
def shopping_list():
    expired_items = check_and_deduct_expired_items()  # Check and deduct expired items before showing shopping list
    low_stock_items = {}
    expiring_items = {}

    for item, details in fridge.items():
        # Check for low stock
        if details['unit'] in ['liter', 'kg', 'pieces'] and float(details['quantity']) < 2:
            low_stock_items[item] = details
        
        # Check for expiry
        expiry_date = datetime.strptime(details['expiry_date'], '%Y-%m-%d').date()
        if expiry_date <= date.today() + timedelta(days=3):  # Expiring within 3 days
            expiring_items[item] = details

    return render_template('shopping_list.html', 
                           low_stock_items=low_stock_items, 
                           expiring_items=expiring_items, 
                           expired_items=expired_items)


@app.route('/history')
def history_page():
    global history
    return render_template("history.html", history=history)

if __name__ == '__main__':
    app.run(debug=True)
