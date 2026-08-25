from flask import Flask, render_template, request, redirect, url_for, flash , session , Blueprint ,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re
from datetime import datetime
import PyPDF2
import pytesseract
from PIL import Image
import traceback
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import matplotlib.pyplot as plt
import io
import base64
from flask import render_template
import sqlite3
from collections import defaultdict
from datetime import datetime,date
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# From extract_transactions_from_pdf
pattern = r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s+(.*?)\s+(-?\d+[\d,]*\.\d{2})'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

graph_bp = Blueprint('graph', __name__)

# Add allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Transaction(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.String(50), nullable=False)

    description = db.Column(db.String(255), nullable=False)

    amount = db.Column(db.Float, nullable=False)

    category = db.Column(db.String(50), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
# Initialize database
with app.app_context():
    db.create_all()


def extract_transactions_from_pdf(pdf_path):
    transactions = []
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page in reader.pages:
                text = page.extract_text()
                print(f"Raw PDF Text:\n{text}\n{'-'*50}")

                # First check if it's a receipt-style document
                receipt_transactions = process_receipt_text(text)
                if receipt_transactions:
                    transactions.extend(receipt_transactions)
                    continue  # Skip regular processing if receipt found

                # Regular bank statement processing
                statement_pattern = r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s+(.*?)\s+(-?\d+[\d,]*\.\d{2})'
                matches = re.findall(statement_pattern, text)
                print(f"Found {len(matches)} bank transactions")

                for date, desc, amount in matches:
                    try:
                        # Handle different date formats
                        date_formats = ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                        parsed_date = None
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(date, fmt)
                                break
                            except ValueError:
                                continue

                        if not parsed_date:
                            continue

                        amount = float(amount.replace(',', ''))
                        
                        transactions.append({
                            'date': parsed_date.strftime('%Y-%m-%d'),
                            'description': desc.strip(),
                            'amount': abs(amount)
                        })
                    except Exception as e:
                        print(f"Error processing transaction: {str(e)}")
                        continue

    except Exception as e:
        print(f"PDF processing error: {str(e)}")
    
    return transactions

def process_receipt_text(text):
    transactions = []
    
    # Try to find receipt header
    if "RECEIPT" not in text and "TOTAL AMOUNT" not in text:
        return []
    
    print("Processing receipt-style document")
    
    try:
        # Extract date
        date_match = re.search(r'\d{2}-\d{2}-\d{4}', text)
        trans_date = datetime.now().strftime('%Y-%m-%d')
        if date_match:
            try:
                trans_date = datetime.strptime(date_match.group(), '%d-%m-%Y').strftime('%Y-%m-%d')
            except:
                pass

        # Extract total amount
        total_match = re.search(r'TOTAL\s+AMOUNT\s+\D*(\d+\.\d{2})', text, re.IGNORECASE)
        if total_match:
            transactions.append({
                'date': trans_date,
                'description': 'Retail Purchase',
                'amount': float(total_match.group(1))
            })
            print(f"Found receipt total: {transactions[-1]}")

        # Alternative: Extract individual items
        item_matches = re.findall(r'(\d+ x .+?)\s+(\$\d+\.\d{2})', text)
        for item, price in item_matches:
            transactions.append({
                'date': trans_date,
                'description': item.strip(),
                'amount': float(price.replace('$', ''))
            })

    except Exception as e:
        print(f"Receipt processing error: {str(e)}")
    
    return transactions

def categorize_transaction(description):
    desc = description.lower()
    categories = {
        'Food': ['swiggy', 'zomato', 'grocery', 'restaurant', 'food'],
        'Travel': ['ola', 'uber', 'fuel', 'metro', 'flight'],
        'Education': ['coursera', 'udemy', 'school', 'book', 'tuition']
    }
    for category, keywords in categories.items():
        if any(keyword in desc for keyword in keywords):
            return category
    return 'Miscellaneous'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return extract_transactions_from_receipt(text)
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return []
        # Extract transaction details
        transaction = {
            'date': re.search(r'\d{2}/\d{2}/\d{4}', text).group(0),
            'description': re.search(r'[A-Za-z\s]+', text).group(0).strip(),
            'amount': float(re.search(r'\d+\.\d{2}', text).group(0))
        }
        return transaction
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return None



def extract_transactions_from_receipt(text):
    total_amount = None
    # Regex pattern to find total amount
    total_pattern = r'TOTAL\s+AMOUNT\s+\D*(\d+\.\d{2})'
    match = re.search(total_pattern, text, re.IGNORECASE)
    
    if match:
        total_amount = float(match.group(1))
        return [{
            'date': datetime.now().strftime('%Y-%m-%d'),  # Use current date or extract from receipt
            'description': 'Shopping Purchase',
            'amount': total_amount
        }]
    return []

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('signup'))
            
        new_user = User(
            email=email,
            password=generate_password_hash(password)  # Removed method parameter
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main application routes
@app.route('/')
@login_required
def dashboard():
    categories = ['Food', 'Travel', 'Education', 'Miscellaneous']
    totals = {}
    for category in categories:
        totals[category] = db.session.query(db.func.sum(Transaction.amount)).\
            filter(Transaction.user_id == current_user.id, 
                   Transaction.category == category).scalar() or 0.0
    
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    return render_template('dashboard.html', totals=totals, transactions=transactions)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            
            # Validate file presence and extension
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if not file.filename.lower().endswith('.pdf'):
                flash('Only PDF files are allowed', 'error')
                return redirect(request.url)
            
            # Secure filename and save
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            print(f"\n📁 File saved to: {save_path}")

            # Extract transactions
            transactions = extract_transactions_from_pdf(save_path)
            print(f"\n🔍 Found {len(transactions)} raw transactions")
            
            if not transactions:
                flash('No transactions found in PDF', 'warning')
                return redirect(request.url)
            
            # Process and save transactions
            new_transactions = []
            for idx, transaction in enumerate(transactions):
                try:
                    category = categorize_transaction(transaction['description'])
                    print(f"\n⚙️ Processing transaction {idx + 1}:")
                    print(f"   Date: {transaction['date']}")
                    print(f"   Desc: {transaction['description']}")
                    print(f"   Amt:  {transaction['amount']}")
                    print(f"   Cat:  {category}")

                    new_trans = Transaction(
                        user_id=current_user.id,
                        date=transaction['date'],
                        description=transaction['description'],
                        amount=transaction['amount'],
                        category=category
                    )
                    db.session.add(new_trans)
                    new_transactions.append(new_trans)
                
                except Exception as e:
                    print(f"\n❌ Error processing transaction {idx}: {str(e)}")
                    continue

            # Commit to database
            db.session.commit()
            print(f"\n💾 Successfully saved {len(new_transactions)} transactions")
            flash(f'Successfully processed {len(new_transactions)} transactions!', 'success')
            
            # Cleanup uploaded file (optional)
            # os.remove(save_path)
            
            return redirect(url_for('dashboard'))

        except PyPDF2.errors.PdfReadError:
            flash('Invalid PDF file - could not read contents', 'error')
            return redirect(request.url)
        
        except Exception as e:
            db.session.rollback()
            print(f"\n🔥 Critical error: {traceback.format_exc()}")
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('upload.html')


@app.route('/upload_image', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image file provided', 'error')
            return redirect(request.url)

        image = request.files['image']
        if image.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            # OCR using Tesseract
            text = pytesseract.image_to_string(Image.open(image_path))

            # Extract total amount (e.g., TOTAL AMOUNT $363.99 or TOTAL AMOUNT    $363.99)
            match = re.search(r'TOTAL AMOUNT\s*\$?([\d,]+\.\d{2})', text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    session['pending_transaction'] = {
                        'filename': filename,
                        'date': datetime.now().strftime('%d/%m/%Y'),
                        'description': 'Receipt OCR Total',
                        'amount': amount
                    }
                    return redirect(url_for('categorize'))
                except ValueError:
                    flash('Failed to parse amount from receipt.', 'error')
                    return redirect(request.url)
            else:
                flash('No total amount found in receipt.', 'error')
                return redirect(request.url)

    return render_template('upload_image.html')


@app.route('/categorize', methods=['GET', 'POST'])
@login_required
def categorize():
    if 'pending_transaction' not in session:
        return redirect(url_for('upload_image'))
    
    transaction = session['pending_transaction']
    
    if request.method == 'POST':
        try:
            # Update with user input
            transaction['category'] = request.form['category']
            transaction['amount'] = float(request.form['amount'])
            transaction['date'] = request.form['date']
            transaction['description'] = request.form['description']
            
            # Save to database
            new_trans = Transaction(
                user_id=current_user.id,
                date=transaction['date'],
                description=transaction['description'],
                amount=transaction['amount'],
                category=transaction['category']
            )
            db.session.add(new_trans)
            db.session.commit()
            
            session.pop('pending_transaction', None)
            flash('Transaction saved!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            print(f"Error saving transaction: {str(e)}")
            flash('Error saving transaction', 'error')
    
    return render_template('categorize.html', transaction=transaction)

@app.route('/categorize_multiple', methods=['GET', 'POST'])
@login_required
def categorize_multiple():
    if 'pending_transactions' not in session or not session['pending_transactions']:
        return redirect(url_for('upload_image'))

    # Get the first transaction from the list
    transaction = session['pending_transactions'][0]

    if request.method == 'POST':
        try:
            transaction['category'] = request.form['category']
            transaction['amount'] = float(request.form['amount'])
            transaction['date'] = request.form['date']
            transaction['description'] = request.form['description']

            # Save to DB
            new_trans = Transaction(
                user_id=current_user.id,
                date=transaction['date'],
                description=transaction['description'],
                amount=transaction['amount'],
                category=transaction['category']
            )
            db.session.add(new_trans)
            db.session.commit()

            # Remove the processed one
            session['pending_transactions'].pop(0)

            if not session['pending_transactions']:
                session.pop('pending_transactions', None)
                flash('All transactions saved!', 'success')
                return redirect(url_for('dashboard'))

            return redirect(url_for('categorize_multiple'))

        except Exception as e:
            db.session.rollback()
            flash('Error saving transaction', 'error')

    return render_template('categorize.html', transaction=transaction)


# app.py
# Add this route

@app.route("/add-transaction", methods=["POST"])
@login_required
def add_transaction():

    date = request.form.get("date")
    description = request.form.get("description")
    amount = request.form.get("amount")
    category = request.form.get("category")

    if not date or not description or not amount or not category:
        flash("Please fill all fields.", "danger")
        return redirect(url_for("dashboard"))

    try:
        amount = float(amount)
    except ValueError:
        flash("Please enter a valid amount.", "danger")
        return redirect(url_for("dashboard"))

    new_transaction = Transaction(
        date=date,
        description=description,
        amount=amount,
        category=category,
        user_id=current_user.id
    )

    db.session.add(new_transaction)
    db.session.commit()

    flash("Transaction added successfully!", "success")

    return redirect(url_for("dashboard"))


def get_transaction_date(transaction_date):
    """
    Converts transaction date into Python date object.
    Handles both Date column and string date.
    """

    if isinstance(transaction_date, datetime):
        return transaction_date.date()

    if isinstance(transaction_date, date):
        return transaction_date

    # If stored as string
    try:
        return datetime.strptime(
            str(transaction_date),
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return None
@app.route('/budget-analysis')
@login_required
def budget_analysis():

    categories = [
        'Food',
        'Travel',
        'Education',
        'Miscellaneous'
    ]

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).all()

    today = date.today()

    current_year = today.year
    current_month = today.month

    # Calculate previous month
    if current_month == 1:
        last_month = 12
        last_month_year = current_year - 1
    else:
        last_month = current_month - 1
        last_month_year = current_year

    # Store expenses
    last_month_expenses = defaultdict(float)
    previous_month_expenses = defaultdict(float)

    last_month_total = 0
    previous_month_total = 0

    # Month before last month
    if last_month == 1:
        previous_month = 12
        previous_month_year = last_month_year - 1
    else:
        previous_month = last_month - 1
        previous_month_year = last_month_year


    for transaction in transactions:

        transaction_date = get_transaction_date(
            transaction.date
        )

        if not transaction_date:
            continue

        category = transaction.category
        amount = float(transaction.amount)


        # Last month expenses
        if (
            transaction_date.month == last_month
            and transaction_date.year == last_month_year
        ):

            last_month_expenses[category] += amount
            last_month_total += amount


        # Previous month expenses
        if (
            transaction_date.month == previous_month
            and transaction_date.year == previous_month_year
        ):

            previous_month_expenses[category] += amount
            previous_month_total += amount


    # ==========================================
    # BUILD SMART ANALYSIS
    # ==========================================

    analysis = []

    predicted_total = 0
    recommended_total = 0
    potential_savings = 0


    for category in categories:

        last_expense = last_month_expenses.get(
            category,
            0
        )

        previous_expense = previous_month_expenses.get(
            category,
            0
        )


        # ------------------------------------------
        # Calculate spending trend
        # ------------------------------------------

        if previous_expense > 0:

            percentage_change = (
                (
                    last_expense - previous_expense
                )
                / previous_expense
            ) * 100

        else:
            percentage_change = 0


        # ------------------------------------------
        # Predict next month's expense
        # ------------------------------------------

        if previous_expense > 0:

            predicted_expense = (
                last_expense * 0.7
                +
                previous_expense * 0.3
            )

        else:
            predicted_expense = last_expense


        # ------------------------------------------
        # CATEGORY SPECIFIC BUDGET REDUCTION
        # ------------------------------------------

        if category == "Food":

            reduction_percent = 0.15

        elif category == "Travel":

            reduction_percent = 0.10

        elif category == "Miscellaneous":

            reduction_percent = 0.20

        else:

            reduction_percent = 0.05


        recommended_budget = (
            predicted_expense
            * (1 - reduction_percent)
        )


        savings = (
            predicted_expense
            - recommended_budget
        )


        predicted_total += predicted_expense

        recommended_total += recommended_budget

        potential_savings += savings


        # ------------------------------------------
        # SPENDING STATUS
        # ------------------------------------------

        if percentage_change > 15:

            status = "High Increase"

        elif percentage_change > 0:

            status = "Increased"

        elif percentage_change < -10:

            status = "Reduced"

        else:

            status = "Stable"


        analysis.append({

            "category": category,

            "last_expense": round(
                last_expense,
                2
            ),

            "previous_expense": round(
                previous_expense,
                2
            ),

            "predicted_expense": round(
                predicted_expense,
                2
            ),

            "recommended_budget": round(
                recommended_budget,
                2
            ),

            "potential_savings": round(
                savings,
                2
            ),

            "percentage_change": round(
                percentage_change,
                1
            ),

            "status": status

        })


    # ==========================================
    # FIND HIGHEST EXPENSE CATEGORY
    # ==========================================

    highest_category = None

    if last_month_total > 0:

        highest_category = max(
            analysis,
            key=lambda x: x["last_expense"]
        )


    # ==========================================
    # GENERATE INSIGHTS
    # ==========================================

    insights = []


    if highest_category and highest_category["last_expense"] > 0:

        insights.append(
            f"You spent the most on "
            f"{highest_category['category']} "
            f"last month: ₹{highest_category['last_expense']:.2f}"
        )


    for item in analysis:

        if item["percentage_change"] > 15:

            insights.append(
                f"{item['category']} expenses increased by "
                f"{item['percentage_change']}% compared to the previous month."
            )


    if potential_savings > 0:

        insights.append(
            f"Following the recommended budget could save approximately "
            f"₹{potential_savings:.2f} next month."
        )


    # ------------------------------------------
    # CATEGORY WISE COST CUTTING SUGGESTIONS
    # ------------------------------------------

    suggestions = []

    for item in analysis:

        if item["last_expense"] <= 0:
            continue


        if item["category"] == "Food":

            suggestions.append({
                "category": "Food",
                "icon": "🍔",
                "title": "Reduce food spending",
                "message": (
                    "Try reducing restaurant and food delivery orders. "
                    "Plan weekly groceries and home-cooked meals."
                ),
                "saving": item["potential_savings"]
            })


        elif item["category"] == "Travel":

            suggestions.append({
                "category": "Travel",
                "icon": "✈️",
                "title": "Optimize travel costs",
                "message": (
                    "Consider public transport, ride sharing, "
                    "or planning trips in advance."
                ),
                "saving": item["potential_savings"]
            })


        elif item["category"] == "Education":

            suggestions.append({
                "category": "Education",
                "icon": "🎓",
                "title": "Review education expenses",
                "message": (
                    "Check for unnecessary subscriptions, duplicate courses, "
                    "or available student discounts."
                ),
                "saving": item["potential_savings"]
            })


        elif item["category"] == "Miscellaneous":

            suggestions.append({
                "category": "Miscellaneous",
                "icon": "🛍️",
                "title": "Control miscellaneous spending",
                "message": (
                    "This category often contains impulse purchases. "
                    "Set a fixed weekly spending limit."
                ),
                "saving": item["potential_savings"]
            })


    return render_template(

        'budget_analysis.html',

        analysis=analysis,

        insights=insights,

        suggestions=suggestions,

        last_month_total=round(
            last_month_total,
            2
        ),

        previous_month_total=round(
            previous_month_total,
            2
        ),

        predicted_total=round(
            predicted_total,
            2
        ),

        recommended_total=round(
            recommended_total,
            2
        ),

        potential_savings=round(
            potential_savings,
            2
        ),

        highest_category=highest_category,

        last_month=last_month,
        last_month_year=last_month_year

    )



def parse_transaction_date(transaction_date):

    if isinstance(transaction_date, datetime):
        return transaction_date.date()

    if isinstance(transaction_date, date):
        return transaction_date

    try:
        return datetime.strptime(
            str(transaction_date),
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return None

@app.route('/finance-chat', methods=['POST'])
@login_required
def finance_chat():

    data = request.get_json()

    if not data or not data.get('message'):
        return jsonify({
            "reply": "Please ask me something about your expenses or budget."
        }), 400

    message = data.get('message', '').lower().strip()

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).all()

    if not transactions:
        return jsonify({
            "reply": (
                "You don't have any transactions yet. "
                "Please upload a statement or add transactions manually, "
                "then I can analyze your spending."
            )
        })

    categories = [
        "Food",
        "Travel",
        "Education",
        "Miscellaneous"
    ]

    # =====================================
    # ANALYZE ALL TRANSACTIONS
    # =====================================

    category_totals = defaultdict(float)

    monthly_totals = defaultdict(float)

    total_expense = 0

    today = date.today()

    current_month_total = 0
    last_month_total = 0

    if today.month == 1:
        last_month = 12
        last_month_year = today.year - 1
    else:
        last_month = today.month - 1
        last_month_year = today.year

    for transaction in transactions:

        transaction_date = parse_transaction_date(
            transaction.date
        )

        amount = float(transaction.amount)

        category = transaction.category

        total_expense += amount

        category_totals[category] += amount

        if transaction_date:

            month_key = (
                transaction_date.year,
                transaction_date.month
            )

            monthly_totals[month_key] += amount

            # Current month
            if (
                transaction_date.month == today.month
                and transaction_date.year == today.year
            ):
                current_month_total += amount

            # Last month
            if (
                transaction_date.month == last_month
                and transaction_date.year == last_month_year
            ):
                last_month_total += amount


    # =====================================
    # BASIC STATISTICS
    # =====================================

    highest_category = max(
        category_totals,
        key=category_totals.get
    )

    highest_amount = category_totals[highest_category]

    average_transaction = (
        total_expense / len(transactions)
    )

    total_transactions = len(transactions)


    # =====================================
    # CATEGORY DETECTION
    # =====================================

    detected_category = None

    for category in categories:

        if category.lower() in message:
            detected_category = category
            break


    # =====================================
    # RESPONSE GENERATION
    # =====================================

    reply = ""


    # -------------------------------------
    # GREETING
    # -------------------------------------

    if any(word in message for word in [
        "hello",
        "hi",
        "hey",
        "hii"
    ]):

        reply = (
            f"Hey! 👋 I'm your Finance AI Assistant.\n\n"
            f"I've analyzed {total_transactions} transactions. "
            f"Your total recorded spending is ₹{total_expense:,.2f}.\n\n"
            f"Ask me about your spending, categories, savings, "
            f"or next month's budget!"
        )


    # -------------------------------------
    # TOTAL SPENDING
    # -------------------------------------

    elif any(word in message for word in [
        "total expense",
        "total spend",
        "how much spent",
        "kitna kharcha",
        "kitna spend"
    ]):

        reply = (
            f"Your total recorded spending is "
            f"₹{total_expense:,.2f} across "
            f"{total_transactions} transactions."
        )


    # -------------------------------------
    # CURRENT MONTH
    # -------------------------------------

    elif any(word in message for word in [
        "this month",
        "current month",
        "is month",
        "iss month"
    ]):

        reply = (
            f"This month, you have spent "
            f"₹{current_month_total:,.2f} so far."
        )


    # -------------------------------------
    # LAST MONTH
    # -------------------------------------

    elif any(word in message for word in [
        "last month",
        "previous month",
        "pichle month",
        "last motnh"
    ]):

        reply = (
            f"Last month, your total spending was "
            f"₹{last_month_total:,.2f}."
        )


    # -------------------------------------
    # CATEGORY SPECIFIC QUESTIONS
    # -------------------------------------

    elif detected_category:

        amount = category_totals.get(
            detected_category,
            0
        )

        percentage = 0

        if total_expense > 0:
            percentage = (
                amount / total_expense
            ) * 100


        reply = (
            f"You have spent ₹{amount:,.2f} on "
            f"{detected_category}. "
            f"That's approximately {percentage:.1f}% "
            f"of your total expenses."
        )


        # Add cost-cutting suggestions

        if any(word in message for word in [
            "reduce",
            "save",
            "cut",
            "kam",
            "reduce expense"
        ]):

            if detected_category == "Food":

                reply += (
                    "\n\n💡 Suggestion: Try setting a weekly food "
                    "budget, reduce food delivery, and plan groceries. "
                    f"You could aim to save around ₹{amount * 0.15:,.2f}."
                )

            elif detected_category == "Travel":

                reply += (
                    "\n\n💡 Suggestion: Use public transport, "
                    "carpooling, or plan trips in advance. "
                    f"You could potentially save around ₹{amount * 0.10:,.2f}."
                )

            elif detected_category == "Education":

                reply += (
                    "\n\n💡 Suggestion: Review subscriptions and "
                    "check for student discounts or free alternatives."
                )

            elif detected_category == "Miscellaneous":

                reply += (
                    "\n\n💡 Suggestion: This category can contain "
                    "impulse purchases. Set a strict monthly limit. "
                    f"You could potentially save around ₹{amount * 0.20:,.2f}."
                )


    # -------------------------------------
    # HIGHEST EXPENSE
    # -------------------------------------

    elif any(word in message for word in [
        "highest",
        "most",
        "maximum",
        "sabse zyada",
        "highest expense",
        "most expense"
    ]):

        percentage = (
            highest_amount / total_expense
        ) * 100

        reply = (
            f"Your highest spending category is "
            f"📊 {highest_category}.\n\n"
            f"You spent ₹{highest_amount:,.2f}, "
            f"which is {percentage:.1f}% of your "
            f"total recorded expenses."
        )


    # -------------------------------------
    # BUDGET PLANNING
    # -------------------------------------

    elif any(word in message for word in [
        "budget",
        "next month",
        "budget planning",
        "plan"
    ]):

        predicted_budget = total_expense

        # If last month exists, use that
        if last_month_total > 0:
            predicted_budget = last_month_total

        recommended_budget = predicted_budget * 0.88

        reply = (
            f"📅 Based on your spending pattern, "
            f"I recommend a next-month budget of "
            f"approximately ₹{recommended_budget:,.2f}.\n\n"
            f"Your estimated potential saving is "
            f"₹{predicted_budget - recommended_budget:,.2f}.\n\n"
            f"Suggested category budgets:\n"
        )

        for category in categories:

            amount = category_totals.get(
                category,
                0
            )

            if amount > 0:

                category_budget = amount * 0.88

                reply += (
                    f"\n• {category}: "
                    f"₹{category_budget:,.2f}"
                )


    # -------------------------------------
    # SAVINGS
    # -------------------------------------

    elif any(word in message for word in [
        "save",
        "saving",
        "savings",
        "bachat"
    ]):

        potential_saving = 0

        for category, amount in category_totals.items():

            if category == "Food":
                potential_saving += amount * 0.15

            elif category == "Travel":
                potential_saving += amount * 0.10

            elif category == "Miscellaneous":
                potential_saving += amount * 0.20

            else:
                potential_saving += amount * 0.05


        reply = (
            f"💰 Based on your current expenses, "
            f"you could potentially save around "
            f"₹{potential_saving:,.2f} by following "
            f"recommended category limits."
        )


    # -------------------------------------
    # AVERAGE TRANSACTION
    # -------------------------------------

    elif any(word in message for word in [
        "average",
        "avg"
    ]):

        reply = (
            f"Your average transaction amount is "
            f"₹{average_transaction:,.2f}."
        )


    # -------------------------------------
    # HELP
    # -------------------------------------

    else:

        reply = (
            "I can analyze your transactions and help you with:\n\n"
            "• 💰 Total spending\n"
            "• 📅 This month's expenses\n"
            "• 📊 Last month's expenses\n"
            "• 🍔 Food, Travel, Education expenses\n"
            "• 🔥 Highest spending category\n"
            "• ✂️ Cost-cutting suggestions\n"
            "• 🎯 Next month's budget\n"
            "• 💵 Savings opportunities\n\n"
            "Try asking: "
            "\"How can I reduce my Food expenses?\""
        )


    return jsonify({
        "reply": reply
    })

@app.route('/graph')
@login_required
def show_graph():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    from collections import defaultdict
    category_totals = defaultdict(float)
    total_expense = 0.0

    for txn in transactions:
        category_totals[txn.category] += txn.amount
        total_expense += txn.amount

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    return render_template(
        'graph.html',
        categories=categories,
        amounts=amounts,
        total_expense=round(total_expense, 2)
    )
