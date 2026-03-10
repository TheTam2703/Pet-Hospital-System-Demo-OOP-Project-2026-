from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
import uvicorn

from Class import (
    PetHospital,
    User,
    PetProfile,
    Ward,
    Cage,
    CageSize,
)

# ========= DATA ========= #

def create_instances():

    system = PetHospital()

    user = User("1", "Namchiew")

    pet1 = PetProfile("5", "siri", 5.0)
    pet2 = PetProfile("12", "rodtang", 12.0)

    user.add_pet(pet1)
    user.add_pet(pet2)

    system.add_user(user)

    ward1 = Ward("W1")

    cage1 = Cage("C1", CageSize.S)
    cage2 = Cage("C2", CageSize.M)
    cage3 = Cage("C3", CageSize.L)

    ward1.add_cage(cage1)
    ward1.add_cage(cage2)
    ward1.add_cage(cage3)

    system.add_ward(ward1)

    return system


system = create_instances()

app = FastAPI()


# ========= แปลงปี พศ คศ ========= #

def be_to_ad(dt: datetime):

    if dt.year > 2400:
        return dt.replace(year=dt.year - 543)

    return dt


def ad_to_be_format(dt: datetime):

    dt_be = dt.replace(year=dt.year + 543)

    return dt_be.strftime("%d/%m/%Y %H:%M")


# ========= API ========= #

@app.get("/")
def root():
    return {"message": "Pet Hospital API Running"}


@app.post("/book_cage")
def book_cage(

    user_id: str = Query(
        description="รหัสผู้ใช้"
    ),

    pet_id: str = Query(
        description="รหัสสัตว์เลี้ยง"
    ),

    cage_size: CageSize = Query(),

    stay_date: datetime = Query(
        description="YYYY-MM-DDTHH:MM (ปี พ.ศ.)"
    ),

    duration: int = Query(
        description="จำนวนชั่วโมงที่พัก"
    )

):

    try:

        stay_date_ad = be_to_ad(stay_date)

        result = system.book_cage(
            user_id=user_id,
            pet_id=pet_id,
            cage_size=cage_size,
            stay_date=stay_date_ad,
            duration=duration
        )

        return {

            "booking_id": result.booking_id,
            "status": result.status.value,

            "stay_date": ad_to_be_format(result.stay_date),
            "leave_date": ad_to_be_format(result.leave_date),

            "user_id": result.user.user_id,
            "pet_id": result.pet_profile.id,

            "cage_id": result.cage.cage_no,
            "ward_id": result.ward.ward_no
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


if __name__ == "__main__":

    uvicorn.run(
        "BookCage:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )