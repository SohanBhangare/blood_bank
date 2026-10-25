import os
from app import create_app, db
from app.seed import seed_sample_data

app = create_app()

with app.app_context():
    db.create_all()
    # Auto-seed database if empty
    seed_sample_data()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==================================================")
    print(f" LifeFlow - Blood Bank Management System")
    print(f" Server running at: http://127.0.0.1:{port}")
    print(f" Demo Accounts:")
    print(f"   Admin:  admin@bloodbank.com / admin123")
    print(f"   Staff:  staff@bloodbank.com / staff123")
    print(f"   Donor:  donor@bloodbank.com / donor123")
    print(f"==================================================")
    app.run(host='127.0.0.1', port=port, debug=True)
