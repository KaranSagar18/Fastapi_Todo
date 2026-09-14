from pydantic import BaseModel , ConfigDict

class UserCreate(BaseModel):
    username : str
    password : str

class TaskCreate(BaseModel):
    title : str

class TaskResponse(BaseModel):
    id : int 
    title : str
    completed : bool
    owner_id : int

    model_config = ConfigDict(from_attributes = True)
    