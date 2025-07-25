from datetime import datetime
from bson import ObjectId

class BlogModel:
    @staticmethod
    def create_blog_document(keyword_id, blog_data, html_content, original_html=None):
        """Create a new blog document"""
        blog_doc = {
            "keyword_id": ObjectId(keyword_id),
            "title": blog_data.get('title', ''),
            "h1": blog_data.get('h1', ''),
            "opening_paragraph": blog_data.get('opening_paragraph', ''),
            "subheadings": blog_data.get('subheadings', []),
            "content_sections": blog_data.get('content_sections', []),
            "cta": blog_data.get('cta', ''),
            "conclusion": blog_data.get('conclusion', ''),
            "html_content": html_content,
            "generation_step": blog_data.get('current_step', 'completed'),
            "created_at": datetime.utcnow(),
            "status": "draft"
        }
        
        # Add original HTML if provided
        if original_html:
            blog_doc["original_html"] = original_html
        
        return blog_doc
    
    @staticmethod
    def update_blog_step(blog_id, step_name, step_data):
        """Update a specific step in blog generation"""
        update_data = {
            f"steps.{step_name}": step_data,
            "updated_at": datetime.utcnow()
        }
        return update_data
    
    @staticmethod
    def format_blog_response(blog_doc):
        """Format blog document for API response"""
        blog_doc['_id'] = str(blog_doc['_id'])
        blog_doc['keyword_id'] = str(blog_doc['keyword_id'])
        blog_doc['created_at'] = blog_doc['created_at'].isoformat()
        return blog_doc