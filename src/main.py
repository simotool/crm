import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models import db
from src.routes.user import user_bp
from src.routes.product import product_bp
from src.routes.order import order_bp
from src.routes.webhook import webhook_bp
from src.routes.google_sheets import google_sheets_bp
from src.routes.delivery_company import delivery_company_bp
from src.routes.delivery_price_list import delivery_price_list_bp
from src.routes.staff import staff_bp
from src.routes.inventory import inventory_bp
from src.routes.delivery_integration import delivery_integration_bp
from src.routes.expense import expense_bp
from src.routes.financial_reports import financial_reports_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Enable CORS for all routes
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(order_bp, url_prefix='/api')
app.register_blueprint(webhook_bp, url_prefix='/api')
app.register_blueprint(google_sheets_bp, url_prefix='/api')
app.register_blueprint(delivery_company_bp, url_prefix='/api')
app.register_blueprint(delivery_price_list_bp, url_prefix='/api')
app.register_blueprint(staff_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api')
app.register_blueprint(delivery_integration_bp, url_prefix='/api')
app.register_blueprint(expense_bp, url_prefix='/api')
app.register_blueprint(financial_reports_bp, url_prefix='/api')

# Database configuration
database_url = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'app.db')}")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
