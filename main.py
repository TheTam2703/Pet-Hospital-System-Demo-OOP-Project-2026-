from HospitalClass import *
from fastmcp import FastMCP

def create_test():
    system = PetHospital("Test Pet Hospital")

    # ====== 0. MEDICINE ======
    med1 = Medicine("MED01", "Paracetamol", 50.0)
    system.add_medicine(med1)

    # ====== 1. USER + PET ======
    user = User("U001", "Tam", "0999999999")
    user2 = User("U002", "Staffer", "4445556666", "STAFF")
    user.add_petprofile("P001", "AIDUM", Species.DOG, 12.0, Sex.MALE, "13/04/2017", [])
    user2.add_petprofile("P002", "tood", Species.CAT, 8.0, Sex.FEMALE, "14/08/2019", [])
    system.add_user(user)
    system.add_user(user2)

    # ====== 2. STAFF ======
    vet = Vet("V001", "Dr. Somchai", 35000.0, Species.DOG, "7778889999")
    vet2 = Vet("V002", "Dr. Jaidee", 35000.0, Species.CAT, "0004445555")
    vet.add_timeslot(datetime(2026, 3, 10, 10, 0))
    vet.add_timeslot(datetime(2026, 3, 15, 10, 0))
    vet2.add_timeslot(datetime(2026, 3, 12, 14, 0))
    vet2.add_timeslot(datetime(2026, 3, 12, 16, 0))
    vet2.add_timeslot(datetime(2026, 3, 12, 10, 0))
    system.add_employee(vet)
    system.add_employee(vet2)

    # ====== 3. WARD + CAGES ======
    ward = Ward("W01", WardType.STANDARD)
    cage1 = Cage("C1", CageSize.S, None, CageStatus.AVAILABLE)
    cage2 = Cage("C2", CageSize.M, None, CageStatus.AVAILABLE)
    ward.add_cage(cage1)
    ward.add_cage(cage2)
    system.add_ward(ward)

    # ====== 4. APPOINTMENT & MEDICAL RECORD ======
    pet = user.get_pet_by_id("P001")
    appt = Appointment("APP001", user.user_id, vet.employee_id, pet,
                       datetime(2026, 3, 10, 9, 0), AppointmentStatus.COMPLETED)
    user.current_appointment = appt
    system.add_appointment(appt)
    vet.book_timeslot(datetime(2026, 3, 10, 10, 0))

    prescription = Prescription(med1, "Take 1 pill twice a day", 2)
    system.make_medical_record(
        medical_id="M001",
        date="10/03/2026 10:00",
        symptoms="fever",
        diagnosis="infection",
        prescription=[prescription],
        admit=True,
        examination_fee=500.0,
        appointment=appt
    )
    return system

system = create_test()

#============ MCP ============#

mcp = FastMCP("Pet Hospital Management System")

# ==================== MCP TOOLS ====================

# =============== USER MANAGEMENT ===============
@mcp.tool()
def add_user(user_id: str, name: str, phone_num: str) -> str:
    """Add a new user. Raises error on duplicate user_id."""
    try:
        user = User(user_id, name, phone_num)
        system.add_user(user)
        return f"User {name} (ID: {user_id}) added successfully"
    except ValueError as e:
        return str(e)

@mcp.tool()
def add_pet_to_user(user_id: str, pet_id: str, name: str, species: str, weight: float,
                    sex: str, birthdate: str, allergies: list[str] = []) -> str:
    """Add a pet profile to an existing user. Species: DOG/CAT/EXOTIC, Sex: MALE/FEMALE"""
    user = system.search_user_by_id(user_id)
    if not user:
        return f"User {user_id} not found"
    try:
        species_enum = Species[species.upper()]
        sex_enum = Sex[sex.upper()]
        allergy_meds = [system.search_medicine_by_id(m) for m in allergies
                        if system.search_medicine_by_id(m)]
        user.add_petprofile(pet_id, name, species_enum, weight, sex_enum, birthdate, allergy_meds)
        return f"Pet {name} (ID: {pet_id}) added to user {user_id}"
    except ValueError as e:
        return str(e)

@mcp.tool()
def get_user_info(user_id: str) -> dict:
    """Get detailed information about a user and their pets."""
    user = system.search_user_by_id(user_id)
    if not user:
        return {"error": f"User {user_id} not found"}
    pets = [{"pet_id": p.id, "name": p.name, "species": p.species.name,
             "weight": p.weight, "admitted_cage": p.is_admit()} for p in user.pet_list]
    return {
        "user_id": user.user_id,
        "name": user.name,
        "no_show_left": user.no_show_left,
        "current_appointment": user.current_appointment.appointment_id if user.current_appointment else None,
        "pets": pets
    }

# =============== VETERINARIAN MANAGEMENT ===============
@mcp.tool()
def add_veterinarian(employee_id: str, user_id: str, name: str, salary: float,
                     expertise: str, phone_num: str) -> str:
    """Add a new veterinarian. Expertise: DOG/CAT/EXOTIC"""
    try:
        expertise_enum = Species[expertise.upper()]
        vet = Vet(employee_id, user_id, name, salary, expertise_enum, phone_num)
        system.add_employee(vet)
        return f"Veterinarian Dr. {name} (ID: {employee_id}) added successfully"
    except ValueError as e:
        return str(e)

@mcp.tool()
def add_vet_timeslot(vet_id: str, date_time: str) -> str:
    """Add available timeslot for a vet. Format: DD/MM/YYYY HH:MM"""
    vet = system.search_employee_by_id(vet_id)
    if not vet:
        return f"Vet {vet_id} not found"
    dt = datetime.strptime(date_time, "%d/%m/%Y %H:%M")
    vet.add_timeslot(dt)
    return f"Timeslot {date_time} added for vet {vet_id}"

@mcp.tool()
def get_vet_availability(vet_id: str) -> dict:
    """Get all available timeslots for a veterinarian."""
    vet = system.search_employee_by_id(vet_id)
    if not vet:
        return {"error": f"Vet {vet_id} not found"}
    slots = [slot.date.strftime("%d/%m/%Y %H:%M") for slot in vet.timeslots if slot.available]
    return {"vet_id": vet_id, "expertise": vet.expertise.name, "available_slots": slots}

# =============== STAFF MANAGEMENT ===============
@mcp.tool()
def add_hospital_staff(employee_id: str, user_id: str, name: str, salary: float, phone_num: str) -> str:
    """Add a new front-desk HospitalStaff member. Handles check-ins, bookings, admissions, and payments."""
    try:
        staff = HospitalStaff(employee_id, user_id, name, salary, phone_num)
        system.add_employee(staff)
        return f"HospitalStaff {name} (ID: {employee_id}) added successfully"
    except ValueError as e:
        return str(e)

@mcp.tool()
def add_hospital_manager(employee_id: str, user_id: str, name: str, salary: float, phone_num: str) -> str:
    """Add a new HospitalManager. Oversees staff, wards, cages, medicines, and pricing."""
    try:
        manager = HospitalManager(employee_id, user_id, name, salary, phone_num)
        system.add_employee(manager)
        return f"HospitalManager {name} (ID: {employee_id}) added successfully"
    except ValueError as e:
        return str(e)

# =============== APPOINTMENT MANAGEMENT ===============
@mcp.tool()
def book_appointment(user_id: str, vet_id: str, pet_id: str, chosen_date: str) -> str:
    """Book an appointment. Date format: DD/MM/YYYY HH:MM. Cannot book past dates."""
    result = system.book_appointment(user_id, vet_id, pet_id, chosen_date)
    if isinstance(result, Appointment):
        return (f"Appointment booked successfully!\n"
                f"Appointment ID    : {result.appointment_id}\n"
                f"Booking date      : {result.date_created}\n"
                f"Scheduled date    : {result.scheduled_date}\n"
                f"Vet               : {result.vet_id}\n"
                f"Pet               : {result.pet.name}\n"
                f"Status            : {result.status}")
    return f"Booking failed: {result}"

@mcp.tool()
def get_appointment_details(appointment_id: str) -> dict:
    """Get details of a specific appointment."""
    appt = system.search_appointment_by_id(appointment_id)
    if not appt:
        return {"error": f"Appointment {appointment_id} not found"}
    return {
        "appointment_id": appt.appointment_id,
        "user_id": appt.user_id,
        "vet_id": appt.vet_id,
        "pet_id": appt.pet.id,
        "date": appt.scheduled_date.strftime("%d/%m/%Y %H:%M"),
        "status": appt.status.name
    }

@mcp.tool()
def checkin_patient(appointment_id: str, user_id: str, check_in_time: str = None) -> str:
    """
    Check in a patient.
    - Cannot check in before appointment time.
    - More than 30 min late → auto NO_SHOW, user freed to rebook.
    check_in_time format: DD/MM/YYYY HH:MM (defaults to now)
    """
    return system.check_in(appointment_id, user_id, check_in_time)

@mcp.tool()
def cancel_appointment(appointment_id: str, user_id: str) -> str:
    """
    Cancel an appointment.
    - Cannot cancel if CHECKED_IN.
    - Cannot cancel within 2 hours of the appointment.
    """
    return system.cancel_appointment(appointment_id, user_id)

@mcp.tool()
def get_receipt_list(user_id: str) -> dict:
    """[6] Get itemised bill for the user's current appointment."""
    return system.get_receipt(user_id)

# =============== MEDICINE MANAGEMENT ===============
@mcp.tool()
def add_medicine(medicine_id: str, name: str, unit_price: float) -> str:
    """Add a new medicine to the system."""
    med = Medicine(medicine_id, name, unit_price)
    system.add_medicine(med)
    return f"Medicine {name} (ID: {medicine_id}) added at {unit_price} baht/unit"

@mcp.tool()
def update_medicine_price(medicine_id: str, new_price: float) -> str:
    """Update the price of a medicine."""
    return system.new_medicine_price(medicine_id, new_price)

@mcp.tool()
def create_prescription(medicine_id: str, amount: int, instruction: str, pet_id: str) -> str:
    """Create a prescription. Returns allergy warning if applicable."""
    result = system.write_prescription(medicine_id, amount, instruction, pet_id)
    if isinstance(result, Prescription):
        return f"Prescription created: {amount} units of {medicine_id} — {instruction}"
    return f"Cannot prescribe: {result}"

# =============== WARD & CAGE MANAGEMENT ===============
@mcp.tool()
def add_ward(ward_id: str, ward_type: str) -> str:
    """Add a new ward. Ward type: Standard / ICU / Isolation"""
    ward_type_enum = WardType[ward_type]
    ward = Ward(ward_id, ward_type_enum)
    system.add_ward(ward)
    return f"Ward {ward_id} ({ward_type}) added successfully"

@mcp.tool()
def add_cage_to_ward(ward_id: str, cage_id: str, size: str) -> str:
    """Add a cage to a ward. Size: S (≤5 kg) / M (≤15 kg) / L (≤30 kg)"""
    ward = system.search_ward_by_id(ward_id)
    if not ward:
        return f"Ward {ward_id} not found"
    cage_exist: Ward = system.cage_existed_on_ward(cage_no=cage_id)
    if cage_exist != None:
        return f"Cage {cage_id} is already existed on ward {cage_exist.id}"
    size_enum = CageSize[size.upper()]
    cage = Cage(cage_id, size_enum, None, CageStatus.AVAILABLE)
    ward.add_cage(cage)
    return f"Cage {cage_id} (size {size}) added to ward {ward_id}"

@mcp.tool()
def remove_cage(cage_no: str):
    if system.remove_cage(cage_no) == None:
        return f"Cage number {cage_no} not found."
    return f"Removed Cagen number {cage_no} successfully."

@mcp.tool()
def update_cage_price(size: str, new_price: float) -> str:
    """Update the daily price for a cage size (S/M/L)."""
    return system.new_cage_price(size.upper(), new_price)

# =============== MEDICAL RECORDS & TREAMENT ===================
@mcp.tool()
def create_medical_record(medical_id: str, date: str, appointment_id: str, symptoms: str,
                          diagnosis: str, prescription_list: list[dict], admit: bool,
                          examination_fee: float) -> str:
    """
    Create a medical record. Appointment must be CHECKED_IN.
    prescription_list: [{"medicine_id": "MED01", "amount": 2, "instruction": "Twice daily"}]
    Date format: DD/MM/YYYY HH:MM
    """
    appt = system.search_appointment_by_id(appointment_id)
    if not appt:
        return f"Appointment {appointment_id} not found"
    prescriptions = []
    for p in prescription_list:
        med = system.search_medicine_by_id(p["medicine_id"])
        if med:
            prescriptions.append(Prescription(med, p["instruction"], p["amount"]))
    result = system.make_medical_record(medical_id, date, symptoms, diagnosis,
                                        prescriptions, admit, examination_fee, appt)
    return result

@mcp.tool()
def admit_patient(medical_record_id: str, date_admit: str, ward_type: str = "STANDARD") -> str:
    """
    Admit a patient. Appointment must be CHECKED_IN.
    """
    return system.admit(medical_record_id, date_admit, ward_type=ward_type)

@mcp.tool()
def checkout_patient(medical_record_id: str, date_leave: str) -> str:
    """
    Check out a patient. Payment must be completed first if balance > 0.
    Date format: DD/MM/YYYY HH:MM
    """
    return system.check_out(medical_record_id, date_leave)

@mcp.tool()
def get_admitted_pets(user_id: str) -> dict:
    """Get all currently admitted pets for a user with their cage numbers."""
    return system.display_pet_admit(user_id)

@mcp.tool()
def get_medical_records_for_pet(pet_id: str) -> list:
    """Get all medical records attached to this pet"""
    return system.display_all_medical_records_for_pet(pet_id)

# ========== PAYMENT ============

@mcp.tool()
def calculate_total_payment(user_id: str) -> float:
    """Calculate the total bill for a user's current appointment."""
    return system.calculate_payment(user_id)

@mcp.tool()
def pay_appointment(user_id: str, payment_method: str) -> str:
    """
    Record payment for the current appointment
    Payment methods: Cash / QR
    """
    return system.make_payment(user_id, payment_method)

@mcp.tool()
def clear_user_appointment(user_id: str) -> str:
    """Clear the current appointment for a user after payment and checkout."""
    user = system.clear_appointment(user_id)
    if user:
        return f"Appointment cleared for user {user_id}"
    return f"User {user_id} not found"

# ==================== CAGE BOOKING TOOLS ====================

@mcp.tool()
def book_cage(user_id: str, pet_id: str, cage_size: str, ward_type: str,
              stay_date: str, duration_hours: int) -> str:
    """
    Reserve a cage for a pet for a fixed boarding period (no vet appointment needed).

    Rules:
    - stay_date must be in the future                        
    - duration must be between 1 and 24 hours              
    - pet weight must fit the selected cage size              
    - no overlapping bookings on the same cage               
    - pet may only have one active booking at a time        
    - ward type is respected (Standard / ICU / Isolation)   
    """
    result = system.book_cage(user_id, pet_id, cage_size, stay_date, duration_hours, ward_type=WardType.STANDARD.name)
    if isinstance(result, CageBooking):
        return (f"Cage booked successfully!\n"
                f"Booking ID : {result.booking_id}\n"
                f"Pet        : {result.pet.name}\n"
                f"Cage       : {result.cage.no} (size {result.cage.size.name})"
                f" in ward {result.ward.id} ({result.ward.type.name})\n"
                f"Check-in   : {result.stay_date.strftime('%d/%m/%Y %H:%M')}\n"
                f"Check-out  : {result.leave_date.strftime('%d/%m/%Y %H:%M')}\n"
                f"Total cost : {CageService.CAGE_PRICES_PER_HOUR[result.cage.size.name] * duration_hours} baht\n"
                f"Status : {result.status}")
    return f"Booking failed: {result}"

@mcp.tool()
def cancel_cage_booking(booking_id: str, user_id: str) -> str:
    """
    Cancel a cage booking.

    Rules:
    - Must be CONFIRMED (cannot cancel once pet is checked in)
    - Cannot cancel within 24 hours of check-in              (R6)
    """
    return system.cancel_cage_booking(booking_id, user_id)

@mcp.tool()
def checkin_cage_booking(booking_id: str, user_id: str) -> str:
    """
    Mark a cage booking as CHECKED_IN when the pet physically arrives.
    Cannot check in before the booked stay_date.
    """
    return system.checkin_cage_booking(booking_id, user_id)

@mcp.tool()
def checkout_cage_booking(booking_id: str, user_id: str) -> str:
    """
    Mark a cage booking as COMPLETED when the owner collects their pet.
    Pet must be CHECKED_IN first.
    """
    return system.checkout_cage_booking(booking_id, user_id)

@mcp.tool()
def get_cage_bookings(user_id: str) -> list:
    """
    List all cage bookings for a user, sorted by check-in date.
    Returns booking ID, pet, cage, ward, dates, status, and total cost.
    """
    return system.get_cage_bookings_for_user(user_id)

@mcp.tool()
def get_cage_booking_details(booking_id: str) -> dict:
    """Get details of a specific cage booking by its ID."""
    booking = system.search_cage_booking_by_id(booking_id)
    if not booking:
        return {"error": f"Cage booking '{booking_id}' not found"}
    duration = (booking.leave_date - booking.stay_date).days or 1
    return {
        "booking_id":    booking.booking_id,
        "user_id":       booking.user.user_id,
        "pet_id":        booking.pet.id,
        "pet_name":      booking.pet.name,
        "ward_id":       booking.ward.id,
        "ward_type":     booking.ward.type.name,
        "cage_no":       booking.cage.no,
        "cage_size":     booking.cage.size.name,
        "stay_date":     booking.stay_date.strftime("%d/%m/%Y %H:%M"),
        "leave_date":    booking.leave_date.strftime("%d/%m/%Y %H:%M"),
        "duration_days": duration,
        "status":        booking.status.name,
        "total_cost":    booking.cage.size.get_price() * duration,
        "booked_on":     booking.booking_created.strftime("%d/%m/%Y %H:%M"),
    }

# ==================== MCP RESOURCES ====================

@mcp.resource("hospital://info")
def get_hospital_info() -> str:
    return f"Hospital Name: {system.name}\nFully operational Pet Hospital Management System"

@mcp.resource("hospital://statistics")
def get_hospital_statistics() -> dict:
    return {
        "total_users": len(system.get_all_users()),
        "total_employees": len(system.get_all_employees()),
        "total_appointments": len(system.get_all_appointments()),
        "total_wards": len(system.get_all_wards()),
        "total_medicines": len(system.get_all_medicines()),
        "total_medical_records": len(system.get_all_medical_records())
    }

@mcp.resource("hospital://users/list")
def list_all_users() -> list[dict]:
    return [{"user_id": u.user_id, "name": u.name, "no_show_left": u.no_show_left,
             "has_appointment": u.current_appointment is not None,
             "pets": len(u.pet_list)} for u in system.get_all_users()]

@mcp.resource("hospital://employees/list")
def list_all_employees() -> list[dict]:
    result = []
    for emp in system.get_all_employees():
        entry = {"employee_id": emp.employee_id, "name": emp.name, "role": emp.role}
        if isinstance(emp, Vet):
            entry["expertise"] = emp.expertise.name
            entry["available_slots"] = len([s for s in emp.timeslots if s.available])
        result.append(entry)
    return result

@mcp.resource("hospital://appointments/list")
def list_all_appointments() -> list[dict]:
    return [{"appointment_id": a.appointment_id, "user_id": a.user_id, "vet_id": a.vet_id,
             "pet_id": a.pet.id, "date": a.scheduled_date.strftime("%d/%m/%Y %H:%M"),
             "status": a.status.name} for a in system.get_all_appointments()]

@mcp.resource("hospital://wards/list")
def list_all_wards() -> list[dict]:
    wards = []
    for ward in system.get_all_wards():
        cages = [{"cage_id": c.no, "size": c.size.name, "max_weight": c.size.value,
                  "daily_price": c.size.get_price(), "status": c.status.name}
                 for c in ward.get_cages()]
        wards.append({"ward_id": ward.id, "type": ward.type.name,
                      "total_cages": len(cages), "cages": cages})
    return wards

@mcp.resource("hospital://medicines/list")
def list_all_medicines() -> list[dict]:
    return [{"medicine_id": m.id, "name": m.name, "unit_price": m.unit_price}
            for m in system.get_all_medicines()]

@mcp.resource("hospital://cage-bookings/list")
def list_all_cage_bookings() -> list[dict]:
    """List every cage booking in the system with key details."""
    result = []
    for b in sorted(system.get_all_cage_bookings(), key=lambda x: x.stay_date):
        duration = (b.leave_date - b.stay_date).days or 1
        result.append({
            "booking_id":  b.booking_id,
            "user_id":     b.user.user_id,
            "pet_id":      b.pet.id,
            "cage_no":     b.cage.no,
            "ward_id":     b.ward.id,
            "ward_type":   b.ward.type.name,
            "stay_date":   b.stay_date.strftime("%d/%m/%Y %H:%M"),
            "leave_date":  b.leave_date.strftime("%d/%m/%Y %H:%M"),
            "duration_days": duration,
            "status":      b.status.name,
        })
    return result

@mcp.resource("hospital://medical_records/list")
def list_all_medical_records() -> list[dict]:
    """ List every medical records with all of its detail"""
    result = []
    for mr in sorted(system.get_all_medical_records(), key=lambda x: x.date_recorded):
        result.append({
            "id" : mr.get_medical_id(),
            "appointment": mr.get_appointment().appointment_id,
            "date_recorded": mr.date_recorded,
            "pet": mr.get_pet(),
            "vet": mr.get_vet(),
            "symptoms": mr.symptoms,
            "diagnosis": mr.diagnosis,
            "prescription": mr.Prescription,
            "admit_record": mr.get_admit_record()    
        })
    return result

if __name__ == "__main__":
    mcp.run()