from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Donor
from app.utils import validate_phone
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()  # can be email or username
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter(
            (User.email.ilike(identifier)) | (User.username.ilike(identifier))
        ).first()

        if user and user.check_password(password):
            if not user.is_active_account:
                flash('This account has been deactivated. Please contact the administrator.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            next_page = request.args.get('next')
            if user.role == 'donor':
                return redirect(next_page or url_for('donor_portal.dashboard'))
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username/email or password. Please try again.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        gender = request.form.get('gender', '').strip()
        dob_str = request.form.get('date_of_birth', '')
        weight_kg = request.form.get('weight_kg', 0)
        address = request.form.get('address', '')
        city = request.form.get('city', 'Pune')

        # Medical History fields
        has_chronic_illness = bool(request.form.get('has_chronic_illness'))
        chronic_illness_details = request.form.get('chronic_illness_details', '').strip()
        has_recent_surgery = bool(request.form.get('has_recent_surgery'))
        has_recent_tattoo_piercing = bool(request.form.get('has_recent_tattoo_piercing'))
        on_medications = bool(request.form.get('on_medications'))
        medications_details = request.form.get('medications_details', '').strip()
        has_infectious_history = bool(request.form.get('has_infectious_history'))
        is_pregnant_or_nursing = bool(request.form.get('is_pregnant_or_nursing'))

        # Validations
        is_phone_valid, clean_phone = validate_phone(phone)
        if not is_phone_valid:
            flash('Phone number must be exactly 10 digits (e.g. 9876543210).', 'danger')
            return render_template('auth/register.html')
        phone = clean_phone

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first() or Donor.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            weight = float(weight_kg)
        except (ValueError, TypeError):
            flash('Invalid date of birth or weight format.', 'danger')
            return render_template('auth/register.html')

        # Create user account with donor role
        new_user = User(
            username=username,
            email=email,
            role='donor',
            full_name=full_name,
            phone=phone
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()

        # Determine initial status based on medical history
        init_status = 'Eligible'
        if has_infectious_history or has_chronic_illness:
            init_status = 'Deferred'
        elif has_recent_surgery or has_recent_tattoo_piercing or is_pregnant_or_nursing:
            init_status = 'Deferred'

        # Create corresponding Donor profile
        new_donor = Donor(
            user_id=new_user.id,
            first_name=full_name.split()[0] if full_name else username,
            last_name=" ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
            email=email,
            phone=phone,
            blood_group=blood_group,
            gender=gender,
            date_of_birth=dob,
            weight_kg=weight,
            address=address,
            city=city,
            status=init_status,
            has_chronic_illness=has_chronic_illness,
            chronic_illness_details=chronic_illness_details,
            has_recent_surgery=has_recent_surgery,
            has_recent_tattoo_piercing=has_recent_tattoo_piercing,
            on_medications=on_medications,
            medications_details=medications_details,
            has_infectious_history=has_infectious_history,
            is_pregnant_or_nursing=is_pregnant_or_nursing
        )
        db.session.add(new_donor)
        db.session.commit()

        flash('Registration successful! You can now log in to your donor account.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('auth.login'))
