-- USERS TABLE (must exist first)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PATIENTS
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    contact_number VARCHAR(15) UNIQUE NOT NULL,
    medical_record_number VARCHAR(20) UNIQUE NOT NULL,
    blood_group VARCHAR(10) CHECK (blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    marital_status VARCHAR(20) CHECK (marital_status IN ('Single', 'Married', 'Divorced', 'Widowed', 'Other')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PATIENT HISTORY
CREATE TABLE IF NOT EXISTS patient_history (
    id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    past_diagnoses TEXT,
    surgeries TEXT,
    hospital_admissions TEXT,
    immunization_records TEXT,
    family_medical_history TEXT,
    lifestyle_factors TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HOSPITALS
CREATE TABLE IF NOT EXISTS hospitals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    contact_number VARCHAR(15),
    website TEXT
);

-- DOCTORS
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    experience INTEGER CHECK (experience >= 0),
    rating NUMERIC(2,1) CHECK (rating >= 0 AND rating <= 5),
    hospital_id INTEGER REFERENCES hospitals(id) ON DELETE SET NULL
);

-- AVAILABILITY SLOTS
CREATE TABLE IF NOT EXISTS availability_slots (
    id SERIAL PRIMARY KEY,
    doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    available_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (start_time < end_time)
);

-- REVIEWS
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    rating DECIMAL(3,2) NOT NULL CHECK (rating >= 0 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- APPOINTMENTS
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    slot_id INT NOT NULL REFERENCES availability_slots(id) ON DELETE CASCADE,
    appointment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VISITS
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    visit_date DATE NOT NULL,
    department VARCHAR(100) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SPECIALISTS
CREATE TABLE IF NOT EXISTS specialists (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

-- SYMPTOMS
CREATE TABLE IF NOT EXISTS symptoms (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

-- SPECIALIST_SYMPTOM (MANY-TO-MANY)
CREATE TABLE IF NOT EXISTS specialist_symptom (
    specialist_id INT REFERENCES specialists(id) ON DELETE CASCADE,
    symptom_id INT REFERENCES symptoms(id) ON DELETE CASCADE,
    PRIMARY KEY (specialist_id, symptom_id)
);