from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base

class User(Base):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True, index=True)
    username : Mapped[str] = mapped_column(unique = True, index = True)
    hashed_password : Mapped[str] = mapped_column()

    tasks : Mapped[list[Task]] = relationship(back_populates="owner")
    

class Task(Base):
    __tablename__ = "tasks"
    id : Mapped[int] = mapped_column(primary_key = True, index= True)
    title : Mapped [str] = mapped_column(index=True)
    completed : Mapped[bool]= mapped_column(default= False)
    owner_id : Mapped[int] = mapped_column(ForeignKey("users.id"))

    owner : Mapped[User] = relationship(back_populates="tasks")