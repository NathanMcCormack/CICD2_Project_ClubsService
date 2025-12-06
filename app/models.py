from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship 
from sqlalchemy import String, Integer, ForeignKey

class Base(DeclarativeBase): 
    pass 


class ClubDB(Base): 
    __tablename__ = "clubs" 
    id: Mapped[int] = mapped_column(primary_key=True, index=True) 
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False) 
    description: Mapped[str] = mapped_column(String, unique=True, nullable=False) 
    category: Mapped[str] = mapped_column(String, nullable=False)  #"club" or "society"
    membership_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    memberships: Mapped[list["MembershipDB"]] = relationship(back_populates="club",cascade="all, delete-orphan")


class MembershipDB(Base):
    __tablename__ = "memberships"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False) #from User MS
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"),nullable=False,)
    club: Mapped["ClubDB"] = relationship(back_populates="memberships")