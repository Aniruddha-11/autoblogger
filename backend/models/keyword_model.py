from datetime import datetime
from bson import ObjectId

class KeywordModel:
    @staticmethod
    def create_keyword_batch(main_keyword, keywords):
        """Create a new keyword batch"""
        keyword_doc = {
            "main_keyword": main_keyword,
            "keywords": keywords,
            "created_at": datetime.utcnow(),
            "status": "created",
            "scraped_data_id": None,
            "blog_id": None,
            "images_id": None
        }
        return keyword_doc
    
    @staticmethod
    def format_keyword_response(keyword_doc):
        """Format keyword document for API response"""
        # Create a copy to avoid modifying original
        formatted = dict(keyword_doc)
        
        # Convert ObjectId fields to strings
        formatted['_id'] = str(keyword_doc['_id'])
        
        # Convert any ObjectId fields to strings
        if formatted.get('scraped_data_id'):
            formatted['scraped_data_id'] = str(formatted['scraped_data_id'])
        if formatted.get('blog_id'):
            formatted['blog_id'] = str(formatted['blog_id'])
        if formatted.get('images_id'):
            formatted['images_id'] = str(formatted['images_id'])
            
        # Format datetime
        if 'created_at' in formatted:
            formatted['created_at'] = formatted['created_at'].isoformat()
            
        return formatted