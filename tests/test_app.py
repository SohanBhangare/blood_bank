import unittest
from datetime import date, timedelta
from app import create_app, db
from app.models import User, Donor, Donation, BloodInventory, BloodRequest
from app.utils import is_compatible, get_compatible_donors_for_recipient
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class BloodBankTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create Admin
        self.admin = User(username='admin_test', email='admintest@example.com', role='admin')
        self.admin.set_password('pass123')

        # Create Staff
        self.staff = User(username='staff_test', email='stafftest@example.com', role='staff')
        self.staff.set_password('pass123')

        # Create Donor
        self.donor = Donor(
            first_name='Test',
            last_name='Donor',
            email='testdonor@example.com',
            phone='1234567890',
            blood_group='O+',
            gender='Male',
            date_of_birth=date(1995, 1, 1),
            weight_kg=70.0,
            status='Eligible'
        )

        db.session.add_all([self.admin, self.staff, self.donor])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_blood_compatibility(self):
        # O- is universal donor
        self.assertTrue(is_compatible('O-', 'AB+'))
        self.assertTrue(is_compatible('O-', 'O-'))
        self.assertTrue(is_compatible('O-', 'A+'))

        # AB+ is universal recipient
        compat = get_compatible_donors_for_recipient('AB+')
        self.assertIn('O-', compat)
        self.assertIn('A+', compat)
        self.assertIn('B-', compat)

        # O- can only receive O-
        self.assertEqual(get_compatible_donors_for_recipient('O-'), ['O-'])

    def test_donor_eligibility(self):
        # Healthy donor
        is_el, msg = self.donor.is_eligible_to_donate
        self.assertTrue(is_el)

        # Underweight donor
        self.donor.weight_kg = 45.0
        is_el, msg = self.donor.is_eligible_to_donate
        self.assertFalse(is_el)
        self.donor.weight_kg = 70.0

        # Recent donation cooldown (<90 days)
        self.donor.last_donation_date = date.today() - timedelta(days=30)
        is_el, msg = self.donor.is_eligible_to_donate
        self.assertFalse(is_el)
        self.donor.last_donation_date = None

        # Medical History: Infectious disease history
        self.donor.has_infectious_history = True
        is_el, msg = self.donor.is_eligible_to_donate
        self.assertFalse(is_el)
        self.assertIn("infectious", msg.lower())
        self.donor.has_infectious_history = False

        # Medical History: Recent tattoo or piercing
        self.donor.has_recent_tattoo_piercing = True
        is_el, msg = self.donor.is_eligible_to_donate
        self.assertFalse(is_el)
        self.assertIn("tattoo", msg.lower())
        self.donor.has_recent_tattoo_piercing = False

        # Medical History: Chronic illness
        self.donor.has_chronic_illness = True
        self.donor.chronic_illness_details = "Type 1 Diabetes"
        is_el, msg = self.donor.is_eligible_to_donate
        self.assertFalse(is_el)
        self.assertIn("diabetes", msg.lower())
        self.donor.has_chronic_illness = False

    def test_inventory_creation(self):
        inv = BloodInventory(
            bag_barcode='BB-OP-TEST-001',
            blood_group='O+',
            component='Whole Blood',
            collection_date=date.today(),
            expiry_date=date.today() + timedelta(days=42),
            status='Available'
        )
        db.session.add(inv)
        db.session.commit()

        self.assertFalse(inv.is_expired)
        self.assertGreater(inv.days_until_expiry, 40)

    def test_login_flow(self):
        resp = self.client.post('/auth/login', data={
            'identifier': 'admintest@example.com',
            'password': 'pass123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Hospital Blood Operations Center', resp.data)

    def test_routes_accessible(self):
        # Log in as admin
        self.client.post('/auth/login', data={
            'identifier': 'admintest@example.com',
            'password': 'pass123'
        }, follow_redirects=True)

        for route in ['/dashboard', '/donors/', '/inventory/', '/requests/', '/reports/', '/camps/', '/hospitals/', '/hospitals/emergency']:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed")

if __name__ == '__main__':
    unittest.main()
