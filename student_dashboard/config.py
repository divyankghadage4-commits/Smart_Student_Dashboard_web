import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _secret_key = os.environ.get('SECRET_KEY')
    if not _secret_key:
        if os.environ.get('FLASK_ENV', '').lower() == 'production' or os.environ.get('RENDER'):
            raise RuntimeError('SECRET_KEY environment variable must be set in production.')
        _secret_key = 'local-development-only-change-before-deployment'
    SECRET_KEY = _secret_key

    # Database Configuration
    # By default this app runs on the bundled SQLite database
    # (data/student_dashboard.db), which already matches the SQLAlchemy
    # models in models.py and comes pre-loaded with sample data.
    #
    # To use MySQL instead, set the DATABASE_URL environment variable, e.g.:
    #   export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/student_dashboard"
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'data', 'student_dashboard.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f"sqlite:///{SQLITE_DB_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload limit configurations (16 MB)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
