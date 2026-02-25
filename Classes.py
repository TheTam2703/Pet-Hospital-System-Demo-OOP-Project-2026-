from enum import Enum
from datetime import datetime
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
    
    @property
    def id(self):
        return self.__id
    
    @property
    def species(self):
        return self.__species

class Userr:
    def __init__(self, user_id: str, name: str):
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

class Employee(Userr):
    def __init__(self, employee_id: str, user_id: str, name: str, salary: float):
        super().__init__(user_id, name)
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
    def __init__(self, employee_id: str, user_id: str, name: str, salary: float, expertise: Species):
        super().__init__(employee_id, user_id, name, salary)
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
    
#=========CONTROLLER CLASS==========#

class PetHospital:
    def __init__(self, name):
        self.__name = name
        self.__user_list = []
        self.__employee_list = []
        self.__appointment_list = []

    def add_user(self, user: Userr):
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
    
    def check_user_eligibility(self, user: Userr):
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
