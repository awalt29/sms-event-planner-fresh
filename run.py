from app import create_app
from app.models import db
import os

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Get port from environment variable or default to 5002
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
