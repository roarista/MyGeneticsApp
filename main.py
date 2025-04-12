from app import app, db
from utils.test_routes import test_routes

# Register test routes for debugging
app.register_blueprint(test_routes)

# Create all database tables
with app.app_context():
    import models  # Import models to register them with SQLAlchemy
    db.create_all()
    print("Database tables created successfully!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
