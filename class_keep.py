from fastapi import HTTPException
from enum import Enum
from datetime import datetime
import uvicorn
from typing import Union
"////////////////////////////////////////////////"

class Sex(Enum):
    Male = "Male"
    Female = "Female"

"////////////////////////////////////////////////"

class CageSize(Enum):
    S = 5.0
    M = 15.0
    L = 30.0
    XL = 30.0

"////////////////////////////////////////////////"

class Expertise(Enum):
    CAT = "CAT"
    DOG = "DOG"
    EXOTIC = "EXOTIC"

"////////////////////////////////////////////////"

class CageStatus(Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"

"////////////////////////////////////////////////"

class WardType(Enum):
    Standard = "Standard"
    ICU = "ICU"
    Isotaion = "Isotation"

"////////////////////////////////////////////////"
class PetHospital :
    def __init__(self, name):
        self.__name = name
        self.__user_list = []
        self.__employee_list = []
        self.__admitted_list = []
        self.__ward_list = []
        self.__medical_record_list = []
        self.__appointment_list = []
        self.__cage_booking_list = []

    def admit(self,MedicalRecordID,date_admit):
        Pet = None
        weight = None
        medical = None
        date_admit = self.valid_date(date_admit)
        for medical_record in self.__medical_record_list:
            if(MedicalRecordID == medical_record.get_medical_id()):
                Pet, weight = medical_record.get_approval()
                medical = medical_record
                break
        if(isinstance(Pet,PetProfile)):
            for ward in self.__ward_list:
                cage_no, ward_no =  ward.try_admit(Pet, weight)
                if(cage_no != None and ward_no != None):
                    
                    admit_record = AdmitRecord(Pet.get_id(), ward, cage_no, date_admit)
                    medical.write_admit_record(admit_record)
                    return f"admit success at cage {cage_no} ward {ward_no}"
    
            else:
                return f"no cage match available"
            
        elif(Pet == None): ## ไม่ได้มีการรีเทิร์น PetProfile = ไม่อนุมัติ 
            return "Not approved"
        
        elif(isinstance(Pet,AdmitRecord)):
            return "already admited"

    def check_out(self, Med_id: str, date_leave: str):
        date_leave: datetime = self.valid_date(date_leave)
        
        for medical in self.__medical_record_list:
            if(medical.get_medical_id() == Med_id):
                MedicalRecord: medical_record = medical
                Pet: PetProfile = medical.get_pet()
                break
        
        for ward in self.__ward_list:
            if(ward.check_out(Pet)): ## check out แล้ว
                break
        else:
            return f"somethings went wrong"
        
        cage_id = MedicalRecord.check_out_at(date_leave)
        return f"{Pet.get_id()} checkout from {cage_id} at {datetime.strftime(date_leave, "%d/%m/%Y %H:%M")}"


    def valid_date(self, date_time: str):
        try:
            date_time = datetime.strptime(date_time, "%d/%m/%Y %H:%M")
            return date_time
        except :
            raise HTTPException(status_code= 400, detail= "validate datetime format. dd/mm/yy hr:min")

    def make_medical_record(self, medical_id: str, date: str, pet: object, user: object, vet: object, symtomps: str, diagnosis: str,prescription: object, admit: bool):
        medical_rec = medical_record(medical_id,date,pet,user,vet,symtomps,diagnosis,prescription,admit)
        self.__medical_record_list.append(medical_rec)
        pet.add_medical_record(medical_rec)

    def add_ward(self,ward: object):
        self.__ward_list.append(ward)
    
    def get_med_list(self):
        return self.__medical_record_list

"////////////////////////////////////////////////"

class AdmitRecord():
    def __init__(self, pet_id: str, ward: object, cage: object, date_of_admit: str):
        self.__pet = pet_id
        self.__ward = ward
        self.__cage = cage
        self.__date_of_admit = date_of_admit
        self.__date_of_leave = None

    def get_pet(self):
        return self.__pet
    def get_cage(self):
        return self.__cage

    def check_out_at(self, date_leave: str) -> str:
        self.__date_of_leave = date_leave
        return self.__cage.no
"////////////////////////////////////////////////"

class Prescription:
    pass
"////////////////////////////////////////////////"

class Employee():
    def __init__(self, employee_id: str, hospital: str, salary: float):
        self.__employee_id = employee_id
        self.__hospital = hospital
        self.__salary = salary


class Vet(Employee):
    def __init__(self,employee_id: str, hospital: str, salary: float,vet_id: str, expertise: Expertise):
        self.__vet_id = vet_id
        self.__expertise = expertise
        super.__init__(employee_id, hospital, salary)

"////////////////////////////////////////////////"

class medical_record :
    def __init__(self,medical_id:str, date: str, pet: object, user :object, vet: object, symtomps: str, diagnosis: str, prescription: Prescription, admit: bool)  :
        self.__id = medical_id
        self.__datetime = date
        self.__pet = pet
        self.__user = user
        self.__vet = vet
        self.__symtomps = symtomps
        self.__diagnosis = diagnosis
        self.__perscription = prescription
        self.__admited_record = admit

    def get_medical_id(self) -> str:
        return self.__id

    def get_approval(self) -> Union[None,object]:
        "return Pet and weight if approved return None if not aprroved"
        if(self.__admited_record == True): 
            return self.__pet, self.__pet.get_information()
        elif(isinstance(self.__admited_record, AdmitRecord)):
            return self.__admited_record, None
        return None, None

    def write_admit_record(self,admit_record: object):
        self.__admited_record = admit_record
        
    def check_out_at(self, date_leave: datetime) -> str:
        if(isinstance(self.__admited_record,AdmitRecord)):
            return self.__admited_record.check_out_at(date_leave)

    def get_pet(self):
        return self.__pet
    def get_admit_record(self):
        return self.__admited_record

"////////////////////////////////////////////////"

class PetProfile :
    def __init__(self, pet_id: str, name: str, species: str, weight: float, sex: Sex, birthdate: str):
        self.__pet_id = pet_id
        self.__name = name
        self.__species = species
        self.__weight = weight
        self.__sex = sex
        self.__birthdate = birthdate
        self.__medical_record_list = []

    def add_medical_record(self,medical_record: object):
        self.__medical_record_list.append(medical_record)

    def get_information(self) -> float:
        return self.__weight
    def get_id(self):
        return self.__pet_id

"////////////////////////////////////////////////"

class Ward :
    def __init__(self, ward_no: str, type: WardType, max_number_of_cage: int = 10):
        self.__ward_no = ward_no
        self.__type = type
        self.__cage_list = []
        self.__max_number_of_cage = max_number_of_cage


    def try_admit(self, Pet:object, weight: float):
        for cage in self.__cage_list:
            admit_cage = cage.can_admit(Pet, weight)
            if(admit_cage != None):
                return admit_cage, self.__ward_no

        return None, None
    
    def check_out(self, Pet: PetProfile):
        for cage in self.__cage_list: 
            if(cage.check_out(Pet)):
                return 1

    def add_cage(self, cage: object):
        self.__cage_list.append(cage)

    def get_cage(self) -> list:
        "return cage_list in ward"
        return self.__cage_list
    
    def __str__(self):
        return self.__ward_no

"////////////////////////////////////////////////"

class Cage :
    def __init__(self, cage_no: str, cage_size: CageSize, pet: object ,cage_status: CageStatus):
        self.__cage_no = cage_no
        self.__cage_size = cage_size
        self.__pet = pet
        self.__cage_status = cage_status

    def can_admit(self, Pet: object, weight: float) -> Union[str, None]:
        "ถ้ากรงว่างและน้ำหนักสัตว์ไม่เกิน return True"
        if(self.__cage_status == CageStatus.AVAILABLE and weight < self.__cage_size.value):
            self.update_status(Pet)
            return self
        
        return None
    
    def update_status(self, Pet: object):
        "รับ pet มาและupdate pet และ status ของกรงเป็น occupied"
        self.__pet = Pet
        self.__cage_status = CageStatus.OCCUPIED

    def check_out(self, Pet:object):
        if(Pet == self.__pet):
            self.pet_check_out()
            return 1
        return 0

    def pet_check_out(self):
        self.__pet = None
        self.__cage_status = CageStatus.AVAILABLE

    @property
    def cage_status(self): return self.__cage_status
    @property
    def no(self):
        return self.__cage_no
    def __str__(self):
     return self.__cage_no
"////////////////////////////////////////////////"

class User :
    def __init__(self ,user_id: str,  name: str, phone_num: str):
        self.__user_id = user_id
        self.__name = name
        self.__phone_no= phone_num
        self.__pet = []  
        self.__no_show_left = 3



