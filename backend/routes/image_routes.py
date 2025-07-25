from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.db import keywords_collection, images_collection
from models.image_model import ImageModel
from utils.image_search import ImageSearcher

image_bp = Blueprint('images', __name__)

@image_bp.route('/search-images/<keyword_id>', methods=['POST'])
def search_images(keyword_id):
    try:
        # Get keyword batch
        keyword_doc = keywords_collection.find_one({"_id": ObjectId(keyword_id)})
        
        if not keyword_doc:
            return jsonify({"error": "Keyword batch not found"}), 404
        
        # Check if images already searched
        existing_images = images_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if existing_images:
            return jsonify({"error": "Images already searched for this keyword batch"}), 400
        
        # Update status
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {"$set": {"status": "searching_images"}}
        )
        
        # Initialize image searcher
        searcher = ImageSearcher()
        
        # Search for images
        image_results = searcher.search_images_for_keywords(
            keyword_doc['main_keyword'],
            keyword_doc['keywords']
        )
        
        # Save image data
        image_doc = ImageModel.create_image_batch(keyword_id, image_results)
        result = images_collection.insert_one(image_doc)
        
        # Update keyword document
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {
                "$set": {
                    "status": "images_found",
                    "images_id": result.inserted_id
                }
            }
        )
        
        image_doc['_id'] = result.inserted_id
        response = ImageModel.format_image_response(image_doc)
        
        return jsonify({
            "message": "Images found successfully",
            "data": response,
            "total_images": image_results['total_images']
        }), 200
        
    except Exception as e:
        # Update status to failed
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {"$set": {"status": "image_search_failed"}}
        )
        return jsonify({"error": str(e)}), 500

@image_bp.route('/images/<keyword_id>', methods=['GET'])
def get_images(keyword_id):
    try:
        # Find images for this keyword batch
        image_doc = images_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        
        if not image_doc:
            return jsonify({"error": "No images found for this keyword batch"}), 404
        
        response = ImageModel.format_image_response(image_doc)
        
        return jsonify({"data": response}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500