import certifi
from pymongo import MongoClient
from dotenv import load_dotenv
import os


load_dotenv()
mongo_connection = os.environ.get('MONGO_URL')
db = os.environ.get('DB_NAME')


def get_database():
    client = MongoClient(mongo_connection, tlsCAFile=certifi.where())
    return client[db]