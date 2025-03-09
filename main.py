from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, engine, Base
import models, schemas

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.User).filter(models.User.is_active == True).offset(skip).limit(limit).all()
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if updating email to one that already exists
    if user.email is not None and user.email != db_user.email:
        email_exists = db.query(models.User).filter(models.User.email == user.email).first()
        if email_exists:
            raise HTTPException(status_code=400, detail="Email already registered")

    update_data = user.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Soft delete
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/users/{user_id}/matches", response_model=List[schemas.User])
def find_matches(
        user_id: int,
        db: Session = Depends(get_db),
        age_diff: int = 5,
        same_city: bool = True,
        interest_overlap: bool = True
):
    # Get the user
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Base query for active users excluding the user themselves
    matches_query = db.query(models.User).filter(
        models.User.id != user.id,
        models.User.is_active == True
    )

    # Filter by preferred gender (assuming opposite gender matching for simplicity)
    if user.gender.lower() == "male":
        matches_query = matches_query.filter(models.User.gender == "female")
    elif user.gender.lower() == "female":
        matches_query = matches_query.filter(models.User.gender == "male")

    # Filter by age difference if specified
    if age_diff > 0:
        matches_query = matches_query.filter(
            models.User.age.between(user.age - age_diff, user.age + age_diff)
        )

    # Filter by same city if specified
    if same_city:
        matches_query = matches_query.filter(models.User.city == user.city)

    # Get all potential matches
    potential_matches = matches_query.all()

    # Filter by interest overlap if specified
    if interest_overlap and potential_matches:
        user_interests = set(i.strip().lower() for i in user.interests.split(','))

        # Filter matches with at least one common interest
        filtered_matches = []
        for match in potential_matches:
            match_interests = set(i.strip().lower() for i in match.interests.split(','))
            if user_interests.intersection(match_interests):
                filtered_matches.append(match)

        return filtered_matches

    return potential_matches