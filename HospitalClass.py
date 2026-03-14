from fastapi import HTTPException
from enum import Enum
from datetime import datetime, timedelta
from typing import Union
from abc import ABC, abstractmethod
import uuid
import math

#=========ENUM CLASS==========#

class Species(Enum):
    """Species of a pet. Used to match a pet to a compatible vet."""
    DOG = 0
    CAT = 1
    EXOTIC = 2

class Sex(Enum):
    """Biological sex of a pet."""
    MALE = 0
    FEMALE = 1

class AppointmentStatus(Enum):
    """Lifecycle states an appointment can be in."""
    SCHEDULED = 0    # Booked but patient has not arrived yet
    CHECKED_IN = 1   # Patient has arrived at the clinic
    COMPLETED = 2    # Appointment finished and pet has been discharged
    CANCELLED = 3    # Appointment was cancelled before it took place
    NO_SHOW = 4      # Patient did not arrive within the allowed window

class BookingStatus(Enum):
    """Lifecycle states a standalone cage booking can be in."""
    CONFIRMED = 0    # Reservation is active; pet has not yet arrived
    CHECKED_IN = 1   # Pet has been handed over and is now in the cage
    COMPLETED = 2    # Pet has been collected and cage has been released
    CANCELLED = 3    # Booking was cancelled before check-in

class CageSize(Enum):
    """Cage size categories. Value = maximum pet weight (kg) the cage can hold."""
    S = 5.0   # Small  — pets up to 5 kg
    M = 15.0  # Medium — pets up to 15 kg
    L = 30.0  # Large  — pets up to 30 kg

class CageStatus(Enum):
    """Occupancy state of a cage."""
    AVAILABLE = 0  # Empty and ready to admit a pet
    OCCUPIED = 1   # Currently housing a pet
    RESERVED = 2   # Held for a future admission

class WardType(Enum):
    """Type of ward, which determines the level of care provided."""
    STANDARD = 0   # General ward for routine stays
    ICU = 1        # Intensive care for critical patients
    ISOLATION = 2  # Quarantine ward for infectious cases

class PaymentStatus(Enum):
    """Whether the bill for an appointment has been settled."""
    UNPAID = 0
    PAID = 1

class PaymentMethod(Enum):
    """Accepted payment methods."""
    CASH = 0
    QR = 1

class Member(Enum):
    """Discount"""
    REGULAR = 0
    STAFF = 1

#=========ENTITY CLASS==========#
class Payment:
    """
    Tracks the financial transaction for a single appointment.
    Holds a list of ServiceItems (MedicalService, CageService) and records
    payment method and date once settled.
    """
    def __init__(self):
        """Initialise a new Payment with a unique ID and UNPAID status."""
        self.__id = str(uuid.uuid4())
        self.__total = 0
        self.__paid_date: datetime = None
        self.__payment_method: PaymentMethod = None
        self.__status: PaymentStatus = PaymentStatus.UNPAID
        self.__receipt_list: list[ServiceItem] = []
    
    @property
    def status(self):
        """Return the current payment status (UNPAID or PAID)."""
        return self.__status
    @property
    def id(self):
        """Return the unique ID of this payment record."""
        return self.__id
    @property
    def total(self):
        """Return total of payment"""
        return self.__total

    def add_receipt_list(self, service):
        """Append a ServiceItem (MedicalService or CageService) to the bill."""
        self.__receipt_list.append(service)

    def get_receipt(self) -> list:
        """
        Return an itemised breakdown of the bill as a list of dicts,
        each containing the service type and its amount.
        """
        receipt = []
        for recep in self.__receipt_list:
            receipt.append(recep.get_info())
        return receipt

    def calculate_total(self, keep=False):
        """
        Sum the cost of every ServiceItem on the bill BEFORE discount and cache the result.
        Returns the total amount due in baht.
        """
        sum = 0
        for recep in self.__receipt_list:
            sum += recep.calculate_total_price()
        if keep:
            self.__total = sum
        return sum
    
    def pay(self, method: PaymentMethod):
        """
        Mark the payment as PAID using the given method and record the timestamp.
        Returns an error string if payment has already been completed.
        """
        if self.__status == PaymentStatus.PAID:
            return "Payment already completed"
        self.__payment_method = method
        self.__paid_date = datetime.now()
        self.__status = PaymentStatus.PAID

        return f"Payment of {self.__total} baht completed via {method.name}"

    def apply_discount(self, discount):
        self.__total *= discount
        return self.__total


class ServiceItem(ABC):
    """
    Abstract base class for billable services.
    """
    def __init__(self):
        super().__init__()

    @abstractmethod
    def calculate_total_price(self):
        pass

    @abstractmethod
    def get_info(self):
        pass


class CageService(ServiceItem):
    """
    Billable line item for a pet's cage stay.
    Cost = cage daily rate x number of days stayed.
    """
    CAGE_PRICES_PER_DAY: dict = {"S": 300, "M": 450, "L": 600}
    CAGE_PRICES_PER_HOUR: dict = {"S": 20, "M": 50, "L": 90}
    
    def __init__(self, ward, cage, Stay_duration: int):
        """
        Initialise with the ward, cage used, and the total number of days stayed.
        stay_duration is calculated by AdmitRecord.check_out_at() using ceiling division.
        """
        super().__init__()
        self.__ward: Ward = ward
        self.__cage: Cage = cage
        self.__stay_duration = Stay_duration

    def calculate_total_price(self):
        total = self.CAGE_PRICES_PER_DAY[self.__cage.size.name] * self.__stay_duration + self.__ward.get_price()
        return total
    
    def get_info(self):
        return (f"Cage Fee:\n"
                f"Size: {self.__cage.size.name}\n"
                f"Cost: {CageService.CAGE_PRICES_PER_DAY[self.__cage.size.name]} per day."
                f"stayed for {self.__stay_duration} days.") 
    
    @staticmethod
    def get_price(self, cage_size: str):
        """Return the current daily rental price (baht) for this cage size."""
        try:
            size_enum = CageSize[cage_size]
        except:
            return "Invalid cage size."
        return self.CAGE_PRICES[size_enum.name]

    def new_price(self, cage_size: str, new_price: int):
        """Update the daily rental price for the given cage size in the global price table."""
        try:
            size_enum = CageSize[cage_size]
        except:
            return "Invalid cage size."
        if new_price <= 0:
            return "New price cannot be below 0."
        self.CAGE_PRICES_PER_DAY[size_enum.name] = new_price


class MedicalService(ServiceItem):
    """
    Billable line item for an examination and any prescribed medicines.
    Cost = examination fee + sum of all prescription costs.
    """
    def __init__(self, examination_fee: float, prescription: list):
        """
        Initialise with the flat examination fee and the list of Prescription objects
        written during the consultation.
        """
        self.__examination_fee = examination_fee
        self.__prescription_list :list[Prescription] = prescription

    def calculate_total_price(self):
        sum = self.__examination_fee
        for prescription in self.__prescription_list:
            sum += prescription.calculate_price()
        return sum

    def get_info(self):
        medicine_lines = []
        for presc in self.__prescription_list:
            cost = presc.medicine.unit_price * presc.quantity
            medicine_lines.append((presc.medicine.name, presc.quantity, cost))
        res = "".join(f"  {med} x{qty} = {cost} baht\n" for med, qty, cost in medicine_lines)

        return f"Examination Fee: {self.__examination_fee} baht\nMedicines:\n{res}"


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

    def is_allergic(self, medicine):
        for allergy in self.__allergy_list:
            if(allergy == medicine):
                return True
        return False

    @property
    def id(self):
        return self.__id
    @property
    def name(self):
        return self.__name
    @property
    def weight(self):   
        return self.__weight
    @property
    def species(self):
        return self.__species
    @property
    def sex(self):
        return self.__sex
    @property
    def birthdate(self):
        return self.__birthdate

    def is_admit(self):
        """
        Check whether this pet is currently admitted to a cage.
        Returns the cage number string if admitted, or None if the pet is not currently staying.
        Looks for an AdmitRecord in the pet's history that has no checkout date yet.
        """
        for medical_record in self.__medical_records:
            admit_record: AdmitRecord = medical_record.get_admit_record()
            if(isinstance(admit_record,AdmitRecord) and admit_record.get_checkout_date() == None):
                return admit_record.get_cage().no
        return None


class User:

    DISCOUNT = {Member.REGULAR: 1, Member.STAFF: 0.8} 

    def __init__(self, user_id: str, name: str, phone_num: str, member: str = "REGULAR"):
        self.__user_id = user_id
        self.__name = name
        self.__phone = phone_num
        self.__no_show_left = 3
        self.__current_appointment: Union[Appointment,None] = None 
        self.__cage_booking_list = []
        self.__pet_list = []
        self.__membertier = Member[member.upper()]

    @property
    def membertier(self):
        return self.__membertier
    @property
    def user_id(self):
        return self.__user_id
    @property
    def name(self):
        return self.__name
    @property
    def pet_list(self):        
        return self.__pet_list
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

    def decrement_no_show(self):
        if self.__no_show_left > 0:
            self.__no_show_left -= 1

    def add_petprofile(self, pet_id: str, name: str, species: Species, weight: float, sex: Sex, birthdate: str, allergy: list):
        for pet in self.__pet_list:
            if pet.id == pet_id:
                raise ValueError(f"Pet ID '{pet_id}' already exists for this user")
        self.__pet_list.append(PetProfile(pet_id, name, species, weight, sex, birthdate, allergy))

    def get_pet_by_id(self, pet_id: str):
        for pet in self.__pet_list:
            if pet.id == pet_id:
                return pet
        return None
    
    def add_cage_booking(self, booking: object):
        self.__cage_booking_list.append(booking)

    def get_discount(self):
        return self.DISCOUNT[self.membertier]

class Employee(ABC):
    def __init__(self, employee_id: str,  name: str, salary: float, phone_num: str):
        super().__init__()
        self.__name = name
        self.__phone = phone_num
        self.__employee_id = employee_id
        self.__salary = salary
    
    @property
    def employee_id(self):
        return self.__employee_id
    @property
    def salary(self):       
        return self.__salary
    @property
    @abstractmethod
    def role(self) -> str:
        """Role string: 'Vet', 'HospitalStaff', or 'HospitalManager'. Enforced by each subclass."""
        pass


class Appointment:
    def __init__(self, appointment_id: str, user_id: str, vet_id: str, petprofile: PetProfile, chosen_date: datetime, status):
        self.__appointment_id = appointment_id
        self.__status = status
        self.__date_created = datetime.now()
        self.__scheduled_date = chosen_date
        self.__vet_id = vet_id
        self.__user_id = user_id
        self.__petprofile = petprofile
        self.__payment: Payment = Payment()

    @property
    def date_created(self):
        return self.__date_created
        
    def make_payment(self, examination_fee: float, prescription):
        service = MedicalService(examination_fee, prescription)
        self.__payment.add_receipt_list(service)

    def cage_service(self, days: int, ward, cage):
        service = CageService(ward, cage, days)
        self.__payment.add_receipt_list(service)
    
    def cancel(self):
        self.__status = AppointmentStatus.CANCELLED
    
    def completed(self):
        self.__status = AppointmentStatus.COMPLETED
    
    def mark_no_show(self):
        self.__status = AppointmentStatus.NO_SHOW
    
    def checked_in(self):
        self.__status = AppointmentStatus.CHECKED_IN

    @property
    def user_id(self):           
        return self.__user_id
    @property
    def status(self):
        return self.__status
    @property
    def appointment_id(self):   
        return self.__appointment_id
    @property
    def scheduled_date(self):             
        return self.__scheduled_date
    @property
    def vet_id(self):           
        return self.__vet_id
    @property
    def pet(self):              
        return self.__petprofile
    @property
    def payment(self):          
        return self.__payment
    

class CageBooking:
    def __init__(self,
                 user: User,
                 pet: PetProfile,
                 ward: object,
                 cage: object,
                 stay_date: datetime,
                 leave_date: datetime):

        self.__booking_id = str(uuid.uuid4())
        self.__booking_status = BookingStatus.CONFIRMED
        self.__booking_date = datetime.now()
        self.__user = user
        self.__pet_profile = pet
        self.__stay_date = stay_date
        self.__leave_date = leave_date
        self.__ward = ward
        self.__cage = cage
        self.__payment = Payment()

    @property
    def booking_id(self):
        return self.__booking_id
    @property
    def booking_date(self):
        return self.__booking_date
    @property
    def status(self):
        return self.__booking_status
    @property
    def pet(self):
        return self.__pet_profile
    @property
    def cage(self):
        return self.__cage
    @property
    def user(self):
        return self.__user
    @property
    def ward(self):
        return self.__ward
    @property
    def stay_date(self):
        return self.__stay_date
    @property
    def leave_date(self):
        return self.__leave_date

    def confirm_checkin(self):
        """Mark CHECKED_IN once the pet physically arrives."""
        if self.__booking_status != BookingStatus.CONFIRMED:
            return f"Cannot check in: booking status is {self.__booking_status.name}"
        self.__booking_status = BookingStatus.CHECKED_IN
        self.__cage.occupy(self.__pet_profile)
        return f"Booking {self.__booking_id}: {self.__pet_profile.name} checked in to cage {self.__cage.no}"

    def confirm_checkout(self):
        """Mark COMPLETED and free the cage once the pet is collected."""
        if self.__booking_status != BookingStatus.CHECKED_IN:
            return f"Cannot check out: booking status is {self.__booking_status.name}"
        self.__booking_status = BookingStatus.COMPLETED
        return (f"Booking {self.__booking_id}: {self.__pet_profile.name} "
                f"checked out from cage {self.__cage.no}")

    def cancel(self):
        self.__booking_status = BookingStatus.CANCELLED

    def is_active(self) -> bool:
        """Return True if the booking is CONFIRMED or CHECKED_IN."""
        return self.__booking_status in (BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN)

    def overlaps_with(self, start: datetime, end: datetime) -> bool:
        """
        Return True if this booking's stay period overlaps [start, end).
        Only active bookings can cause conflicts.
        Two periods overlap when one starts before the other ends.
        """
        if not self.is_active():
            return False
        return self.__stay_date < end and start < self.__leave_date

    def add_cage_service(self, cage_service):
        self.__payment.add_receipt_list(cage_service)

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
    
    def book(self):
        """ mark timeslot as unavailable when booked"""
        self.__available = False
    
    def free(self):
        """ free timeslot after examination """
        self.__available = True


class Vet(Employee):
    """Veterinarian — creates medical records, writes prescriptions, performs examinations."""
    def __init__(self, employee_id: str, name: str, salary: float, expertise: Species, phone_num: str):
        super().__init__(employee_id, name, salary, phone_num)
        self.__expertise = expertise
        self.__timeslot_list = []
    
    @property
    def expertise(self):
        return self.__expertise
    @property
    def timeslots(self):
        return self.__timeslot_list
    @property
    def role(self):
        return "Vet"
    
    def add_timeslot(self, datetime : datetime):
        self.__timeslot_list.append(TimeSlot(datetime))

    def is_compatible_with(self, species: Species):
        return species == self.__expertise

    def is_available_at(self, chosen_time : datetime):
        for slot in self.__timeslot_list:
            if slot.date == chosen_time and slot.available:
                return True
        return False
    
    def book_timeslot(self, chosen_time : datetime):
        """Called after an appointment is confirmed to prevent double-booking."""
        for slot in self.__timeslot_list:
            if slot.date == chosen_time and slot.available:
                slot.book()
                return True
        return False
    
    def free_timeslot(self, date: datetime):
        """Free timeslot after examination"""
        for slot in self.__timeslot_list:
            if slot.date == date:
                slot.free()
                return True
        return False
    
class HospitalStaff(Employee):
    """
    Front-desk staff.
    Responsibilities: check-in patients, book/cancel appointments,
    admit/discharge pets, process payments.
    """
    def __init__(self, employee_id: str, name: str, salary: float, phone_num: str):
        super().__init__(employee_id, name, salary, phone_num)

    @property
    def role(self) -> str:      return "HospitalStaff"


class HospitalManager(Employee):
    """
    Hospital manager.
    Responsibilities: add/remove staff, manage wards, cages, medicines,
    update pricing, and oversee hospital operations.
    """
    def __init__(self, employee_id: str, name: str, salary: float, phone_num: str):
        super().__init__(employee_id, name, salary, phone_num)

    @property
    def role(self) -> str:      return "HospitalManager"


class Prescription:
    """
    A single drug instruction issued by a vet during a consultation.
    Links a Medicine to a quantity and usage instruction for billing and dispensing.
    """
    def __init__(self, medicine, instruction:str, quantity: int):
        self.__medicine: Medicine = medicine
        self.__instruction = instruction
        self.__quantity = quantity

    @property
    def medicine(self):
        return self.__medicine
    @property
    def quantity(self):
        return self.__quantity
        
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
    def unit_price(self):       
        return self.__unit_price
    @property
    def id(self):               
        return self.__id
    @property
    def name(self):         
        return self.__name

    @unit_price.setter
    def unit_price(self, new_unitprice: float):       
        self.__unit_price = new_unitprice


class MedicalRecord :
    def __init__(self,medical_id:str, date: str, pet: object, user :object, vet: object, symptoms: str, diagnosis: str, prescription: list[Prescription], admit: bool,
        appointment: object)  :
        self.__id = medical_id
        self.__appointment: Appointment = appointment 
        self.__date_recorded = date
        self.__pet = pet
        self.__user = user
        self.__vet = vet
        self.__symptoms = symptoms
        self.__diagnosis = diagnosis
        self.__prescription: list[Prescription] = prescription 
        self.__admited_record = admit

    @property
    def symptoms(self):
        return self.__symptoms
    @property
    def diagnosis(self):
        return self.__diagnosis
    @property
    def date_recorded(self):
        return self.__date_recorded
    @property
    def prescription(self):
        return self.__prescription
    
    def get_medical_id(self) -> str:
        return self.__id
    def get_pet(self):
        return self.__pet
    def get_vet(self):
        return self.__vet
    def get_admit_record(self):
        return self.__admited_record
    def get_appointment(self): 
        return self.__appointment

    def get_approval(self) -> Union[None,object]:
        """
        Return Pet and weight if approved return None if not aprroved
        """
        if(self.__admited_record == True): 
            return self.__pet, self.__pet.weight
        elif(isinstance(self.__admited_record, AdmitRecord)):
            return self.__admited_record, None
        return None, None

    def write_admit_record(self,admit_record: object):
        self.__admited_record = admit_record
        
    def check_out_at(self, date_leave: datetime) -> int:
        if(isinstance(self.__admited_record,AdmitRecord)):
            return self.__admited_record.check_out_at(date_leave)
        

class Ward:
    
    def __init__(self, ward_no: str, type: WardType, max_number_of_cage: int = 10):
        self.__ward_no = ward_no
        self.__type = type
        self.__cage_list = []
        self.__max_number_of_cage = max_number_of_cage

    @property
    def id(self):
        return self.__ward_no
    @property
    def type(self):
        return self.__type

    def try_admit(self, Pet:object, weight: float, required_ward_type: WardType = None) -> Union[object, str]:
        """
        Attempt to find an available cage in this ward that can hold a pet of the given weight.
        If required_ward_type is specified and does not match this ward's type, returns (None, None).
        On success returns (Cage, ward_no); on failure returns (None, None).
        """
        if required_ward_type is not None and self.__type != required_ward_type:
            return None, None
        for cage in self.__cage_list:
            if cage.can_admit(Pet, weight):
                return cage, self.__ward_no
        return None, None
    
    def check_out(self, Pet: PetProfile):
        """
        Find the cage occupied by the given pet and release it back to AVAILABLE.
        Returns true if the pet was found and checked out, otherwise returns false.
        """
        for cage in self.__cage_list: 
            if(cage.check_out(Pet)):
                return True
        return False

    def add_cage(self, cage: object):
        self.__cage_list.append(cage)

    def get_cages(self) -> list:
        "return cage_list in ward"
        return self.__cage_list
    
    def cage_pop(self, position):
        return self.__cage_list.pop(position)

    def __str__(self):
        return self.__ward_no
    

class Cage:
    def __init__(self, cage_no: str, cage_size: CageSize, pet: object ,cage_status: CageStatus):
        self.__cage_no = cage_no
        self.__cage_size = cage_size
        self.__pet = pet
        self.__cage_status = cage_status

    def can_admit(self, Pet: object, weight: float) -> Union[object, None]:
        "ถ้ากรงว่างและน้ำหนักสัตว์ไม่เกิน return True"
        if(self.__cage_status == CageStatus.AVAILABLE and weight < self.__cage_size.value):
            return True 
        return False
    
    def occupy(self, Pet: object):
        "รับ pet มาและupdate pet และ status ของกรงเป็น occupied"
        self.__pet = Pet
        self.__cage_status = CageStatus.OCCUPIED

    def check_out(self, Pet:object):
        if(Pet == self.__pet):
            self.__pet = None
            self.__cage_status = CageStatus.AVAILABLE
            return True
        return False

    def can_hold_weight(self, weight: float) -> bool:
        return weight <= self.__cage_size.value

    def is_cage_available(self, stay_date: datetime, leave_date: datetime,
                          booking_list: list) -> bool:
        """
        Return True if this cage has no active overlapping booking in [stay_date, leave_date).
        Used by book_cage() to find a free slot.
        """
        for booking in booking_list:
            if booking.cage is self and booking.overlaps_with(stay_date, leave_date):
                return False
        return True
    
    def reserve(self):
        """Mark RESERVED. Called in book_cage if successful"""
        self.__cage_status = CageStatus.RESERVED

    @property
    def status(self): return self.__cage_status
    @property
    def no(self):           return self.__cage_no
    @property
    def size(self):         return self.__cage_size

    def __str__(self):
        return self.__cage_no
    

class AdmitRecord:
    def __init__(self, pet_id: str, ward: object, cage: object, date_of_admit: datetime):
        self.__pet: str = pet_id
        self.__ward: Ward = ward
        self.__cage: Cage = cage
        self.__date_of_admit: datetime = date_of_admit
        self.__date_of_leave: datetime = None

    def get_pet(self):
        return self.__pet
    def get_cage(self):
        return self.__cage
    def get_ward(self):
        return self.__ward
    def get_checkout_date(self): 
        return self.__date_of_leave

    def check_out_at(self, date_leave: datetime) -> int:
        self.__date_of_leave = date_leave 
        diff = date_leave - self.__date_of_admit
        """ use ceiling so any partial day is charged as a full day (e.g. 2d 23h → 3 days) """
        return math.ceil(diff.total_seconds() / 86400)

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

    @property
    def name(self):  
        return self.__name

    # =========ADMIT==========#

    def admit(self,medical_record_id: str, date_admit: str, ward_type: str = WardType.STANDARD.name):
        """
        Admit a pet to the hospital by finding it a cage in the appropriate ward.

        Requires the linked appointment to be CHECKED_IN before admission can proceed.
        Blocks admission if the pet is already occupying a cage elsewhere.
        Iterates through all wards and attempts to find the first cage that is available
        and large enough for the pet's weight, within a ward of the requested type.
        On success, creates an AdmitRecord and links it to the MedicalRecord.

        Returns a success message or a descriptive error string.
        """
        pet = None
        weight = None
        medical = None
        date_admit = self.valid_date(date_admit)
        # parse enum
        try:
            ward_type_enum = WardType[ward_type]
        except KeyError:
            return f"Invalid ward type '{ward_type}'. Choose from: Standard, ICU, Isolation"

        for record in self.__medical_record_list:
            if record.get_medical_id() == medical_record_id:
                pet, weight = record.get_approval()
                medical = record
                break

        if medical is None:
            return f"Medical record '{medical_record_id}' not found"
        
        appointment: Appointment = medical.get_appointment()
        if appointment.status != AppointmentStatus.CHECKED_IN:
            return (f"Cannot admit: appointment status is '{appointment.status.name}', "
                    f"must be CHECKED_IN")

        if(isinstance(pet,PetProfile)):
            # block if pet is already admitted elsewhere
            if pet.is_admit() is not None:
                return f"Cannot admit: {pet.name} is already in cage {pet.is_admit()}"
            
            infectious = False
            if medical.diagnosis.upper() == "INFECTIOUS" and ward_type != WardType.ISOLATION:
                infectious = True
                
            for ward in self.__ward_list:
                if infectious:
                    cage, ward_no = ward.try_admit(pet, weight, required_ward_type=WardType.ISOLATION)
                else:  
                    cage, ward_no = ward.try_admit(pet, weight, required_ward_type=ward_type_enum)
                    
                if cage is not None:
                    cage.occupy(pet)
                    admit_record = AdmitRecord(pet.id, ward, cage, date_admit)
                    medical.write_admit_record(admit_record)
                    self.__admitted_list.append(admit_record)
                    
                    if infectious:
                        return f"Pet {pet.name} has infectious disease: Auto allocated to Isolation Ward: {ward_no} - Cage: {cage.no}."
                    return f"Admit success: {pet.name} → cage {cage.no} in ward {ward_no}."

            return f"No available {ward_type.name} cage that fits {pet.name} ({weight} kg)"

        elif pet is None:
            return "Not approved for admission"
        elif isinstance(pet, AdmitRecord):
            return "Already admitted"

    # =========CHECKOUT==========#

    def check_out(self, med_id: str, date_leave: str):
        """
        Discharge a pet from its cage and finalise the appointment.

        Looks up the MedicalRecord, verifies the pet is currently admitted and has not
        already been discharged, then checks that all outstanding fees have been paid
        before releasing the cage. Calculates billable days and adds a CageService
        line item to the appointment's payment, then marks the appointment COMPLETED.

        Returns a success message or a descriptive error string.
        """
        date_leave: datetime = self.valid_date(date_leave)
        medical_record = None

        for record in self.__medical_record_list:
            if(record.get_medical_id() == med_id):
                medical_record: MedicalRecord = record
                pet: PetProfile = record.get_pet()
                break

        if medical_record is None:
            return f"Medical record '{med_id}' not found"
        
        admit_record: AdmitRecord = medical_record.get_admit_record()

        # must be currently admitted
        if not isinstance(admit_record, AdmitRecord):
            return "Cannot check out: pet was never admitted"
        if admit_record.get_checkout_date() is not None:
            return "Cannot check out: pet has already been checked out"

        pet: PetProfile = medical_record.get_pet()
        appointment: Appointment = medical_record.get_appointment()

        # # must pay before leaving
        # total = appointment.payment.calculate_total()
        # if appointment.payment.status == PaymentStatus.UNPAID and total > 0:
        #     return f"Cannot check out: outstanding balance of {total} baht must be paid first"

        checked_out = False
        for ward in self.__ward_list:
            if ward.check_out(pet):
                checked_out = True
                break

        if not checked_out:
            return "Something went wrong: could not locate pet in any ward"

        total_days = medical_record.check_out_at(date_leave)
        cage: Cage = admit_record.get_cage()
        appointment.cage_service(total_days, admit_record.get_ward(),cage)
        appointment.completed()
        
        return f"{pet.id} checkout from {cage.no} at {datetime.strftime(date_leave, "%d/%m/%Y %H:%M")}"

    # =========MEDICAL RECORDS==========#

    def make_medical_record(self, medical_id: str, date: str, symptoms: str, diagnosis: str, prescription: object, admit: bool
                            ,examination_fee: float, appointment: object):
        """
        Create and store a MedicalRecord for a checked-in patient.

        Validates that the appointment exists and is in CHECKED_IN status, and that
        the medical_id has not already been used. Builds the MedicalRecord, stores it,
        adds a MedicalService line to the payment, and attaches the record to the pet's history.

        Returns an error string on failure, or None on success.
        """
        if not isinstance(appointment, Appointment):
            return "Invalid appointment object"

        # Only valid for checked-in appointments
        if appointment.status != AppointmentStatus.CHECKED_IN:
            return (f"Cannot create medical record: appointment status is "
                    f"'{appointment.status.name}', must be CHECKED_IN")

        # Prevent duplicate record IDs
        for rec in self.__medical_record_list:
            if rec.get_medical_id() == medical_id:
                return f"Medical record ID '{medical_id}' already exists"
            
        user: User = self.search_user_by_id(appointment.user_id)
        vet: Vet = self.search_vet_from_id(appointment.vet_id)
        medical_rec = MedicalRecord(medical_id,date,appointment.pet,user,vet,symptoms,diagnosis,prescription,admit, appointment=appointment)
        self.__medical_record_list.append(medical_rec)
        appointment.make_payment(examination_fee, prescription)
        appointment.pet.add_medical_record(medical_rec)
        vet.free_timeslot(appointment.scheduled_date)
        
        return f"Medical record {medical_id} created successfully"
            
    def write_prescription(self, medicine_id: str, amount: int, instruction: str, pet_id: str):
        """
        Create a Prescription object for the given medicine and pet.

        Verifies the medicine and pet both exist, then checks the pet's allergy list
        before issuing the prescription. Returns the Prescription object on success,
        or an error string if the medicine is not found, the pet is not found,
        or the pet is allergic to the medicine.
        """
        medicine = self.search_medicine_by_id(medicine_id)
        if medicine is None:
            return f"Medicine '{medicine_id}' not found"
        petprofile: PetProfile = self.search_pet_by_id(pet_id)
        if petprofile is None:
            return f"Pet '{pet_id}' not found"
        if petprofile.is_allergic(medicine):
            return "Cannot prescribe: drug allergy on record"
        return Prescription(medicine, instruction, amount)
    
    # =========PAYMENT==========#

    def make_payment(self, user_id: str, payment_method: str):
        """
        Record full payment for the user's current active appointment.

        Looks up the user, retrieves their active appointment's Payment object,
        and calls pay() with the given method. 
        Returns a confirmation string or an error message.
        """
        user = self.search_user_by_id(user_id)
        if user is None:
            return f"User '{user_id}' not found"
        if user.current_appointment is None:
            return "No active appointment found for this user"
        if user.current_appointment.status != AppointmentStatus.COMPLETED:
            return "User has not checked out."
        try:
            method = PaymentMethod[payment_method.upper()]
        except KeyError:
            return f"Invalid payment method. Choose from: {[m.name for m in PaymentMethod]}"
        
        self.calculate_payment(user_id)
        return user.current_appointment.payment.pay(method)
        
    def get_receipt(self, user_id: str):
        """
        Return an itemised receipt for the user's current appointment.

        Includes the running total, payment status, and a breakdown of each service item.
        Can be called before payment to let the user review charges.
        Returns an error dict if the user or appointment is not found.
        """
        user = self.search_user_by_id(user_id)
        if user is None:
            return {"error": f"User '{user_id}' not found"}
        if user.current_appointment is None:
            return {"error": "No active appointment"}
        
        payment: Payment = user.current_appointment.payment
        if user.get_discount() != 1:
            return {
                "before discount": payment.calculate_total(),
                "discount": f"{(1 - user.get_discount()) * 100}%",
                "after discount": payment.total,
                "status": payment.status.name,
                "items": payment.get_receipt()
            }
        else:
            return {
                "total": payment.total,
                "status": payment.status.name,
                "items": payment.get_receipt()
            }
    
    def calculate_payment(self, user_id: str):
        """
        Return the total amount currently owed for the user's active appointment.
        Returns 0 if no appointment exists or if there is nothing to bill yet.
        """
        user = self.search_user_by_id(user_id)
        if user is None:
            return f"Can't find '{user_id}'"
        try:
            user.current_appointment.payment.calculate_total(keep=True)
            return user.current_appointment.payment.apply_discount(user.get_discount())
        except Exception as e:
            print(e)
            return "Calculation failed."
    
    # =========APPOINTMENTS==========#  

    def check_user_eligibility(self, user: User):
        """
        Determine whether a user is allowed to book a new appointment.

        Returns False if the user has exhausted their no-show credits (no_show_left == 0),
        or if they already have an active (SCHEDULED or CHECKED_IN) appointment.
        Returns True if they are clear to book.
        """
        if user.no_show_left == 0:
            return False
        else:
            # มี appointment ที่ยังไม่เสร็จ
            for appt in self.__appointment_list:
                if appt.user_id == user.user_id and appt.status in [AppointmentStatus.SCHEDULED, AppointmentStatus.CHECKED_IN]:
                    return False
        return True
    
    def book_appointment(self, user_id: str, vet_id: str, pet_id: str, chosen_date: str):
        """
        Book a new appointment for a user's pet with the specified vet.

        Validates that all entities exist, the chosen date is not in the past,
        the vet can treat the pet's species, the user is eligible to book,
        and the vet has a free timeslot at the chosen time. On success, creates
        the Appointment, assigns it as the user's current appointment, marks the
        vet's timeslot as booked, and returns the new Appointment object.

        Returns an error string on any validation failure.
        """
        chosen_date: datetime = self.valid_date(chosen_date)

        user = self.search_user_by_id(user_id)
        if user is None:
            return f"User '{user_id}' not found"

        vet = self.search_employee_by_id(vet_id)
        if vet is None or not isinstance(vet, Vet):
            return f"Vet '{vet_id}' not found"

        petprofile = user.get_pet_by_id(pet_id)
        if petprofile is None:
            return f"Pet '{pet_id}' not found for user '{user_id}'"
        
        if user.current_appointment != None and user.current_appointment.status != AppointmentStatus.COMPLETED:
            return f"User {user_id} already has an ongoing appointment"

        if chosen_date < datetime.now():
            return f"Cannot book a past date ({chosen_date.strftime('%d/%m/%Y %H:%M')})"

        if not vet.is_compatible_with(petprofile.species):
            return "This vet cannot treat this species"

        if not self.check_user_eligibility(user):
            return "User is not eligible: check no-show count or existing active appointment"

        if not vet.is_available_at(chosen_date):
            return "This timeslot is not available"
        
        appointment_id = str(uuid.uuid4())
        new_appointment: Appointment = Appointment(appointment_id, user_id, vet_id, petprofile, chosen_date, status=AppointmentStatus.SCHEDULED)
        
        user.current_appointment = new_appointment
        self.__appointment_list.append(new_appointment)
        vet.book_timeslot(chosen_date)
        return new_appointment

    def add_appointment(self, appointment: Appointment):
        self.__appointment_list.append(appointment)

    def cancel_appointment(self, appointment_id: str, user_id: str):
        """
        Cancel an existing appointment.

        Blocks cancellation if the appointment is already COMPLETED or CANCELLED,
        if the patient has already CHECKED_IN (they must speak to reception),
        or if the cancellation is attempted within 2 hours of the scheduled time.
        On success, frees the user's current_appointment slot and returns the vet's
        timeslot to available so it can be rebooked.

        Returns a success message or a descriptive error string.
        """
        appointment = self.search_appointment_by_id(appointment_id)    
        if not appointment:
            return f"Appointment {appointment_id} not found"
        
        if appointment.user_id != user_id:
            return f"Appointment {appointment_id} does not belong to user {user_id}"

        if appointment.status == AppointmentStatus.NO_SHOW:
            return "Cannot cancel a missed appointment"
        
        if appointment.status == AppointmentStatus.COMPLETED:
            return "Cannot cancel a completed appointment"
        
        if appointment.status == AppointmentStatus.CANCELLED:
            return "Appointment is already cancelled"
        
        # Checked-in patients cannot self-cancel
        if appointment.status == AppointmentStatus.CHECKED_IN:
            return "Cannot cancel: patient is already checked in. Please speak to reception"

        # 2-hour cancellation deadline
        if datetime.now() > appointment.scheduled_date - timedelta(hours=2):
            return (f"Cannot cancel: must cancel at least 2 hours before the appointment "
                    f"(scheduled at {appointment.scheduled_date.strftime('%d/%m/%Y %H:%M')})")

        # Cancel the appointment
        appointment.cancel()
        
        # Clear user's current appointment if this is their current one
        user = self.search_user_by_id(user_id)
        if user.current_appointment and user.current_appointment.appointment_id == appointment_id:
            user.current_appointment = None
        
        # Get the vet and return the timeslot
        vet = self.search_employee_by_id(appointment.vet_id)
        if vet and isinstance(vet, Vet):
            vet.add_timeslot(appointment.scheduled_date)
        
        return f"Appointment {appointment_id} cancelled successfully"

    def check_in(self, appointment_id: str, user_id: str, check_in_time: str = None):
        """
        Record a patient's arrival for a scheduled appointment.

        Rejects check-in if the patient arrives before the scheduled time.
        If the patient arrives more than 30 minutes late, the appointment is
        automatically marked NO_SHOW, the user's no-show credit is decremented,
        and their current_appointment is cleared so they can rebook.
        On a valid arrival (on time up to 30 minutes late), status changes to CHECKED_IN.

        check_in_time defaults to datetime.now() if not provided.
        Returns a status message string.
        """

        if check_in_time is None:
            """ Use current time if no check_in_time provided"""
            check_in_time = datetime.now()
        else:
            check_in_time: datetime = self.valid_date(check_in_time)

        appointment = self.search_appointment_by_id(appointment_id)

        if not appointment:
            return f"Appointment {appointment_id} not found"

        if appointment.user_id != user_id:
            return f"Appointment {appointment_id} does not belong to user {user_id}"

        if appointment.status == AppointmentStatus.CANCELLED:
            return "Cannot check in: appointment is cancelled"

        if appointment.status == AppointmentStatus.COMPLETED:
            return "Cannot check in: appointment is already completed"

        if appointment.status == AppointmentStatus.NO_SHOW:
            return "Cannot check in: appointment was marked as no-show"

        if appointment.status == AppointmentStatus.CHECKED_IN:
            return "Already checked in"
        
        scheduled = appointment.scheduled_date

        if check_in_time < scheduled:
            minutes_early = int((scheduled - check_in_time).total_seconds() / 60)
            return f"Too early to check in. Appointment starts at {scheduled.strftime('%H:%M')} ({minutes_early} minute(s) remaining)"

        if check_in_time > scheduled + timedelta(minutes=30):
            """ Auto mark as NO_SHOW and free the user to book again"""
            appointment.mark_no_show()
            user = self.search_user_by_id(user_id)
            if user:
                user.decrement_no_show()
                user.current_appointment = None
            minutes_late = int((check_in_time - scheduled).total_seconds() / 60)
            return (f"Arrived {minutes_late} minute(s) late. Appointment marked as no-show. "
                    f"No-shows remaining: {user.no_show_left}. Please book a new appointment.")

        # On time or within 30 min late
        appointment.checked_in()
        return f"Checked in successfully for appointment {appointment_id}"

    def mark_no_show(self, appointment_id: str, user_id: str):
        """
        Staff action to manually mark a SCHEDULED appointment as NO_SHOW.

        Only valid for appointments still in SCHEDULED status.
        Decrements the user's no-show credit and clears their current_appointment
        so they are free to book again.

        Returns a confirmation or error string.
        """
        appointment = self.search_appointment_by_id(appointment_id)
        if not appointment:
            return f"Appointment '{appointment_id}' not found"
        if appointment.user_id != user_id:
            return f"Appointment does not belong to user '{user_id}'"
        if appointment.status != AppointmentStatus.SCHEDULED:
            return f"Can only mark SCHEDULED appointments as no-show (current: {appointment.status.name})"
        
        appointment.mark_no_show()
        user = self.search_user_by_id(user_id)
        if user:
            user.decrement_no_show()
            user.current_appointment = None
        return f"Appointment '{appointment_id}' marked as no-show. No-shows remaining: {user.no_show_left}"
    
    def clear_appointment(self, user_id: str):
        user: User = self.search_user_by_id(user_id)
        user.current_appointment = None
        return user
    
    # =========USERS==========#

    def add_user(self, user: User):
        for existing in self.__user_list:
            if existing.user_id == user.user_id:
                raise ValueError(f"User ID '{user.user_id}' already exists")
        self.__user_list.append(user)
    
    # =========EMPLOYEES==========#

    def add_employee(self, employee: Employee):
        for existing in self.__employee_list:
            if existing.employee_id == employee.employee_id:
                raise ValueError(f"Employee ID '{employee.employee_id}' already exists")
        self.__employee_list.append(employee)

    # =========WARDS & MEDICINES==========#

    def add_ward(self, ward: object):
        self.__ward_list.append(ward)

    def add_medicine(self, medicine: object):
        self.__medicine_list.append(medicine)

    def get_med_list(self):
        return self.__medical_record_list

    def remove_cage(self,Cage_no) -> Union[Cage, None]:
        for ward in self.__ward_list:
            index = 0
            for cage in ward.get_cages():
                if(cage.no == Cage_no and cage.status == CageStatus.AVAILABLE):
                    cage = ward.cage_pop(index)
                    return cage
                index += 1
        return None

    def cage_existed_on_ward(self, cage_no:str) -> object:
        for ward in self.__ward_list:
            for cage in ward.get_cages():
                if(cage.no == cage_no):
                    return ward
        return None

    # =========SEARCH==========#

    def search_appointment_by_id(self, a_id):
        for appointment in self.__appointment_list:
            if(appointment.appointment_id == a_id):
                return appointment
        return None
    
    def search_cage_booking_by_id(self, b_id):
        for booking in self.__cage_booking_list:
            if booking.booking_id == b_id:
                return booking
        return None

    def search_vet_from_id(self, id):
        for employee in self.__employee_list:
            if(isinstance(employee,Vet) and employee.employee_id == id):
                return employee
            
    def search_ward_by_id(self, ward_id: str):
        for ward in self.__ward_list:
            if ward.id == ward_id:
                return ward
        return None

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
    
    def search_medicine_by_id(self, medicine_id: str):
        for medicine in self.__medicine_list:
            if(medicine.id == medicine_id):
                return medicine

    # =========PRICING==========#

    def new_medicine_price(self, medicine_id: str, new_price: float):
        medicine = self.search_medicine_by_id(medicine_id)
        if isinstance(medicine, Medicine):
            old = medicine.unit_price
            medicine.unit_price = new_price
            return f"Old price: {old} → New price: {new_price}"
        return "Medicine not found"

    def new_cage_price(self, size: str, new_price: float):
        for cage_size in [CageSize.S, CageSize.M, CageSize.L]:
            if cage_size.name == size:
                old = CageService.get_price(cage_size.name)
                cage_size.new_price(cage_size, new_price)
                return f"Old price: {old} → New price: {new_price}"
        return f"Cage size '{size}' not found"

    # =========DISPLAY==========#

    def display_pet_admit(self, user_id: str) -> dict:
        user = self.search_user_by_id(user_id)
        if not isinstance(user, User):
            return {"status": "user not found"}
        return {pet.id: pet.is_admit() for pet in user.pet_list if pet.is_admit() is not None}

    def display_all_medical_records_for_pet(self, pet_id: str) -> dict:
        final_result = []
        for record in self.__medical_record_list:
            result = {}
            if record.get_pet().id == pet_id:
                result["medical_record_id"] = record.get_medical_id()
                result["symptoms"] = record.symptoms
                result["diagnosis"] = record.diagnosis
                result["date_recorded"] = record.date_recorded
                result["prescription"] = record.prescription
                final_result.append(result)
        return final_result
    
    # =========PUBLIC GETTERS==========#

    def get_all_users(self):            return self.__user_list
    def get_all_employees(self):        return self.__employee_list
    def get_all_appointments(self):     return self.__appointment_list
    def get_all_wards(self):            return self.__ward_list
    def get_all_medicines(self):        return self.__medicine_list
    def get_all_medical_records(self):  return self.__medical_record_list

    # =========VALIDATION==========#

    def valid_date(self, date_time: str):
        try:
            return datetime.strptime(date_time, "%d/%m/%Y %H:%M")
        except:
            raise Exception("Wrong date format.")

    # ==========CAGE BOOKING==========#

    def book_cage(self,
                  user_id: str,
                  pet_id: str,
                  cage_size: str,
                  stay_date: str,
                  duration: int,
                  ward_type: str = WardType.STANDARD.name):
        
        stay_date: datetime = self.valid_date(stay_date)

        user = self.search_user_by_id(user_id)
        if user is None:
            return f"User '{user_id}' not found"

        pet = user.get_pet_by_id(pet_id)
        if pet is None:
            return f"Pet '{pet_id}' not found for user '{user_id}'"

        if stay_date <= datetime.now():
            return "Cannot book: stay date must be in the future" 

        if not (1 <= duration <= 24):
            return (f"Cannot book: duration must be between 1 and 24 hours "
                    f"(got {duration})")  

        leave_date = stay_date + timedelta(hours=duration)

        # parse enums
        try:
            size_enum = CageSize[cage_size.upper()]
        except KeyError:
            return f"Invalid cage size '{cage_size}'. Choose from: S, M, L"

        try:
            ward_type_enum = WardType[ward_type]
        except KeyError:
            return f"Invalid ward type '{ward_type}'. Choose from: Standard, ICU, Isolation"

        # weight check upfront for a clearer error
        if not (pet.weight < size_enum.value):
            return (f"Cannot book: {pet.name} weighs {pet.weight} kg and does not fit "
                    f"in a size-{cage_size} cage (max {size_enum.value} kg)")  

        # no duplicate active booking for this pet
        if not self.is_pet_available(pet):
            return f"Cannot book: {pet.name} already has an active cage booking"  
        
        size_exist = False

        for ward in self.__ward_list:
            if ward.type != ward_type_enum:
                continue 

            for cage in ward.get_cages():
                if cage.size != size_enum or cage.status != CageStatus.AVAILABLE:
                    continue
                size_exist = True

                if not cage.can_hold_weight(pet.weight):
                    continue

                if not cage.is_cage_available(stay_date, leave_date, self.__cage_booking_list):
                    continue
                    
                # reserve cage
                cage.reserve()

                # create and register the booking
                booking = CageBooking(
                    user=user, pet=pet, ward=ward, cage=cage,
                    stay_date=stay_date, leave_date=leave_date
                )
                self.__cage_booking_list.append(booking)
                user.add_cage_booking(booking)
                return booking

        # specific error messages so the caller knows exactly what failed
        if not size_exist:
            return (f"No size-{cage_size} cage found in any {ward_type} ward. "
                    f"Please ask a manager to add one.") 
        return (f"No available size-{cage_size} cage in a {ward_type} ward "
                f"for {stay_date} + {duration} hour(s). "
                f"Try different dates or ask staff about availability.") 

    def cancel_cage_booking(self, booking_id: str, user_id: str) -> str:
        """
        Cancel a cage booking.

        Rules
        -----
        - Must belong to the given user.
        - Must be CONFIRMED (cannot cancel CHECKED_IN or finished bookings).
        - Cannot cancel within 24 hours of check-in.
        """
        booking = self.search_cage_booking_by_id(booking_id)
        if booking is None:
            return f"Cage booking '{booking_id}' not found"

        if booking.user.user_id != user_id:
            return f"Booking '{booking_id}' does not belong to user '{user_id}'"

        if booking.status == BookingStatus.CANCELLED:
            return "Booking is already cancelled"

        if booking.status == BookingStatus.COMPLETED:
            return "Cannot cancel a completed booking"

        if booking.status == BookingStatus.CHECKED_IN:
            return "Cannot cancel: pet is already checked in. Please speak to reception"

        # 24-hour cancellation deadline
        if datetime.now() > booking.stay_date - timedelta(hours=24):
            return (f"Cannot cancel: must cancel at least 24 hours before check-in "
                    f"(check-in: {booking.stay_date.strftime('%d/%m/%Y %H:%M')})")

        booking.cancel()
        return f"Cage booking '{booking_id}' cancelled successfully"

    def checkin_cage_booking(self, booking_id: str, user_id: str) -> str:
        """
        Mark a cage booking CHECKED_IN when the pet physically arrives.
        Cannot check in before the booked stay_date.
        """
        booking = self.search_cage_booking_by_id(booking_id)
        if booking is None:
            return f"Cage booking '{booking_id}' not found"
        if booking.user.user_id != user_id:
            return f"Booking '{booking_id}' does not belong to user '{user_id}'"
        if booking.status != BookingStatus.CONFIRMED:
            return f"Cannot check in: booking status is {booking.status.name}"
        if datetime.now() < booking.stay_date:
            minutes = int((booking.stay_date - datetime.now()).total_seconds() / 60)
            return (f"Too early to check in. Boarding starts at "
                    f"{booking.stay_date.strftime('%d/%m/%Y %H:%M')} "
                    f"({minutes} minute(s) remaining)")
        return booking.confirm_checkin()

    def checkout_cage_booking(self, booking_id: str, user_id: str) -> str:
        """Mark a cage booking COMPLETED and release the cage when the pet is collected."""
        booking = self.search_cage_booking_by_id(booking_id)
        if booking is None:
            return f"Cage booking '{booking_id}' not found"
        if booking.user.user_id != user_id:
            return f"Booking '{booking_id}' does not belong to user '{user_id}'"
        # Add payment
        booking.add_cage_service(CageService(booking.ward, booking.cage, Stay_duration=(booking.leave_date - booking.stay_date).hours))
        return booking.confirm_checkout()

    def get_cage_bookings_for_user(self, user_id: str) -> Union[list, str]:
        """
        Return all cage bookings for the given user sorted by stay_date.
        Returns an error string if the user is not found.
        """
        user = self.search_user_by_id(user_id)
        if user is None:
            return f"User '{user_id}' not found"
        result = []
        for b in sorted(user.cage_bookings, key=lambda x: x.stay_date):
            duration = (b.leave_date - b.stay_date).hours or 1
            result.append({
                "booking_id":  b.booking_id,
                "pet_id":      b.pet.id,
                "pet_name":    b.pet.name,
                "ward_id":     b.ward.id,
                "ward_type":   b.ward.type.name,
                "cage_no":     b.cage.no,
                "cage_size":   b.cage.size.name,
                "stay_date":   b.stay_date.strftime("%d/%m/%Y %H:%M"),
                "leave_date":  b.leave_date.strftime("%d/%m/%Y %H:%M"),
                "duration_hours": duration,
                "status":      b.status.name,
                "total_cost":  CageService.get_price(b.cage.size.name) * duration,
            })
        return result

    def is_pet_available(self, pet: PetProfile) -> bool:
        for booking in self.__cage_booking_list:
            if booking.pet is pet and booking.is_active():
                return False
        return True