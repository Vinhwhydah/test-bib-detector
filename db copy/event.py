from db.db import get_database
from pydantic import BaseModel
from typing import Optional
import bson

db = get_database()
event_collection = db['events']


class EventEntity(BaseModel):
    _id: bson.ObjectId
    status: str
    user_id: bson.ObjectId
    partner_event_id: Optional[str]
    created_by: Optional[str]

    class Config:
        arbitrary_types_allowed = True


def find_event_by_id(event_id: str) -> EventEntity:
    result = event_collection.find_one({'_id': bson.ObjectId(event_id)})

    return EventEntity.parse_obj(result)
