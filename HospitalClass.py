from fastapi import HTTPException
from enum import Enum
from datetime import datetime
from typing import Union
from abc import ABC, abstractmethod

#=========ENUM CLASS==========#

class Species(Enum):
    DOG = 0
    CAT = 1
    EXOTIC = 2

class Sex(Enum):
    MALE = 0
    FEMALE = 1

class AppointmentStatus(Enum):
    SCHEDULED = 0
    CHECKED_IN = 1
    COMPLETED = 2
    CANCELLED = 3
    NO_SHOW = 4

class CageSize(Enum):
## น้ำหนักไม่เกิน value 
    S = 5.0
    M = 15.0
    L = 30.0

class Expertise(Enum):
    CAT = 0
    DOG = 1
    EXOTIC = 2

class CageStatus(Enum):
    AVAILABLE = 0
    OCCUPIED = 1
    RESERVED = 2

class WardType(Enum):
    Standard = 0
    ICU = 1
    Isotaion = 2

class PatmentStatus(Enum):
    UNPAID = 0
    PAID = 1

#=========ENTITY CLASS==========#

class ServiceItem(ABC):
    def __init__(self, service_type):
        super().__init__()
        self.__service_type = service_type

    @abstractmethod
    def calculate_total_price():
        pass

class Cage(ServiceItem):
    def __init__(self, service_type, cage_no: str, cage_status: str, pet_id: str):
        super().__init__(service_type)
        self.__cage_no = cage_no
        self.__cage_status = cage_status
        self.__pet_id = pet_id

class PetProfile:
    def __init__(self, pet_id: str, name: str, species: Species, weight: float, sex: Sex, birthdate: str):
        self.__id = pet_id
        self.__name = name
        self.__species = species
        self.__weight = weight
        self.__sex = sex
        self.__birthdate = birthdate
        self.__medical_records = []

    def add_medical_record(self,medical_record: object):
        self.__medical_records.append(medical_record)

    def get_information(self) -> float:
        return self.__weight

    @property
    def id(self):
        return self.__id
    
    @property
    def species(self):
        return self.__species

class User:
    def __init__(self, user_id: str, name: str, phone_num: str):
        self.__user_id = user_id
        self.__name = name
        self.__no_show_left = 3
        self.__pet_list = []

    @property
    def user_id(self):
        return self.__user_id
    
    @property
    def no_show_left(self):
        return self.__no_show_left

    def add_petprofile(self, pet_id: str, name: str, species: Species, weight: float, sex: Sex, birthdate: str):
        self.__pet_list.append(PetProfile(pet_id, name, species, weight, sex, birthdate))

    def get_pet_by_id(self, pet_id: str):
        for pet in self.__pet_list:
            if pet.id == pet_id:
                return pet
        return None
    
class Employee(User):
    def __init__(self, employee_id: str, user_id: str, name: str, salary: float, phone_num: str):
        super().__init__(user_id, name , phone_num)
        self.__employee_id = employee_id
        self.__salary = salary
    
    @property
    def employee_id(self):
        return self.__employee_id

class Appointment:
    def __init__(self, appointment_id: str, user_id: str, vet_id: str, petprofile: PetProfile, chosen_date: datetime, status):
        self.appointment_id = appointment_id
        self.appointment_status = status
        self.date = chosen_date
        self.vet_id = vet_id
        self.user_id = user_id
        self.petprofile = petprofile

class TimeSlot:
    def __init__(self, date : datetime):
        self.date = date
        self.available = True
        self.__duration = 1 # hours

class Vet(Employee):
    def __init__(self, employee_id: str, user_id: str, name: str, salary: float, expertise: Species, phone_num: str):
        super().__init__(employee_id, user_id, name, salary, phone_num)
        self.__expertise = expertise
        self.__current_appointment = None
        self.__timeslot_list = []
    
    def add_timeslot(self, datetime : datetime):
        self.__timeslot_list.append(TimeSlot(datetime))

    def is_compatible_with(self, species: Species):
        return species == self.__expertise

    def is_available_at(self, chosen_time : datetime):
        for slot in self.__timeslot_list:
            if slot.date == chosen_time and slot.available:
                return True
        return False

class Prescription:
    def __init__(self):
        pass

class MedicalRecord :
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

#=========CONTROLLER CLASS==========#

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
                medical: MedicalRecord = medical_record
                break
        if(isinstance(Pet,PetProfile)):
            for ward in self.__ward_list:
                cage_no, ward_no =  ward.try_admit(Pet, weight)
                if(cage_no != None and ward_no != None):
                    
                    admit_record = AdmitRecord(Pet.id, ward, cage_no, date_admit)
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
                Medical_record: MedicalRecord = medical
                Pet: PetProfile = medical.get_pet()
                break
        
        for ward in self.__ward_list:
            if(ward.check_out(Pet)): ## check out แล้ว
                break
        else:
            return f"somethings went wrong"
        
        cage_id = Medical_record.check_out_at(date_leave)
        return f"{Pet.id} checkout from {cage_id} at {datetime.strftime(date_leave, "%d/%m/%Y %H:%M")}"


    def valid_date(self, date_time: str):
        try:
            date_time = datetime.strptime(date_time, "%d/%m/%Y %H:%M")
            return date_time
        except :
            raise HTTPException(status_code= 400, detail= "validate datetime format. dd/mm/yy hr:min")

    def make_medical_record(self, medical_id: str, date: str, pet: object, user: object, vet: object, symtomps: str, diagnosis: str,prescription: object, admit: bool):
        medical_rec = MedicalRecord(medical_id,date,pet,user,vet,symtomps,diagnosis,prescription,admit)
        self.__medical_record_list.append(medical_rec)
        pet.add_medical_record(medical_rec)

    def add_ward(self,ward: object):
        self.__ward_list.append(ward)
    
    def get_med_list(self):
        return self.__medical_record_list

    def add_user(self, user: User):
        self.__user_list.append(user)
    
    def add_employee(self, employee: Employee):
        self.__employee_list.append(employee)

    def search_user_by_id(self, user_id: str):
        for user in self.__user_list:
            if user_id == user.user_id:
                return user
        return None
    
    def search_employee_by_id(self, employee_id: str):
        for employee in self.__employee_list:
            if employee_id == employee.employee_id:
                return employee
        return None
    
    def check_user_eligibility(self, user: User):
        if user.no_show_left == 0:
            return False
        else:
            # มี appointment ที่ยังไม่เสร็จ
            for appt in self.__appointment_list:
                if appt.user_id == user.user_id and appt.appointment_status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN]:
                    return False
        return True
    
    def book_appointment(self, user_id: str, vet_id: str, pet_id: str, chosen_date: datetime):
        
        user = self.search_user_by_id(user_id)
        vet = self.search_employee_by_id(vet_id)
        petprofile = user.get_pet_by_id(pet_id)

        if not vet.is_compatible_with(petprofile.species):
            return "แพทย์คนนี้ไม่สามารถรักษาสัตว์ประเภทนี้ได้"
        
        if not self.check_user_eligibility(user):
            return "ไม่สามารถจองได้ ติดเงื่อนไข"
        
        if not vet.is_available_at(chosen_date):
            return "เวลานี้ถูกจองแล้ว"
        
        import uuid
        appointment_id = uuid.uuid4()

        new_appointment = Appointment(appointment_id, user_id, vet_id, petprofile, chosen_date, status=AppointmentStatus.SCHEDULED)
        self.__appointment_list.append(new_appointment)

        return new_appointment





