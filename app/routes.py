from flask import Blueprint, render_template, request, redirect, session, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Category, Expense
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def welcome():
    return render_template('welcome.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        contact_number = request.form['contact_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('main.signup'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('main.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('main.signup'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, contact_number=contact_number, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main.index'))
    return render_template('signup.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.welcome'))

"""@main.route('/index')
@login_required
def index():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Calculate total expected and expended amounts
    total_expected_amount = sum(category.estimated_expense for category in categories)
    total_expended_amount = sum(sum(expense.amount for expense in category.expenses) for category in categories)
    
    # Calculate expended amount for each category
    for category in categories:
        category.expended_amount = sum(expense.amount for expense in category.expenses)
    
    return render_template('index.html', categories=categories, total_expected_amount=total_expected_amount, total_expended_amount=total_expended_amount)"""

@main.route('/index')
@login_required
def index():
    # Fetch categories and totals
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Calculate total expected and expended amounts
    total_expected_amount = sum(category.estimated_expense for category in categories)
    total_expended_amount = sum(sum(expense.amount for expense in category.expenses) for category in categories)
    
    # Calculate expended amount for each category
    # Calculate expended amount for each category
    for category in categories:
        category.expended_amount = sum(expense.amount for expense in category.expenses)
    # Generate a quote using Gemini AI
    quote = generate_quote()

    # Generate suggestions using Gemini AI
    suggestions = generate_suggestions(current_user.id)

    # Check for new suggestions
    has_new_suggestions = check_for_new_suggestions(current_user.id)

    return render_template(
        'index.html',
        categories=categories,
        total_expected_amount=total_expected_amount,
        total_expended_amount=total_expended_amount,
        quote=quote,
        suggestions=suggestions,
        has_new_suggestions=has_new_suggestions
    )

@main.route('/expenses/<int:category_id>')
@login_required
def get_expenses(category_id):
    expenses = Expense.query.filter_by(category_id=category_id, user_id=current_user.id).order_by(Expense.date.desc()).all()
    expenses_data = [{'title': expense.title, 'amount': expense.amount, 'date': expense.date.strftime('%Y-%m-%d %H:%M:%S'), 'notes': expense.notes} for expense in expenses]
    return jsonify({'expenses': expenses_data})

@main.route('/add_category', methods=['GET', 'POST'])
@login_required
def add_category():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    alerts = []

    if request.method == 'POST':
        name = request.form['name']
        estimated_expense = float(request.form['estimated_expense'])
        
        # Check if category already exists
        existing_category = Category.query.filter_by(name=name, user_id=current_user.id).first()
        if existing_category:
            flash('Category with this name already exists!', 'danger')
            return redirect(url_for('main.add_category'))

        # Add new category
        category = Category(name=name, estimated_expense=estimated_expense, user_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('main.add_category'))

    # Calculate expended amount for each category
    for category in categories:
        category.expended_amount = sum(expense.amount for expense in category.expenses)
        if category.expended_amount > category.estimated_expense:
            alerts.append(f"⚠️ Category '{category.name}' exceeded the budget!")

    return render_template('add_category.html', categories=categories, alerts=alerts)

@main.route('/delete_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()

    if not category:
        flash('Category not found or unauthorized!', 'danger')
        return redirect(url_for('main.add_category'))

    # Delete all expenses related to this category
    Expense.query.filter_by(category_id=category.id).delete()

    # Delete the category itself
    db.session.delete(category)
    db.session.commit()

    flash('Category and related expenses deleted successfully!', 'success')
    return redirect(url_for('main.add_category'))

    

@main.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        date_str = request.form['date']  # Get the date input in "YYYY-MM-DDTHH:MM" format
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")  # Parse directly
        notes = request.form['notes']
        category_id = int(request.form['category_id'])
        expense = Expense(title=title, amount=amount, date=date, notes=notes, category_id=category_id, user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.index'))
    return render_template('add_expense.html', categories=categories)

@main.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        contact_number = request.form['contact_number']
        user = User.query.filter_by(email=email, contact_number=contact_number).first()
        if user:
            return redirect(url_for('main.reset_password', user_id=user.id))
        else:
            flash('Email or contact number not found', 'danger')
    return render_template('forgot_password.html')

@main.route('/reset-password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('Invalid user', 'danger')
        return redirect(url_for('main.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('main.reset_password', user_id=user_id))
        
        hashed_password = generate_password_hash(new_password)
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('reset_password.html', user_id=user_id)

@main.route('/category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def expense_details(category_id):
    category = Category.query.get_or_404(category_id)
    if category.user_id != current_user.id:
        flash('You do not have access to this category', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form['title']
        amount = float(request.form['amount'])
        date_str = request.form['date']  # Get the date input in "YYYY-MM-DDTHH:MM" format
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")  # Parse directly
        notes = request.form['notes']
        expense = Expense(title=title, amount=amount, date=date, notes=notes, category_id=category_id, user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.expense_details', category_id=category_id))
    
    expenses = Expense.query.filter_by(category_id=category_id).order_by(Expense.date.desc()).all()
    category.expended_amount = sum(expense.amount for expense in expenses)
    return render_template('expense_details.html', category=category, expenses=expenses)


@main.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.user_id != current_user.id:
        flash('You do not have access to edit this category', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        category.name = request.form['name']
        category.estimated_expense = float(request.form['estimated_expense'])
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('edit_category.html', category=category)

from datetime import datetime

@main.route('/edit_expenses/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_expenses(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    
    if not category:
        flash('Category not found!', 'danger')
        return redirect(url_for('main.add_category'))
    
    expenses = Expense.query.filter_by(category_id=category.id).all()

    if request.method == 'POST':
        for expense in expenses:
            expense.title = request.form.get(f"title-{expense.id}")
            expense.amount = float(request.form.get(f"amount-{expense.id}"))
            expense.notes = request.form.get(f"notes-{expense.id}")
            
            # Combine date and time into a single datetime object
            date_str = request.form.get(f"date-{expense.id}")
            time_str = request.form.get(f"time-{expense.id}")
            if date_str and time_str:
                datetime_str = f"{date_str}T{time_str}"
                expense.date = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")
            
        db.session.commit()
        flash("Expenses updated successfully!", "success")
        return redirect(url_for('main.edit_expenses', category_id=category_id))

    return render_template('edit_expenses.html', category=category, expenses=expenses)

@main.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    
    if not expense:
        return jsonify({"success": False, "message": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()

    return jsonify({"success": True, "message": "Expense deleted successfully!"})


@main.route('/view_all_expenses')
@login_required
def view_all_expenses():
    # Fetch all categories and their expenses for the current user
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Calculate total expected and expended amounts
    total_expected = sum(category.estimated_expense for category in categories)
    total_expended = sum(sum(expense.amount for expense in category.expenses) for category in categories)
    
    # Calculate expended amount for each category
    category_expended = {category.id: sum(expense.amount for expense in category.expenses) for category in categories}
    
    return render_template('view_all_expenses.html', categories=categories, total_expected=total_expected, total_expended=total_expended, category_expended=category_expended)

"""Profile routes"""
from flask import request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64

# Set Matplotlib backend to Agg
plt.switch_backend('Agg')

# Define the upload folder for profile pictures
UPLOAD_FOLDER = 'app/static/uploads/profile_pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Validate current password
        current_password = request.form.get('current_password')
        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('main.profile'))

        # Update user details
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.contact_number = request.form.get('contact_number')

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                current_user.profile_picture = os.path.join('uploads', 'profile_pictures', filename)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))

    # Generate expense analytics graph
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        db.func.strftime('%Y-%m', Expense.date) == datetime.now().strftime('%Y-%m')
    ).all()

    # Prepare data for the graph
    dates = [expense.date.strftime('%Y-%m-%d') for expense in expenses]
    amounts = [expense.amount for expense in expenses]

    # Create the graph
    plt.figure(figsize=(10, 5))
    plt.plot(dates, amounts, marker='o', linestyle='-', color='b')
    plt.title('Expense Trends Over Time')
    plt.xlabel('Date')
    plt.ylabel('Amount')
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return render_template('profile.html', graph_url=graph_url)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""View_Analytics"""
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta

@main.route('/view_analytics', methods=['GET', 'POST'])
@login_required
def view_analytics():
    # Default time range: Last 1 month
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    if request.method == 'POST':
        # Get the selected time range
        time_range = request.form.get('time_range')
        if time_range == 'last_month':
            start_date = end_date - timedelta(days=30)
        elif time_range == 'last_3_months':
            start_date = end_date - timedelta(days=90)
        elif time_range == 'custom':
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')

    # Fetch expenses for the selected time range
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()

    # Prepare data for graphs and tables
    dates = [expense.date.strftime('%Y-%m-%d') for expense in expenses]
    amounts = [expense.amount for expense in expenses]
    categories = {}
    for expense in expenses:
        category_name = expense.category.name
        if category_name in categories:
            categories[category_name] += expense.amount
        else:
            categories[category_name] = expense.amount

    # Line Graph: Expense Trends Over Time
    plt.figure(figsize=(10, 5))
    plt.plot(dates, amounts, marker='o', linestyle='-', color='#4facfe')
    plt.title('Expense Trends Over Time', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Amount (₹)', fontsize=12)
    plt.grid(True)
    buf_line = io.BytesIO()
    plt.savefig(buf_line, format='png')
    buf_line.seek(0)
    line_graph_url = base64.b64encode(buf_line.getvalue()).decode('utf-8')
    plt.close()

    # Bar Chart: Expenses by Category
    plt.figure(figsize=(10, 5))
    plt.bar(categories.keys(), categories.values(), color='#00f2fe')
    plt.title('Expenses by Category', fontsize=16)
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Amount (₹)', fontsize=12)
    plt.xticks(rotation=45)
    buf_bar = io.BytesIO()
    plt.savefig(buf_bar, format='png')
    buf_bar.seek(0)
    bar_chart_url = base64.b64encode(buf_bar.getvalue()).decode('utf-8')
    plt.close()

    # Pie Chart: Expenses by Category (Percentage)
    plt.figure(figsize=(8, 8))
    plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%', colors=['#6a11cb', '#2575fc', '#4facfe', '#00f2fe', '#ff9a9e'])
    plt.title('Expenses by Category (Percentage)', fontsize=16)
    buf_pie = io.BytesIO()
    plt.savefig(buf_pie, format='png')
    buf_pie.seek(0)
    pie_chart_url = base64.b64encode(buf_pie.getvalue()).decode('utf-8')
    plt.close()

    # Key Metrics
    total_expenses = sum(amounts)
    average_daily_expenses = total_expenses / len(dates) if dates else 0
    highest_spending_category = max(categories, key=categories.get) if categories else 'N/A'

    return render_template(
        'view_analytics.html',
        line_graph_url=line_graph_url,
        bar_chart_url=bar_chart_url,
        pie_chart_url=pie_chart_url,
        expenses=expenses,
        total_expenses=total_expenses,
        average_daily_expenses=average_daily_expenses,
        highest_spending_category=highest_spending_category,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
"""About And Help pages route"""
@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/help')
def help():
    return render_template('help.html')

"""Chatbot Integration"""
import google.generativeai as genai

# Configure Gemini AI
genai.configure(api_key='AIzaSyCvK_lBNtpi3FGCGbcjbc-OcXviqNMB31w')

@main.route('/maya', methods=['POST'])
@login_required
def maya():
    user_message = request.json.get('message')
    response = generate_maya_response(user_message, current_user)
    return jsonify({'response': response})

def generate_maya_response(message, user):
    # Greet the user
    if "hello" in message.lower() or "hi" in message.lower():
        return f"Hello {user.username}, I am Maya, your AI finance assistant! How can I help you today?"

    # Fetch user's expense data
    expenses = Expense.query.filter_by(user_id=user.id).all()
    total_expenses = sum(expense.amount for expense in expenses)
    categories = {}
    for expense in expenses:
        category_name = expense.category.name
        if category_name in categories:
            categories[category_name] += expense.amount
        else:
            categories[category_name] = expense.amount

    # Prepare context for Gemini AI
    context = f"""
    User: {user.username}
    Total Expenses: ₹{total_expenses}
    Highest Spending Category: {max(categories, key=categories.get) if categories else 'N/A'}
    Expense Categories: {', '.join(categories.keys()) if categories else 'N/A'}
    """

    # Generate response using Gemini AI
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        You are Maya, a friendly and helpful AI finance assistant. 
        The user has the following expense data:
        {context}
        The user asked: {message}
        Provide a helpful and concise response without mentioning that you are an AI or using Gemini.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Sorry, I encountered an issue while processing your request. Please try again later."
    

"""Quotes and Suggestions"""
def generate_quote():
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Generate a short motivational quote about financial management.")
        return response.text
    except Exception as e:
        return "The best time to start managing your finances is now."

def generate_suggestions(user_id):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Provide 3 actionable suggestions for better financial management.")
        suggestions = response.text.replace('**', '')  # Remove ** symbols
        suggestions = suggestions.replace('. ', '.\n')  # Add line breaks after periods
        return suggestions
    except Exception as e:
        return "1. Track your expenses daily.\n2. Set a monthly budget.\n3. Avoid unnecessary purchases."
    except Exception as e:
        return "1. Track your expenses daily. 2. Set a monthly budget. 3. Avoid unnecessary purchases."

def check_for_new_suggestions(user_id):
    # Example logic to check for new suggestions
    # Replace with actual logic (e.g., check database for unseen suggestions)
    return random.choice([True, False])

"""Change Password"""
@main.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    # Validate current password
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('main.profile'))

    # Validate new password
    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('main.profile'))

    # Update password
    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated successfully!', 'success')
    return redirect(url_for('main.profile'))

"""Delete Account"""
@main.route('/delete_profile', methods=['POST'])
@login_required
def delete_profile():
    current_password = request.form.get('current_password')

    # Validate current password
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('main.profile'))

    # Delete all user data
    Expense.query.filter_by(user_id=current_user.id).delete()
    Category.query.filter_by(user_id=current_user.id).delete()
    db.session.delete(current_user)
    db.session.commit()

    flash('Your profile and all associated data have been deleted.', 'success')
    return redirect(url_for('main.welcome'))

@main.route('/chat')
@login_required
def chat():
    user_id = current_user.id
    # Load or create a chat session for the current user
    chat_session = session.get(f'chat_{user_id}', [])
    chat_timestamp = session.get(f'chat_timestamp_{user_id}')

    # Check if the chat session is older than 3 hours
    if chat_timestamp and datetime.now() - chat_timestamp > timedelta(hours=3):
        chat_session = []
        session[f'chat_{user_id}'] = chat_session
        session[f'chat_timestamp_{user_id}'] = datetime.now()

    return render_template('chat.html', chat_session=chat_session)

@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    user_id = current_user.id
    message = request.json.get('message')
    # Load or create a chat session for the current user
    chat_session = session.get(f'chat_{user_id}', [])
    chat_timestamp = session.get(f'chat_timestamp_{user_id}')

    # Check if the chat session is older than 3 hours
    if chat_timestamp and datetime.now() - chat_timestamp > timedelta(hours=3):
        chat_session = []
        session[f'chat_{user_id}'] = chat_session
        session[f'chat_timestamp_{user_id}'] = datetime.now()

    # Add the user's message to the chat session
    chat_session.append({'sender': 'user', 'message': message})
    # Here you would add the logic to get a response from the Gemini API
    response = get_gemini_response(message)
    # Add the Gemini API's response to the chat session
    chat_session.append({'sender': 'gemini', 'message': response})
    # Save the chat session back to the session
    session[f'chat_{user_id}'] = chat_session
    session[f'chat_timestamp_{user_id}'] = datetime.now()
    return jsonify({'status': 'success', 'response': response})

@main.route('/load_chat_history')
@login_required
def load_chat_history():
    user_id = current_user.id
    chat_history = session.get(f'chat_{user_id}', [])
    return jsonify({'chat_history': chat_history})

@main.route('/save_chat_history', methods=['POST'])
@login_required
def save_chat_history():
    user_id = current_user.id
    sender = request.json.get('sender')
    text = request.json.get('text')
    # Load or create a chat session for the current user
    chat_session = session.get(f'chat_{user_id}', [])
    chat_session.append({'sender': sender, 'text': text})
    # Save the chat session back to the session
    session[f'chat_{user_id}'] = chat_session
    session[f'chat_timestamp_{user_id}'] = datetime.now()
    return jsonify({'status': 'success'})

def get_gemini_response(message):
    # Placeholder function to simulate getting a response from the Gemini API
    return "This is a response from the Gemini API."
