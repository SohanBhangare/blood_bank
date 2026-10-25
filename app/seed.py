from datetime import date, timedelta, datetime
import random
from app import db
from app.models import User, Donor, Donation, BloodInventory, BloodRequest, Dispatch, DonationCamp, Hospital
from app.utils import BLOOD_GROUPS, generate_bag_barcode

def seed_sample_data():
    """Populates database with sample users, donors, donations, inventory, and requests."""
    # Check if data already exists
    if User.query.first():
        return False

    # 1. Create Users
    admin = User(
        username='admin',
        email='admin@bloodbank.com',
        role='admin',
        full_name='Dr. Sohan Sharma',
        phone='+91 98765 43210'
    )
    admin.set_password('admin123')

    staff = User(
        username='staff',
        email='staff@bloodbank.com',
        role='staff',
        full_name='Nurse Priya Patel',
        phone='+91 98234 56789'
    )
    staff.set_password('staff123')

    donor_user = User(
        username='donor_rahul',
        email='donor@bloodbank.com',
        role='donor',
        full_name='Rahul Deshmukh',
        phone='+91 99887 76655'
    )
    donor_user.set_password('donor123')

    db.session.add_all([admin, staff, donor_user])
    db.session.commit()

    # 2. Create Donors
    sample_donors_data = [
        {
            'first_name': 'Rahul', 'last_name': 'Deshmukh', 'email': 'donor@bloodbank.com',
            'phone': '+91 99887 76655', 'blood_group': 'O+', 'gender': 'Male',
            'date_of_birth': date(1995, 4, 15), 'weight_kg': 72.5,
            'address': 'Flat 302, Green Avenue, Baner', 'city': 'Pune', 'state': 'Maharashtra', 'pincode': '411045',
            'status': 'Eligible', 'user_id': donor_user.id
        },
        {
            'first_name': 'Ananya', 'last_name': 'Iyer', 'email': 'ananya.iyer@example.com',
            'phone': '+91 98765 11223', 'blood_group': 'A+', 'gender': 'Female',
            'date_of_birth': date(1998, 9, 21), 'weight_kg': 58.0,
            'address': '12 Rose Villa, Indiranagar', 'city': 'Bangalore', 'state': 'Karnataka', 'pincode': '560038',
            'status': 'Eligible'
        },
        {
            'first_name': 'Vikram', 'last_name': 'Singh', 'email': 'vikram.singh@example.com',
            'phone': '+91 98111 22334', 'blood_group': 'B+', 'gender': 'Male',
            'date_of_birth': date(1990, 11, 8), 'weight_kg': 81.0,
            'address': 'Sector 14, Civil Lines', 'city': 'Jaipur', 'state': 'Rajasthan', 'pincode': '302006',
            'status': 'Eligible'
        },
        {
            'first_name': 'Sneha', 'last_name': 'Kulkarni', 'email': 'sneha.k@example.com',
            'phone': '+91 97654 32109', 'blood_group': 'AB+', 'gender': 'Female',
            'date_of_birth': date(1993, 2, 14), 'weight_kg': 61.5,
            'address': '45 Shivaji Nagar', 'city': 'Pune', 'state': 'Maharashtra', 'pincode': '411005',
            'status': 'Eligible'
        },
        {
            'first_name': 'Amit', 'last_name': 'Verma', 'email': 'amit.verma@example.com',
            'phone': '+91 94230 98765', 'blood_group': 'O-', 'gender': 'Male',
            'date_of_birth': date(1988, 6, 30), 'weight_kg': 75.0,
            'address': 'Flat 101, Palm Grove, Andheri West', 'city': 'Mumbai', 'state': 'Maharashtra', 'pincode': '400053',
            'status': 'Eligible'
        },
        {
            'first_name': 'Kavita', 'last_name': 'Reddy', 'email': 'kavita.reddy@example.com',
            'phone': '+91 98490 12345', 'blood_group': 'A-', 'gender': 'Female',
            'date_of_birth': date(2000, 1, 10), 'weight_kg': 54.0,
            'address': 'Road No. 10, Banjara Hills', 'city': 'Hyderabad', 'state': 'Telangana', 'pincode': '500034',
            'status': 'Eligible'
        },
        {
            'first_name': 'Rohan', 'last_name': 'Mehta', 'email': 'rohan.mehta@example.com',
            'phone': '+91 99099 88776', 'blood_group': 'B-', 'gender': 'Male',
            'date_of_birth': date(1996, 7, 19), 'weight_kg': 68.0,
            'address': 'Navrangpura Cross Road', 'city': 'Ahmedabad', 'state': 'Gujarat', 'pincode': '380009',
            'status': 'Eligible'
        },
        {
            'first_name': 'Deepak', 'last_name': 'Nair', 'email': 'deepak.nair@example.com',
            'phone': '+91 94471 23456', 'blood_group': 'AB-', 'gender': 'Male',
            'date_of_birth': date(1991, 12, 5), 'weight_kg': 74.0,
            'address': 'MG Road, Panampilly Nagar', 'city': 'Kochi', 'state': 'Kerala', 'pincode': '682036',
            'status': 'Eligible'
        },
        {
            'first_name': 'Pooja', 'last_name': 'Sharma', 'email': 'pooja.sharma@example.com',
            'phone': '+91 98101 98101', 'blood_group': 'O+', 'gender': 'Female',
            'date_of_birth': date(1997, 8, 22), 'weight_kg': 56.5,
            'address': 'Preet Vihar, Vikas Marg', 'city': 'Delhi', 'state': 'Delhi', 'pincode': '110092',
            'status': 'Eligible'
        },
        {
            'first_name': 'Arjun', 'last_name': 'Kapoor', 'email': 'arjun.k@example.com',
            'phone': '+91 98200 44556', 'blood_group': 'A+', 'gender': 'Male',
            'date_of_birth': date(1985, 3, 17), 'weight_kg': 79.0,
            'address': 'Juhu Tara Road', 'city': 'Mumbai', 'state': 'Maharashtra', 'pincode': '400049',
            'status': 'Eligible'
        },
        {
            'first_name': 'Meera', 'last_name': 'Sen', 'email': 'meera.sen@example.com',
            'phone': '+91 98300 77889', 'blood_group': 'B+', 'gender': 'Female',
            'date_of_birth': date(2002, 5, 29), 'weight_kg': 52.0,
            'address': 'Salt Lake Sector 1', 'city': 'Kolkata', 'state': 'West Bengal', 'pincode': '700064',
            'status': 'Eligible'
        },
        {
            'first_name': 'Tushar', 'last_name': 'Joshi', 'email': 'tushar.j@example.com',
            'phone': '+91 97234 11224', 'blood_group': 'O-', 'gender': 'Male',
            'date_of_birth': date(1987, 10, 12), 'weight_kg': 70.0,
            'address': 'Kothrud, Paud Road', 'city': 'Pune', 'state': 'Maharashtra', 'pincode': '411038',
            'status': 'Deferred', 'medical_notes': 'Temporary deferral: Recent dental surgery'
        }
    ]

    donors = []
    for d_data in sample_donors_data:
        donor = Donor(**d_data)
        donors.append(donor)
        db.session.add(donor)
    db.session.commit()

    # 3. Create historical & recent Donations and Inventory
    today = date.today()
    components = ['Whole Blood', 'Red Blood Cells', 'Platelets', 'Plasma']

    for i, donor in enumerate(donors):
        # Create 1-3 donations for each eligible donor
        num_donations = 2 if i % 2 == 0 else 1
        for d_idx in range(num_donations):
            # dates from 100 days ago to 10 days ago
            days_ago = 110 - (d_idx * 50) - (i * 3)
            if days_ago < 5:
                days_ago = 5 + (i % 7)
            don_date = today - timedelta(days=days_ago)

            barcode = generate_bag_barcode(donor.blood_group)
            donation = Donation(
                donor_id=donor.id,
                donation_date=don_date,
                blood_group=donor.blood_group,
                component='Whole Blood',
                units=1,
                systolic_bp=random.randint(115, 125),
                diastolic_bp=random.randint(75, 84),
                hemoglobin_level=round(random.uniform(13.2, 16.5), 1),
                pulse_rate=random.randint(68, 78),
                bag_barcode=barcode,
                screening_status='Passed',
                remarks='Healthy donation, screened negative for all infectious markers',
                recorded_by_id=staff.id
            )
            db.session.add(donation)
            db.session.flush()

            donor.total_donations += 1
            if not donor.last_donation_date or don_date > donor.last_donation_date:
                donor.last_donation_date = don_date

            # Add to Inventory
            # Expiry: Whole blood lasts ~42 days, Platelets ~5 days, RBC ~42 days, Plasma ~365 days
            expiry = don_date + timedelta(days=42)
            unit_status = 'Available'
            if expiry < today:
                unit_status = 'Expired'
            elif d_idx == 0 and i in [0, 2, 4]:
                unit_status = 'Dispatched'

            inv = BloodInventory(
                bag_barcode=barcode,
                blood_group=donor.blood_group,
                component='Whole Blood',
                units=1,
                collection_date=don_date,
                expiry_date=expiry,
                status=unit_status,
                storage_location=f"Storage Unit {random.choice(['A', 'B', 'C'])}-Tray {random.randint(1, 5)}",
                donation_id=donation.id
            )
            db.session.add(inv)

    # Add extra units for each blood group so inventory is healthy
    extra_units_spec = [
        ('A+', 6), ('A-', 3), ('B+', 7), ('B-', 2),
        ('AB+', 4), ('AB-', 2), ('O+', 8), ('O-', 4)
    ]
    for bg, count in extra_units_spec:
        for c in range(count):
            don_date = today - timedelta(days=random.randint(2, 20))
            expiry = don_date + timedelta(days=42)
            code = generate_bag_barcode(bg)
            comp = random.choice(['Whole Blood', 'Whole Blood', 'Red Blood Cells', 'Platelets'])
            if comp == 'Platelets':
                expiry = don_date + timedelta(days=5)
            inv = BloodInventory(
                bag_barcode=code,
                blood_group=bg,
                component=comp,
                units=1,
                collection_date=don_date,
                expiry_date=expiry,
                status='Available',
                storage_location=f"Cold Bay {random.choice(['Alpha', 'Beta', 'Gamma'])}-Rack {random.randint(1, 6)}"
            )
            db.session.add(inv)

    db.session.commit()

    # 4. Create Sample Blood Requests
    requests_data = [
        {
            'patient_name': 'Ramesh Chandra', 'patient_age': 54, 'patient_gender': 'Male',
            'hospital_name': 'Ruby Hall Clinic, Pune', 'hospital_contact': '+91 20 6645 5500',
            'city': 'Pune',
            'doctor_name': 'Dr. H. K. Mehta', 'required_blood_group': 'O+',
            'component': 'Whole Blood', 'units_requested': 2, 'units_allocated': 2,
            'urgency': 'Emergency', 'diagnosis_reason': 'Emergency cardiac bypass surgery',
            'contact_person': 'Aakash Chandra (Son)', 'contact_phone': '+91 98811 22334',
            'status': 'Dispatched', 'request_date': today - timedelta(days=3),
            'required_by_date': today - timedelta(days=2), 'created_by_id': staff.id
        },
        {
            'patient_name': 'Sunita Deshpande', 'patient_age': 32, 'patient_gender': 'Female',
            'hospital_name': 'Sahyadri Specialty Hospital, Pune', 'hospital_contact': '+91 20 6721 3000',
            'city': 'Pune',
            'doctor_name': 'Dr. Sunita Kulkarni', 'required_blood_group': 'B+',
            'component': 'Red Blood Cells', 'units_requested': 1, 'units_allocated': 1,
            'urgency': 'Urgent', 'diagnosis_reason': 'Severe postpartum anemia',
            'contact_person': 'Manoj Deshpande', 'contact_phone': '+91 97665 43210',
            'status': 'Approved', 'request_date': today - timedelta(days=1),
            'required_by_date': today + timedelta(days=1), 'created_by_id': staff.id
        },
        {
            'patient_name': 'Mohammed Farooq', 'patient_age': 45, 'patient_gender': 'Male',
            'hospital_name': 'Sassoon General Hospital, Pune', 'hospital_contact': '+91 20 2612 8000',
            'city': 'Pune',
            'doctor_name': 'Dr. S. Nair', 'required_blood_group': 'A-',
            'component': 'Whole Blood', 'units_requested': 2, 'units_allocated': 0,
            'urgency': 'Emergency', 'diagnosis_reason': 'Polytrauma highway accident victim',
            'contact_person': 'Zubair Farooq', 'contact_phone': '+91 98212 34567',
            'status': 'Pending', 'request_date': today,
            'required_by_date': today, 'created_by_id': staff.id
        },
        {
            'patient_name': 'Geeta Agarwal', 'patient_age': 28, 'patient_gender': 'Female',
            'hospital_name': 'KEM Hospital Blood Center, Pune', 'hospital_contact': '+91 20 6603 7300',
            'city': 'Pune',
            'doctor_name': 'Dr. V. Prasad', 'required_blood_group': 'O-',
            'component': 'Whole Blood', 'units_requested': 1, 'units_allocated': 0,
            'urgency': 'Urgent', 'diagnosis_reason': 'Thalassemia recurring transfusion support',
            'contact_person': 'Suresh Agarwal', 'contact_phone': '+91 99001 12233',
            'status': 'Pending', 'request_date': today,
            'required_by_date': today + timedelta(days=2), 'created_by_id': admin.id
        },
        {
            'patient_name': 'Kalyan Sundaram', 'patient_age': 62, 'patient_gender': 'Male',
            'hospital_name': 'Deenanath Mangeshkar Hospital, Pune', 'hospital_contact': '+91 20 4015 1000',
            'city': 'Pune',
            'doctor_name': 'Dr. R. Gill', 'required_blood_group': 'AB+',
            'component': 'Platelets', 'units_requested': 2, 'units_allocated': 0,
            'urgency': 'Normal', 'diagnosis_reason': 'Dengue fever with thrombocytopenia',
            'contact_person': 'Venkatesh Sundaram', 'contact_phone': '+91 98140 55667',
            'status': 'Pending', 'request_date': today,
            'required_by_date': today + timedelta(days=3), 'created_by_id': staff.id
        }
    ]

    for req_data in requests_data:
        req = BloodRequest(**req_data)
        db.session.add(req)

    # 5. Create Donation Camps (Ongoing & Upcoming)
    camps_data = [
        {
            'name': 'Red Cross Mega LifeSaver Blood Camp',
            'organizer': 'Indian Red Cross Society & Sassoon Blood Bank',
            'venue': 'Magarpatta Cybercity Amphitheatre, Tower 7',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411028',
            'start_date': today - timedelta(days=1),
            'end_date': today + timedelta(days=1),
            'operating_hours': '09:00 AM - 06:00 PM',
            'contact_person': 'Dr. Anita Joshi',
            'contact_phone': '+91 98220 12345',
            'target_units': 150,
            'collected_units': 72,
            'status': 'Ongoing',
            'facilities': 'Air-conditioned mobile bus, verified phlebotomists, donor donor cards, fruit juices & sandwiches'
        },
        {
            'name': 'Rotary Club City Center Blood Drive',
            'organizer': 'Rotary Club Midtown & Ruby Hall Blood Center',
            'venue': 'Bal Gandharva Ranga Mandir Forecourt, JM Road',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411005',
            'start_date': today,
            'end_date': today,
            'operating_hours': '08:30 AM - 05:00 PM',
            'contact_person': 'Rtn. Rajesh Gandhi',
            'contact_phone': '+91 98900 23456',
            'target_units': 100,
            'collected_units': 48,
            'status': 'Ongoing',
            'facilities': 'Fast-track screening, doctor consultation, digital certificate instant issuance'
        },
        {
            'name': 'Hinjawadi IT Park Weekend Blood Drive',
            'organizer': 'Tech Mahindra Foundation & Sahyadri Hospitals',
            'venue': 'Phase 1 Quadron Business Park, Central Atrium',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411057',
            'start_date': today + timedelta(days=3),
            'end_date': today + timedelta(days=4),
            'operating_hours': '10:00 AM - 05:30 PM',
            'contact_person': 'Vikram Shinde',
            'contact_phone': '+91 97654 99887',
            'target_units': 120,
            'collected_units': 0,
            'status': 'Upcoming',
            'facilities': 'Corporate donor wellness kit, free hemoglobin check, priority camp badges'
        },
        {
            'name': 'Pune University Youth Donation Festival',
            'organizer': 'NSS Savitribai Phule Pune University & KEM Blood Bank',
            'venue': 'Main Administrative Grounds, Ganeshkhind',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411007',
            'start_date': today + timedelta(days=7),
            'end_date': today + timedelta(days=8),
            'operating_hours': '09:00 AM - 04:00 PM',
            'contact_person': 'Prof. M. K. Kulkarni',
            'contact_phone': '+91 94220 54321',
            'target_units': 200,
            'collected_units': 0,
            'status': 'Upcoming',
            'facilities': 'Student donor merit points, health cards, commemorative donor medal'
        }
    ]

    for camp_data in camps_data:
        camp = DonationCamp(**camp_data)
        db.session.add(camp)

    # 6. Create Partner Hospitals (Which hospital takes blood & in-house blood banks)
    hospitals_data = [
        {
            'name': 'Ruby Hall Clinic & Trauma Center',
            'hospital_type': 'Level 1 Trauma & Super-Specialty',
            'address': '40 Sassoon Road, Sangamvadi',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411001',
            'phone': '+91 20 6645 5100',
            'emergency_helpline': '+91 20 6645 5555 (24x7 Emergency SOS)',
            'accepts_donations': True,
            'blood_bank_inhouse': True,
            'blood_groups_accepted': 'All Blood Groups (A+, A-, B+, B-, AB+, AB-, O+, O-)',
            'urgent_requirements': 'CRITICAL: High demand for O- Negative and A- for cardiac trauma surgery',
            'timing': '24/7 Round-the-clock Blood Intake & Transfusion Wing'
        },
        {
            'name': 'Sassoon General Hospital & Central Blood Bank',
            'hospital_type': 'Government Medical College & Tertiary Care',
            'address': 'Station Road, Near Pune Railway Station',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411001',
            'phone': '+91 20 2612 8000',
            'emergency_helpline': '+91 20 2612 8055 (State Helpline)',
            'accepts_donations': True,
            'blood_bank_inhouse': True,
            'blood_groups_accepted': 'All Blood Groups accepted free of charge',
            'urgent_requirements': 'URGENT: B+ and O+ red cell units needed for pediatric and burns wards',
            'timing': '24/7 State-of-the-Art Blood Bank & Apheresis Center'
        },
        {
            'name': 'Sahyadri Super Specialty Hospital',
            'hospital_type': 'Multi-Specialty & Neuro-Trauma Care',
            'address': 'Plot No. 30-C, Erandwane, Karve Road',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411004',
            'phone': '+91 20 6721 3000',
            'emergency_helpline': '+91 20 6721 5555',
            'accepts_donations': True,
            'blood_bank_inhouse': True,
            'blood_groups_accepted': 'All Groups (Whole blood, platelets, plasma)',
            'urgent_requirements': 'Immediate requirement for Single Donor Platelets (SDP) - any group',
            'timing': '24/7 Emergency Blood Bank Services'
        },
        {
            'name': 'KEM Hospital & Research Centre',
            'hospital_type': 'Charitable Trust & Referral Hospital',
            'address': '489 Rasta Peth, Mudaliar Road',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411011',
            'phone': '+91 20 6603 7300',
            'emergency_helpline': '+91 20 6603 7333',
            'accepts_donations': True,
            'blood_bank_inhouse': True,
            'blood_groups_accepted': 'All Blood Groups',
            'urgent_requirements': 'Ongoing requirement for Thalassemia and Hemophilia transfusion unit',
            'timing': 'Open 24/7 for voluntary donation walk-ins'
        },
        {
            'name': 'Deenanath Mangeshkar Hospital & Research Center',
            'hospital_type': 'Super Specialty & Cancer Institute',
            'address': 'Near Mhatre Bridge, Erandwane',
            'city': 'Pune',
            'state': 'Maharashtra',
            'pincode': '411038',
            'phone': '+91 20 4015 1000',
            'emergency_helpline': '+91 20 4015 1111',
            'accepts_donations': True,
            'blood_bank_inhouse': True,
            'blood_groups_accepted': 'All Blood Groups (Whole Blood, PRBC, FFP, Platelets)',
            'urgent_requirements': 'Active need for AB+ and AB- Plasma and Platelets for oncology patients',
            'timing': '24/7 NABH Accredited Blood Bank'
        }
    ]

    for hosp_data in hospitals_data:
        hosp = Hospital(**hosp_data)
        db.session.add(hosp)

    db.session.commit()
    return True
