from class_keep import *
from fastapi import FastAPI
"////////////////////////////////////////////////"
hospital =  create_test()
app = FastAPI()

@app.get("/")
def read_root():
    return {"welcome to" : "Pethospital"}

@app.post("/admit", tags=["admit"])
def admit(MedID: str, date_in: str)-> dict:

    status = hospital.admit(MedID, date_in)
    return {"status" : status}

@app.get("/admit",tags=["admit"])
def get_admit_record(MedID):
    for med in hospital.get_med_list():
        if(med.get_medical_id() == MedID):
            if(isinstance(med.get_admit_record(),AdmitRecord)):
                cage_id = med.get_admit_record().get_cage().no
                pet_id = med.get_admit_record().get_pet()
                print(f"{type(cage_id)} : {type(pet_id)}")
                print(f"{pet_id} : {cage_id}")
                return {pet_id : cage_id}
            return {MedID : med.get_admit_record()}
    return {MedID : "can't find this ID"}

if __name__ == "__main__":
    uvicorn.run("admit:app",host="127.0.0.1",port=8000,reload=True)
