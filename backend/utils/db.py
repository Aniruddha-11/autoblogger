from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGODB_URI)
db = client[Config.DATABASE_NAME]

# Collections
keywords_collection = db['keywords']
scraped_data_collection = db['scraped_data']
images_collection = db['images']
blogs_collection = db['blogs']
product_knowledge_collection = db['product_knowledge']
batch_jobs_collection = db['batch_jobs']  # Add this line

# Initialize product knowledge if not exists
from models.product_knowledge_model import ProductKnowledgeModel
if product_knowledge_collection.count_documents({}) == 0:
    default_knowledge = ProductKnowledgeModel.get_default_product_knowledge()
    product_knowledge_collection.insert_one(default_knowledge)