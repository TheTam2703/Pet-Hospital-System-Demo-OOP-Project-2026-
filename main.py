from HospitalClass import *
import uvicorn
from fastapi import FastAPI

def create_test():
    system = PetHospital("Test Pet Hospital")

    # ====== 0. MEDICINE ======
    # สร้างข้อมูลยาเข้าระบบ เพื่อใช้ตอนทำ Prescription และนำไปคำนวณค่าใช้จ่าย
    med1 = Medicine("MED01", "Dog Paracetamol", 50.0)
    system.add_medicine(med1)

    # ====== 1. USER + PET ======
    user = User("U001", "Tam", "0999999999")
    user.add_petprofile(
        pet_id="P001",
        name="AIDUM",
        species=Species.DOG,
        weight=12.0,
        sex=Sex.MALE,
        birthdate="13/04/2017",
        allergy= []
         # เพิ่มพารามิเตอร์ allergy (ตามที่กำหนดไว้ใน __init__ ของ PetProfile)
    )
    system.add_user(user)

    # ====== 2. VET ======
    vet = Vet(
        employee_id="V001",
        user_id="EMP001",
        name="Dr. Somchai",
        salary=35000.0,
        expertise=Species.DOG,
        phone_num= "1234"
    )
    # เพิ่ม Timeslot ว่างให้หมอ เพื่อรองรับ Test Case: Booking
    vet.add_timeslot(datetime(2026, 3, 10, 10, 0)) 
    vet.add_timeslot(datetime(2026, 3, 15, 10, 0)) # Slot สำหรับทดสอบจองวันอื่น
    system.add_employee(vet)

    # ====== 3. WARD + CAGES ======
    ward = Ward("W01", WardType.Standard)
    # กรง Size S รับน้ำหนักได้ไม่เกิน 5.0kg / Size M รับได้ไม่เกิน 15.0kg
    cage1 = Cage("C1", CageSize.S, None, CageStatus.AVAILABLE)
    cage2 = Cage("C2", CageSize.M, None, CageStatus.AVAILABLE) # AIDUM หนัก 12kg จะถูกจัดเข้ากรงนี้
    ward.add_cage(cage1)
    ward.add_cage(cage2)
    system.add_ward(ward)

    # ====== 4. APPOINTMENT & MEDICAL RECORD ======
    # เพื่อรองรับ Test Case: Admit, Checkout และ Calculate Payment
    pet = user.get_pet_by_id("P001")
    
    # 4.1 จำลองว่ามี Appointment เกิดขึ้นแล้ว (สถานะ CHECKED_IN)
    appt = Appointment("APP001", user.user_id, vet.employee_id, pet, datetime(2026, 3, 10, 9, 0), AppointmentStatus.CHECKED_IN)
    user.current_appointment = appt
    system.add_appointment(appt)

    # 4.2 สร้างรายการยาที่สั่ง (จำนวน 2 หน่วย x 50 บาท = 100 บาท)
    prescription = Prescription(med1, "Take 1 pill twice a day", 2)

    # 4.3 สร้างประวัติการรักษา (สั่ง Admit = True, ค่าตรวจ = 500 บาท, ผูกกับ Appointment)
    system.make_medical_record(
        medical_id="M001",
        date="10/03/2026 10:00",
        symtomps="fever", 
        diagnosis="infection",
        prescription=[prescription], # ต้องใส่เป็น List
        admit=True,           
        examination_fee=500.0,       # กำหนดค่าตรวจ
        appointment=appt             # ต้องผูก Appointment เพื่อให้ตอน Checkout นำค่ากรงไปรวมบิลได้
    )

    return system

system = create_test()
    
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "Pet Hospital"}

@app.get("/calculate total",tags= ["Staff"])
def calculate_total(user_id):
    total = system.calculate_payment(user_id)
    return {"total" : total}

@app.get("/display pet admit",tags= ['Owner'])
def display_pet(user_id: str):
    get = system.display_pet_admit(user_id= user_id)
    return get

@app.post("/book_appointment",tags= ['Owner'])
def book_appointment(user_id: str, vet_id: str, pet_id: str, chosen_date: str):

    fmt = "%d/%m/%Y %H:%M"
    try:
        formated_desired_date = datetime.strptime(chosen_date, fmt)
        result = system.book_appointment(user_id, vet_id, pet_id, formated_desired_date)
        if isinstance(result, str):
            return {"success": False, "message": result}
        
        return {
            "success" : True,
            "data" : {
                "appointment_id": result.appointment_id,
                "appointment_status": result.appointment_status,
                "date": result.date,
                "vet_id": result.vet_id,
                "user_id": result.user_id,
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Sum thing wrong: {str(e)}"}
    
@app.get("/admit",tags=["Staff"])
def get_admit_record(MedID):
    for med in system.get_med_list():
        if(med.get_medical_id() == MedID):
            if(isinstance(med.get_admit_record(),AdmitRecord)):
                cage_id = med.get_admit_record().get_cage().no
                pet_id = med.get_admit_record().get_pet()
                return {pet_id : cage_id}
            return {MedID : med.get_admit_record()}
    return {MedID : "can't find this ID"}

@app.post("/admit", tags=["Staff"])
def admit(MedID: str, date_in: str)-> dict:

    status = system.admit(MedID, date_in)
    return {"status" : status}

@app.post("/checkout", tags=['Staff'])
def check_out(Medical_recordID : str, date_leave: str):
    status = system.check_out(Medical_recordID, date_leave)
    return {"status" : status}
@app.patch("/clear.current.appointment", tags= ['Staff'])
def clear_appointment(user_id):
    user: User = system.clear_appointment(user_id)
    return {f"Current user:{user_id}" : user.current_appointment}
@app.patch("/new_cage_price",tags= ['Manager'])
def new_cage_price(cagesize: str, new_price):
    get = system.new_cage_price(size=cagesize, new_price=new_price)
    return {"status" : get}
@app.patch("/new_medicine_price",tags=["Manager"])
def new_medicine_price(med_id: str, new_price):
    get = system.new_medicine_price(medicine_id= med_id, new_price= new_price)
    return {"status" : get}

if __name__ == "__main__":
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)