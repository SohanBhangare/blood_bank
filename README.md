# 🩸 LifeFlow - Blood Bank Management System

A full-featured, secure, and modern **Blood Bank Management System** built with **Python 3**, **Flask**, **SQLite**, and **Tailwind CSS**. It covers the complete operational lifecycle of a clinical blood bank: donor recruitment, eligibility screening, blood collection & component separation, cold storage inventory tracking with shelf-life monitoring, emergency hospital requisitions with automated cross-match compatibility matrix, and analytical reporting.

---

## 🌟 Key Features

### 1. 🛡️ Role-Based Access Control (RBAC)
- **Admin**: Full administrative management, seed/reset capabilities, donor deletion, full reports export.
- **Staff / Phlebotomist**: Donor registration, recording collections & screening vitals, inventory management, hospital request triage & dispatch.
- **Donor**: Personalized donor portal, real-time eligibility countdown, donation history log, and downloadable **Certificate of Appreciation**.

### 2. 👥 Clinical Screening & Medical History Questionnaire
- **Detailed Clinical Questionnaire**:
  - History of chronic illnesses (Diabetes on insulin, hypertension, cardiac disorders).
  - Recent major surgeries or blood transfusions (within past 6 months).
  - Body piercings or tattoos (within past 6 months).
  - Current medications (blood thinners, antibiotics, immunosuppressants).
  - History of infectious diseases (Hepatitis B/C, HIV, Malaria within past 3 months).
  - Pregnancy or active nursing status.
- Automated medical eligibility validation (Age 18–65, Weight &ge; 50 kg, 90-day cooldown).
- Clinical vitals recording during donation: Blood Pressure, Hemoglobin (Hb), and Pulse.
- Serological / infectious diseases screening check (`Passed`, `Pending`, `Failed`).
- Printable **Blood Donor Recognition Certificate**.

### 3. 🎪 Live Blood Donation Camps & Mobile Drives Tracker
- Real-time directory of **Ongoing Today** and **Upcoming** blood donation camps.
- Details: Camp organizer, venue address, operating hours, target vs. collected blood units progress bar.
- One-click Google Maps directions and coordinator phone lines.
- Donors can pledge/RSVP to donate at any active camp.

### 4. 🏥 Which Hospital Takes Blood (Partner Hospital Directory)
- Comprehensive directory of accredited hospitals with in-house blood banks.
- Displays whether the hospital accepts 24x7 walk-in voluntary blood donations.
- Lists current critical blood group requirements for each hospital (e.g. trauma surgical ward needs).
- Direct one-click phone dialer for 24x7 Emergency Helplines.

### 5. 🚨 Nearby Emergency Blood SOS Live Broadcast
- Real-time feed of pending **Emergency** and **Urgent** hospital blood requisitions.
- Highlights critically needed blood groups, units requested, and patient clinical indications.
- Donors and citizens can respond immediately with direct hospital contact or pledge donation.

### 6. 📦 Smart Cold Storage Inventory
- Unit-level tracking with unique bag barcodes (e.g. `BB-OP-261025-X7K2`).
- Supports **Whole Blood**, **Red Blood Cells (PRBC)**, **Platelets (PC)**, and **Plasma (FFP)**.
- Automated shelf-life and expiration calculator (e.g. Platelets: 5 days, Whole Blood: 42 days, Plasma: 365 days).
- Real-time stock status cards for all 8 blood groups (`A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`).
- Critical low-stock warning banners (< 3 units).

### 7. 🚑 Hospital Requisition & Transfusion Compatibility Engine
- Urgent and Emergency request priority triage.
- Built-in **Universal Blood Compatibility Matrix**:
  - Automatically identifies safe cross-match donor groups (e.g. `O-` universal red cell donor, `AB+` universal recipient).
- One-click allocation and reservation of compatible blood units from storage.
- Dispatch tracking with cold chain logistics notes and receiver verification.

### 8. 📊 Reports & CSV Data Exports
- Real-time Chart.js interactive visualizations:
  - Blood Inventory distribution by group
  - Request fulfillment pipeline
- Instant CSV dataset downloads for:
  - Blood Inventory ledger
  - Registered Donors directory
  - Requisitions & Dispatches history
- Printer-friendly executive reports.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+ installed
- `pip` package manager

### 1. Installation
Clone or navigate to the project directory:
```bash
cd blood_bank
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Start the Flask development server:
```bash
python run.py
```

The database (`blood_bank.db`) and realistic sample dataset will be automatically initialized on first run.

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Default Demo Accounts

The system comes pre-seeded with 3 roles ready for testing:

| Role | Username / Email | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@bloodbank.com` | `admin123` | Full system control, reports, resets |
| **Staff** | `staff@bloodbank.com` | `staff123` | Donors, collections, inventory, dispatch |
| **Donor** | `donor@bloodbank.com` | `donor123` | Personal portal, eligibility status, certificates |

> 💡 **Tip:** On the login page, you can click any of the **Quick Demo Login** buttons to autofill credentials instantly!

---

## 🧪 Running Unit Tests

Run the test suite with Python's built-in `unittest`:
```bash
python -m unittest tests/test_app.py
```
