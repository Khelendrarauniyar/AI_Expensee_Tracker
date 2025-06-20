# AI Expense Tracker

AI Expense Tracker is a web application built with Flask that helps users manage their personal finances. It allows you to track expenses, categorize them, view analytics, and get AI-powered suggestions for better financial management.

## Features

- User authentication (Sign Up, Login, Password Reset)
- Add, edit, and delete expense categories
- Add, edit, and delete expenses
- View all expenses and category-wise breakdown
- Visual analytics (line, bar, and pie charts)
- Motivational quotes and actionable finance suggestions powered by Gemini AI
- Profile management with profile picture upload
- Integrated AI chatbot ("Maya") for finance-related queries
- Responsive, modern UI with custom CSS

## Directory Structure

```
.
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── models/
│   ├── static/
│   │   ├── css/
│   │   ├── images/
│   │   ├── uploads/
│   │   └── videos/
│   └── templates/
│       ├── about.html
│       ├── add_category.html
│       ├── add_expense.html
│       ├── base.html
│       ├── edit_category.html
│       ├── edit_expenses.html
│       ├── expense_details.html
│       ├── forgot_password.html
│       ├── help.html
│       ├── index.html
│       ├── login.html
│       ├── profile.html
│       ├── reset_password.html
│       ├── signup.html
│       ├── start.html
│       ├── view_all_expenses.html
│       ├── view_analytics.html
│       └── welcome.html
├── config.py
├── Dockerfile
├── manage.py
├── requirements.txt
├── run.py
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
├── instance/
│   └── expenses.db
├── .env
└── project data/
    └── (images, videos, presentations, etc.)
```

## Setup Instructions

1. **Clone the repository**

    ```sh
    git clone https://github.com/yourusername/ai-expense-tracker.git
    cd ai-expense-tracker
    ```

2. **Create and activate a virtual environment**

    ```sh
    python -m venv env
    source env/bin/activate  # On Windows: env\Scripts\activate
    ```

3. **Install dependencies**

    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables**

    - Copy `.env.example` to `.env` and set your `SECRET_KEY` and any other configs as needed.

5. **Initialize the database**

    ```sh
    flask db upgrade
    ```

6. **Run the application**

    ```sh
    python run.py
    ```

    The app will be available at [http://localhost:2003](http://localhost:2003).

7. **(Optional) Run with Docker**

    ```sh
    docker build -t ai-expense-tracker .
    docker run -p 2003:2003 ai-expense-tracker
    ```


## Technologies Used

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Jinja2
- SQLite (default, can be changed)
- Google Gemini AI (for chatbot and suggestions)
- Docker (optional)

## License

MIT License

---

*For any questions or support, please contact [support@expensetracker.com](mailto:support@expensetracker.com).*
