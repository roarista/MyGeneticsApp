from app import app, db

# Create all database tables
with app.app_context():
    import models  # Import models to register them with SQLAlchemy
    db.create_all()
    print("Database tables created successfully!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
