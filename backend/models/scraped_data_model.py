from datetime import datetime
from bson import ObjectId

class ScrapedDataModel:
    @staticmethod
    def create_scraped_data(keyword_id, scraped_content):
        """Create a new scraped data document"""
        scraped_doc = {
            "keyword_id": ObjectId(keyword_id),
            "content": scraped_content,
            "created_at": datetime.utcnow(),
            "status": "completed"
        }
        return scraped_doc
    
    @staticmethod
    def format_scraped_response(scraped_doc):
        """Format scraped document for API response"""
        scraped_doc['_id'] = str(scraped_doc['_id'])
        scraped_doc['keyword_id'] = str(scraped_doc['keyword_id'])
        scraped_doc['created_at'] = scraped_doc['created_at'].isoformat()
        return scraped_doc