from db.db import get_database
from pydantic import BaseModel
import bson

db = get_database()
partner_collection = db['partners']


class PartnerEntity(BaseModel):
    _id: bson.ObjectId
    secret_key: str
    name: str
    ping_notify_url: str
    admin_id: str

    class Config:
        arbitrary_types_allowed = True


def find_partner_by(partner_id: str) -> PartnerEntity:
    result = partner_collection.find_one({'name': partner_id})

    return PartnerEntity.parse_obj(result)
