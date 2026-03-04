from HospitalClass import *
import uvicorn
from fastapi import FastAPI

def create_test():
    system = PetHospital("Test Pet Hospital")

    # ====== USER + PET ======
    user = User("U001", "Tam", "0999999999")
    user.add_petprofile(
        pet_id="P001",
        name="AIDUM",
        species=Species.DOG,
        weight=12.0,
        sex=Sex.MALE,
        birthdate="13/04/2017"
    )

    system.add_user(user)

    # ====== VET ======
    vet = Vet(
        employee_id="V001",
        user_id="EMP001",
        name="Dr. Somchai",
        salary=35000.0,
        expertise=Species.DOG,
        phone_num= "1234"
    )

    vet.add_timeslot(datetime(2026, 3, 10, 10, 0))
    vet.add_timeslot(datetime(2026, 3, 10, 11, 0))
    system.add_employee(vet)

    # ====== WARD + CAGES ======
    ward = Ward("W01", WardType.Standard)

    cage1 = Cage("C1", CageSize.S, None, CageStatus.AVAILABLE)
    cage2 = Cage("C2", CageSize.M, None, CageStatus.AVAILABLE)

    ward.add_cage(cage1)
    ward.add_cage(cage2)

    system.add_ward(ward)

    # ====== MEDICAL RECORD (approved for admit) ======
    pet = user.get_pet_by_id("P001")

    system.make_medical_record(
        medical_id="M001",
        date="10/03/2026 10:00",
        pet=pet,
        user=user,
        vet=vet,
        symtomps="fever",
        diagnosis="infection",
        prescription=Prescription(),
        admit=True  # อนุมัติให้ admit ได้
    )

    return system

system = create_test()
    
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "Pet Hospital"}

@app.post("/book_appointment")
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
    
@app.get("/admit",tags=["admit"])
def get_admit_record(MedID):
    for med in system.get_med_list():
        if(med.get_medical_id() == MedID):
            if(isinstance(med.get_admit_record(),AdmitRecord)):
                cage_id = med.get_admit_record().get_cage().no
                pet_id = med.get_admit_record().get_pet()
                return {pet_id : cage_id}
            return {MedID : med.get_admit_record()}
    return {MedID : "can't find this ID"}

@app.post("/admit", tags=["admit"])
def admit(MedID: str, date_in: str)-> dict:

    status = system.admit(MedID, date_in)
    return {"status" : status}

@app.post("/checkout", tags=['checkout'])
def check_out(Medical_recordID : str, date_leave: str):
    status = system.check_out(Medical_recordID, date_leave)
    return {"status" : status}
if __name__ == "__main__":
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)