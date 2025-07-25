from datetime import datetime
from bson import ObjectId

class ImageModel:
    @staticmethod
    def create_image_batch(keyword_id, images_data):
        """Create a new image batch document"""
        image_doc = {
            "keyword_id": ObjectId(keyword_id),
            "images": images_data,
            "created_at": datetime.utcnow(),
            "status": "completed"
        }
        return image_doc
    
    @staticmethod
    def format_image_response(image_doc):
        """Format image document for API response"""
        image_doc['_id'] = str(image_doc['_id'])
        image_doc['keyword_id'] = str(image_doc['keyword_id'])
        image_doc['created_at'] = image_doc['created_at'].isoformat()
        return image_doc