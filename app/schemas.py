from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, Field, StringConstraints, ConfigDict 

ClubNameStr = Annotated[str, StringConstraints(min_length=3, max_length=100)]
CategoryStr = Annotated[str,StringConstraints(pattern=r"^(club|society)$", to_lower=True,)] #only allows club or society, to_lower changes any input to  lower case
DescriptionStr = Annotated[str, StringConstraints(min_length=10, max_length=255)]
MembershipCostInt =  Annotated[int, Ge(0), Le(150)]

#----------- Club Schemas --------------

class ClubCreate(BaseModel):
    name: ClubNameStr
    description: DescriptionStr
    category: CategoryStr
    membership_cost: MembershipCostInt

class ClubRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    name: ClubNameStr
    description: DescriptionStr
    category: CategoryStr
    membership_cost: MembershipCostInt    

class ClubUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    membership_cost: Optional[int] = None

#---------- Membership Schemas ----------

class MembershipCreate(BaseModel):
    user_id: int
    club_id: int

class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    club_id: int

class MembershipUpdate(BaseModel):
    user_id: Optional[int] = None
    club_id: Optional[int] = None

class MembershipReadWithClub(MembershipRead):
    club: Optional[ClubRead] = None   
