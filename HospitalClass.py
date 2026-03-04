from fastapi import HTTPException
from enum import Enum
from datetime import datetime
from typing import Union
from abc import ABC, abstractmethod
from typing import Union
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
    def get_price(self):
        if(self == CageSize.S):
            return 300
        elif(self == CageSize.M):
            return 450
        elif(self == CageSize.L):
            return 600
        

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

class PaymentMethod(Enum):
    Cash = 0

#=========ENTITY CLASS==========#
class Payment:
    def __init__(self):
        import uuid
        self.__id = str(uuid.uuid4())
        self.__total = 0
        self.__paid_date: datetime = None
        self.__payment_method: PaymentMethod = None
        self.__recept_list: list[ServiceItem] = []

    def add_recept_list(self, service):
        self.__recept_list.append(service)
    def calculate_total(self):
        sum = 0
        for recep in self.__recept_list:
            sum += recep.calculate_total_price()
            print(f"sum = {sum}")
        else:
            self.__total = sum
            return self.__total

class ServiceItem(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def calculate_total_price(self):
        pass

class CageService(ServiceItem):
    def __init__(self, ward, cage, Stay_duration: int):
        super().__init__()
        self.__ward: Ward = ward
        self.__cage: Cage = cage
        self.__stay_duration = Stay_duration

    def calculate_total_price(self):
        total = self.__cage.size.get_price() * self.__stay_duration

        return total

class MedicalService(ServiceItem):
    def __init__(self, examination_fee: float, prescription: list):
        self.__examination_fee = examination_fee
        self.__prescription_list :list[Prescription] = []

    def calculate_total_price(self):
        sum = self.__examination_fee
        for prescription in self.__prescription_list:
            sum += prescription.calculate_price()

        return sum


class PetProfile:
    def __init__(self, pet_id: str, name: str, species: Species, weight: float, sex: Sex, birthdate: str, allergy: list):
        self.__id = pet_id
        self.__name = name
        self.__species = species
        self.__weight = weight
        self.__sex = sex
        self.__birthdate = birthdate
        self.__medical_records = []
        self.__allergy_list: list[Medicine] = allergy

    def add_medical_record(self,medical_record: object):
        self.__medical_records.append(medical_record)

    def get_information(self) -> float:
        return self.__weight

    def is_allergy(self, medicine):
        for allergy in self.__allergy_list:
            if(allergy == medicine):
                return True
            
        return False

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
        self.__current_appointment: Union[Appointment,None] = None 
        self.__pet_list = []

    @property
    def user_id(self):
        return self.__user_id
    
    @property
    def pet_list(self):         return self.__pet_list

    @property
    def no_show_left(self):
        return self.__no_show_left

    @property
    def current_appointment(self):
        return self.__current_appointment
    @current_appointment.setter
    def current_appointment(self, current_appointment):
        if(isinstance(current_appointment,Appointment) or current_appointment == None):
            self.__current_appointment :Appointment = current_appointment
        else:
            raise TypeError(f"{current_appointment} is type {type(current_appointment)} not Appointment")

    def add_petprofile(self, pet_id: str, name: str, species: Species, weight: float, sex: Sex, birthdate: str, allergy: list):
        self.__pet_list.append(PetProfile(pet_id, name, species, weight, sex, birthdate, allergy))

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
        self.__appointment_id = appointment_id
        self.__appointment_status = status
        self.__date = chosen_date
        self.__vet_id = vet_id
        self.__user_id = user_id
        self.__petprofile = petprofile
        self.__payment: Payment = Payment()
        
    def make_payment(self, examination_fee: float, prescription):
        service = MedicalService(examination_fee, prescription)
        self.__payment.add_recept_list(service)

    def cage_service(self, days: int, ward, cage):
        service = CageService(ward, cage, days)
        self.__payment.add_recept_list(service)

    @property
    def user_id(self):           return self.__user_id
    @property
    def appointment_status(self):return self.__appointment_status
    @property
    def appointment_id(self):   return self.__appointment_id
    @property
    def date(self):             return self.__date
    @property
    def vet_id(self):           return self.__vet_id
    @property
    def pet(self):              return self.__petprofile
    @property
    def payment(self):          return self.__payment

class TimeSlot:
    def __init__(self, date : datetime):
        self.__date = date
        self.__available = True
        self.__duration = 1 # hours

    @property
    def date(self):
        return self.__date
    @property
    def available(self):
        return self.__available
    

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
    def __init__(self, medicine, instruction:str, quantity: int):
        self.__medicine: Medicine = medicine
        self.__instruction = instruction
        self.__quantity = quantity
        
    def calculate_price(self):
        unit_price = self.__medicine.unit_price
        total = unit_price * self.__quantity
        return total

class Medicine:
    def __init__(self, medicine_id: str, name: str, unit_price: float):
        self.__id = medicine_id
        self.__name = name
        self.__unit_price = unit_price

    @property
    def unit_price(self):       return self.__unit_price
    @property
    def id(self):               return self.__id

class MedicalRecord :
    def __init__(self,medical_id:str, date: str, pet: object, user :object, vet: object, symtomps: str, diagnosis: str, prescription: list[Prescription], admit: bool,
        appointment: object)  :
        self.__id = medical_id
        self.__appointment: Appointment = appointment 
        self.__datetime = date
        self.__pet = pet
        self.__user = user
        self.__vet = vet
        self.__symtomps = symtomps
        self.__diagnosis = diagnosis
        self.__perscription: list[Prescription] = prescription 
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
        
    def check_out_at(self, date_leave: datetime) -> int:
        if(isinstance(self.__admited_record,AdmitRecord)):
            return self.__admited_record.check_out_at(date_leave)

    def get_pet(self):
        return self.__pet
    def get_admit_record(self):
        return self.__admited_record
    def get_appointment(self): return self.__appointment

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
    def no(self):           return self.__cage_no
    @property
    def size(self):         return self.__cage_size
    def __str__(self):
     return self.__cage_no

class AdmitRecord():
    def __init__(self, pet_id: str, ward: object, cage: object, date_of_admit: datetime):
        self.__pet = pet_id
        self.__ward = ward
        self.__cage = cage
        self.__date_of_admit = date_of_admit
        self.__date_of_leave = None

    def get_pet(self):
        return self.__pet
    def get_cage(self):
        return self.__cage
    def get_ward(self):return self.__ward

    def check_out_at(self, date_leave: datetime) -> int:
            format = "%d/%m/%Y %H:%M"
            diff: datetime =date_leave - self.__date_of_admit 
            return diff.days

#=========CONTROLLER CLASS==========#

class PetHospital :
    def __init__(self, name):
        self.__name = name
        self.__user_list :list[User]= []
        self.__employee_list :list[Employee]= []
        self.__admitted_list :list[AdmitRecord]= []
        self.__ward_list :list[Ward]= []
        self.__medical_record_list : list[MedicalRecord]= []
        self.__appointment_list : list[Appointment]= []
        self.__cage_booking_list = []
        self.__medicine_list : list[Medicine]= []

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
    
        total_days = Medical_record.check_out_at(date_leave)
        admit_record: AdmitRecord = Medical_record.get_admit_record()
        appointment: Appointment = Medical_record.get_appointment()
        cage: Cage = admit_record.get_cage()
        appointment.cage_service(total_days, admit_record.get_ward(),cage)
        
        return f"{Pet.id} checkout from {cage.no} at {datetime.strftime(date_leave, "%d/%m/%Y %H:%M")}"


    def valid_date(self, date_time: str):
        try:
            date_time = datetime.strptime(date_time, "%d/%m/%Y %H:%M")
            return date_time
        except :
            raise HTTPException(status_code= 400, detail= "validate datetime format. dd/mm/yy hr:min")

    def make_medical_record(self, medical_id: str, date: str, symtomps: str, diagnosis: str,prescription: object, admit: bool
        ,examination_fee: float, appointment: object):
        if(isinstance(appointment,Appointment)):
            user: User = self.search_user_by_id(appointment.user_id)
            vet: Vet = self.search_vet_from_id(appointment.vet_id)
            medical_rec = MedicalRecord(medical_id,date,appointment.pet,user,vet,symtomps,diagnosis,prescription,admit, appointment=appointment)
            self.__medical_record_list.append(medical_rec)
            appointment.make_payment(examination_fee, prescription)
            appointment.pet.add_medical_record(medical_rec)
            
    def write_presctiption(self, medicine_id: str, amount: int, instruction: str, pet: str):
        medicine = None
        for med in self.__medicine_list:
            if (med.id == medicine_id):
                medicine: Medicine = med
                break
        petprofile : PetProfile = self.search_pet_by_id(pet)
        if(not petprofile.is_allergy(medicine)):
            return Prescription(medicine,instruction,amount)
        else:
            return "drug allergy"

    def add_ward(self,ward: object):
        self.__ward_list.append(ward)
    
    def add_medicine(self, medicine:object):
        self.__medicine_list.append(medicine)

    def get_med_list(self):
        return self.__medical_record_list

    def add_user(self, user: User):
        self.__user_list.append(user)
    
    def add_employee(self, employee: Employee):
        self.__employee_list.append(employee)

    def search_appointment_by_id(self, a_id):
        for appointment in self.__appointment_list:
            if(appointment.appointment_id == a_id):
                return appointment
        return None

    def search_vet_from_id(self, id):
        for employee in self.__employee_list:
            if(isinstance(employee,Vet) and employee.employee_id):
                return employee

    def search_user_by_id(self, user_id: str):
        for user in self.__user_list:
            if user_id == user.user_id:
                return user
        return None
    
    def search_pet_by_id(self, pet_id):
        for user in self.__user_list:
            for pet in user.pet_list:
                if(pet.id == pet_id):
                    return pet


    def search_employee_by_id(self, employee_id: str):
        for employee in self.__employee_list:
            if employee_id == employee.employee_id:
                return employee
        return None
    
    def calculate_payment(self, user_id):
        user = self.search_user_by_id(user_id)
        if(user == None):
            return f"Can't find {user_id}"
        try:
            payment: Payment = user.current_appointment.payment
            total = payment.calculate_total()
            return total

        except Exception:
            return 0        

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
        
        user: User = self.search_user_by_id(user_id)
        vet = self.search_employee_by_id(vet_id)
        petprofile = user.get_pet_by_id(pet_id)

        if not vet.is_compatible_with(petprofile.species):
            return "แพทย์คนนี้ไม่สามารถรักษาสัตว์ประเภทนี้ได้"
        
        if not self.check_user_eligibility(user):
            return "ไม่สามารถจองได้ ติดเงื่อนไข"
        
        if not vet.is_available_at(chosen_date):
            return "เวลานี้ถูกจองแล้ว"
        
        import uuid
        appointment_id = str(uuid.uuid4())
        new_appointment: Appointment = Appointment(appointment_id, user_id, vet_id, petprofile, chosen_date, status=AppointmentStatus.SCHEDULED)
        user.current_appointment = new_appointment
        self.__appointment_list.append(new_appointment)

        return new_appointment

    def add_appointment(self, appointment: Appointment):
        self.__appointment_list.append(appointment)

    def clear_appointment(self, user_id: str):
        user: User = self.search_user_by_id(user_id)
        user.current_appointment = None
        return user


