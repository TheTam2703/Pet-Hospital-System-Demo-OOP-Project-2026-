from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
import uuid


# ================= ENUM =================

class CageSize(Enum):
    S = "S"
    M = "M"
    L = "L"

    def weight_limit(self):
        if self == CageSize.S:
            return 5
        elif self == CageSize.M:
            return 15
        elif self == CageSize.L:
            return 30


class CageStatus(Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    OCCUPIED = "OCCUPIED"


class BookingStatus(Enum):
    SCHEDULED = "SCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


# ================= ENTITY =================

class PetProfile:

    def __init__(self, pet_id: str, name: str, weight: float):
        self.__id = pet_id
        self.__name = name
        self.__weight = weight

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @property
    def weight(self):
        return self.__weight


class User:

    def __init__(self, user_id: str, name: str):
        self.__user_id = user_id
        self.__name = name
        self.__pet_list: List[PetProfile] = []
        self.__booking_list: List["CageBooking"] = []

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
    def booking_list(self):
        return self.__booking_list

    def add_pet(self, pet: PetProfile):
        self.__pet_list.append(pet)

    def get_pet_by_id(self, pet_id: str):
        for pet in self.__pet_list:
            if pet.id == pet_id:
                return pet
        return None


class Cage:

    def __init__(self, cage_no: str, cage_size: CageSize):
        self.__cage_no = cage_no
        self.__cage_size = cage_size
        self.__cage_status = CageStatus.AVAILABLE

    @property
    def cage_no(self):
        return self.__cage_no

    @property
    def cage_size(self):
        return self.__cage_size

    @property
    def cage_status(self):
        return self.__cage_status

    def can_hold_weight(self, weight: float) -> bool:
        return weight <= self.__cage_size.weight_limit()

    def is_cage_available(self,
                          stay_date: datetime,
                          leave_date: datetime,
                          booking_list: List["CageBooking"]) -> bool:

        if self.__cage_status == CageStatus.OCCUPIED:
            return False

        for booking in booking_list:

            if booking.cage == self and booking.status != BookingStatus.CANCELLED:

                if not (leave_date <= booking.stay_date or
                        stay_date >= booking.leave_date):
                    return False

        return True


class Ward:

    def __init__(self, ward_no: str):
        self.__ward_no = ward_no
        self.__cage_list: List[Cage] = []

    @property
    def ward_no(self):
        return self.__ward_no

    def add_cage(self, cage: Cage):
        self.__cage_list.append(cage)

    @property
    def cage_list(self):
        return self.__cage_list


class CageBooking:

    def __init__(self,
                 user: User,
                 pet: PetProfile,
                 ward: Ward,
                 cage: Cage,
                 stay_date: datetime,
                 leave_date: datetime):

        self.__booking_id = str(uuid.uuid4())
        self.__booking_status = BookingStatus.SCHEDULED
        self.__booking_date = datetime.now()

        self.__user = user
        self.__pet_profile = pet

        self.__stay_date = stay_date
        self.__leave_date = leave_date

        self.__ward = ward
        self.__cage = cage

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
    def pet_profile(self):
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


# ================= SYSTEM =================

class PetHospital:

    def __init__(self):
        self.__user_list: List[User] = []
        self.__ward_list: List[Ward] = []
        self.__booking_list: List[CageBooking] = []

    @property
    def booking_list(self):
        return self.__booking_list

    def add_user(self, user: User):
        self.__user_list.append(user)

    def add_ward(self, ward: Ward):
        self.__ward_list.append(ward)

    def search_user_by_id(self, user_id: str) -> Optional[User]:
        for user in self.__user_list:
            if user.user_id == user_id:
                return user
        return None

    def is_pet_available(self, pet: PetProfile) -> bool:

        for booking in self.__booking_list:

            if booking.pet_profile.id == pet.id:

                if booking.status not in (
                    BookingStatus.NO_SHOW,
                    BookingStatus.CANCELLED,
                    BookingStatus.COMPLETED
                ):
                    return False

        return True

    def book_cage(self,
                  user_id: str,
                  pet_id: str,
                  cage_size: CageSize,
                  stay_date: datetime,
                  duration: int):

        user = self.search_user_by_id(user_id)

        if not user:
            raise Exception("User not found")

        pet = user.get_pet_by_id(pet_id)

        if not pet:
            raise Exception("Pet not found")

        leave_date = stay_date + timedelta(hours=duration)

        size_exist = False
        valid_weight_found = False

        if not self.is_pet_available(pet):
            raise Exception("This pet already has an active booking")

        for ward in self.__ward_list:

            for cage in ward.cage_list:

                if cage.cage_size != cage_size:
                    continue
                size_exist = True

                if not cage.can_hold_weight(pet.weight):
                    continue
                valid_weight_found = True

                if not cage.is_cage_available(stay_date, leave_date, self.__booking_list):
                    continue

                booking = CageBooking(
                    user=user,
                    pet=pet,
                    cage=cage,
                    ward=ward,
                    stay_date=stay_date,
                    leave_date=leave_date
                )

                self.__booking_list.append(booking)
                user.booking_list.append(booking)

                return booking

        if not size_exist:
            raise Exception("Cage size not found")

        if not valid_weight_found:
            raise Exception("Your pet is overweight for this cage size")

        raise Exception("No cage available in selected time")