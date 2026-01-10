import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Response 
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select 
from sqlalchemy.exc import IntegrityError 
from contextlib import asynccontextmanager 
from fastapi.middleware.cors import CORSMiddleware 
from .database import engine, get_db 
from .models import Base, ClubDB, MembershipDB
from .schemas import (
    ClubCreate,
    ClubRead,
    ClubUpdate,
    MembershipCreate,
    MembershipRead,
    MembershipUpdate,
    MembershipReadWithClub,
)

#Replacing @app.on_event("startup") 
@asynccontextmanager 
async def lifespan(app: FastAPI): 
    Base.metadata.create_all(bind=engine)    
    yield 
 
app = FastAPI(lifespan=lifespan) 
 
# CORS (add this block) 
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"],   # dev-friendly; tighten in prod 
    allow_methods=["*"], 
    allow_headers=["*"], 
) 

def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg) #Duplicate info

#helper function
def verify_user_exists(user_id: int) -> None:
    base_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001").rstrip("/")
    url = f"{base_url}/api/users/{user_id}"

    try:
        r = httpx.get(url, timeout=2.0)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Users service unavailable")

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")
    if r.status_code != 200:
        raise HTTPException(status_code=503, detail="Users service unavailable")

# ------------- Health Check ---------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "clubs"}

#--------------- Club Endpoints ------------------

# GET: All Clubs, Clubs by ID
@app.get("/api/clubs", response_model=list[ClubRead]) 
def List_All_Clubs(db: Session = Depends(get_db)): 
    stmt = select(ClubDB).order_by(ClubDB.id) 
    return list(db.execute(stmt).scalars()) 
 
@app.get("/api/clubs/{club_id}", response_model=ClubRead) 
def Get_Club_By_ID(club_id: int, db: Session = Depends(get_db)): 
    club = db.get(ClubDB, club_id) 
    if not club: 
        raise HTTPException(status_code=404, detail="Club not found") 
    return club 

#POST a new club
@app.post("/api/clubs", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club(payload: ClubCreate, db: Session = Depends(get_db)):
    club = ClubDB(**payload.model_dump())
    db.add(club)
    commit_or_rollback(db, "Club with this name or description may already exist")
    db.refresh(club)
    return club

#PATCH Club Info
@app.patch("/api/clubs/{club_id}", response_model=ClubRead)
def Update_Club_Info(club_id: int,payload: ClubUpdate,db: Session = Depends(get_db)):
    club = db.get(ClubDB, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(club, field, value)

    commit_or_rollback(db, "Club update failed, maybe duplicate name or description")
    db.refresh(club)
    return club

#PUT club information - updates all club attributes
@app.put("/api/clubs/{club_id}", response_model=ClubRead)
def Update_Full_Club_Info(club_id: int, payload: ClubCreate, db: Session = Depends(get_db)):
    club = db.get(ClubDB, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    for field_name, field_value in payload.model_dump().items():
        setattr(club, field_name, field_value)

    commit_or_rollback(db, "Club update failed, maybe duplicate name or descripion")
    return club


#DELETE Club 
@app.delete("/api/clubs/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
def Delete_Club(club_id: int, db: Session = Depends(get_db)) -> Response:
    club = db.get(ClubDB, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    db.delete(club)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# GET: All Memberships
@app.get("/api/memberships", response_model=list[MembershipRead]) 
def List_All_Memberships(db: Session = Depends(get_db)): 
    stmt = select(MembershipDB).order_by(MembershipDB.id) 
    return list(db.execute(stmt).scalars()) 

#POST new membership
@app.post("/api/memberships",response_model=MembershipReadWithClub,status_code=status.HTTP_201_CREATED)
def create_membership(payload: MembershipCreate, db: Session = Depends(get_db)):
    verify_user_exists(payload.user_id)
    # Ensure the club exists
    club = db.get(ClubDB, payload.club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Optional: prevent duplicate memberships for same user & club
    existing_stmt = select(MembershipDB).where(
        MembershipDB.user_id == payload.user_id,
        MembershipDB.club_id == payload.club_id,
    )
    existing = db.scalar(existing_stmt)
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member of this club")

    membership = MembershipDB(**payload.model_dump())
    db.add(membership)
    commit_or_rollback(db, "Could not create membership")

    # Reload with club relationship
    db.refresh(membership)
    membership = db.scalar(select(MembershipDB).options(selectinload(MembershipDB.club)).where(MembershipDB.id == membership.id))
    return membership

#PATC Membership info 
@app.patch("/api/memberships/{membership_id}", response_model=MembershipReadWithClub)
def update_membership(membership_id: int,payload: MembershipUpdate,db: Session = Depends(get_db)):

    membership = db.get(MembershipDB, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    update_data = payload.model_dump(exclude_unset=True)

    # If club_id is changed, ensure the new club exists
    if "club_id" in update_data:
        new_club = db.get(ClubDB, update_data["club_id"])
        if not new_club:
            raise HTTPException(status_code=404, detail="Club not found")

    for field, value in update_data.items():
        setattr(membership, field, value)

    commit_or_rollback(db, "Could not update membership")

    membership = db.scalar(select(MembershipDB).options(selectinload(MembershipDB.club)).where(MembershipDB.id == membership_id))
    return membership

 #DELETE Membership
@app.delete("/api/memberships/{membership_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_membership(membership_id: int, db: Session = Depends(get_db)) -> Response:
    membership = db.get(MembershipDB, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    db.delete(membership)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
