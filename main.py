from fastapi import FastAPI
import uvicorn
from Classes import *


def create_instances():
    system = PetHospital("Smart Pet Clinic")

    user = Userr("0", "Tam")
    user.add_petprofile("0", "aidum", Species.DOG, 12.00, Sex.MALE, datetime(2017, 4, 13))

    vet1 = Vet("111", "1", "Dr. Somchai", 35000.00, Species.DOG)
    vet2 = Vet("112", "2", "Dr. Jaibun", 35000.00, Species.CAT)

    vet1.add_timeslot((datetime(2026, 2, 23, 11, 0)))
    vet1.add_timeslot((datetime(2026, 2, 23, 12, 0)))

    system.add_user(user)
    system.add_employee(vet1)
    system.add_employee(vet2)

    return system

system = create_instances()
    
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "Pet Hospital"}

@app.post("/book_appointment")
def book_appointment(user_id: str, vet_id: str, pet_id: str, chosen_date: str):

    fmt = "%Y-%m-%d %H:%M"
    try:
        formated_desired_date = datetime.strptime(chosen_date, fmt)
        result = system.book_appointment(user_id, vet_id, pet_id, formated_desired_date)
        if isinstance(result, str):
            return {"success": False, "message": result}
        
        return {
            "success" : True,
            "appointment_data" : {
                "appointment_id": result.appointment_id,
                "appointment_status": result.appointment_status,
                "date": result.date,
                "vet_id": result.vet_id,
                "user_id": result.user_id,
            }
        }
    except Exception as e:
        return {"success": False, "message": f"Sum ting wong: {str(e)}"}
    
if __name__ == "__main__":
    uvicorn.run("main:app",host="127.0.0.1",port=8000,reload=True)