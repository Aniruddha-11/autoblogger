from flask import Blueprint, request, jsonify
from utils.db import keywords_collection
from models.keyword_model import KeywordModel
from bson import ObjectId
import traceback

keyword_bp = Blueprint('keywords', __name__)

@keyword_bp.route('/keywords', methods=['POST'])
def create_keywords():
    try:
        data = request.json
        main_keyword = data.get('main_keyword')
        keywords = data.get('keywords', [])
        
        # Validation
        if not main_keyword:
            return jsonify({"error": "Main keyword is required"}), 400
        
        if not keywords or len(keywords) < 4 or len(keywords) > 5:
            return jsonify({"error": "Please provide 4-5 keywords"}), 400
        
        # Create keyword batch
        keyword_doc = KeywordModel.create_keyword_batch(main_keyword, keywords)
        
        # Save to MongoDB
        result = keywords_collection.insert_one(keyword_doc)
        keyword_doc['_id'] = result.inserted_id
        
        # Format response
        response = KeywordModel.format_keyword_response(keyword_doc)
        
        return jsonify({
            "message": "Keywords saved successfully",
            "data": response
        }), 201
        
    except Exception as e:
        print(f"Error in create_keywords: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@keyword_bp.route('/keywords/<keyword_id>', methods=['GET'])
def get_keyword_batch(keyword_id):
    try:
        keyword_doc = keywords_collection.find_one({"_id": ObjectId(keyword_id)})
        
        if not keyword_doc:
            return jsonify({"error": "Keyword batch not found"}), 404
        
        response = KeywordModel.format_keyword_response(keyword_doc)
        
        return jsonify({"data": response}), 200
        
    except Exception as e:
        print(f"Error in get_keyword_batch: {str(e)}")
        return jsonify({"error": str(e)}), 500

@keyword_bp.route('/keywords', methods=['GET'])
def get_all_keywords():
    try:
        keyword_docs = list(keywords_collection.find().sort("created_at", -1).limit(20))
        
        formatted_docs = []
        for doc in keyword_docs:
            try:
                formatted_doc = KeywordModel.format_keyword_response(doc)
                formatted_docs.append(formatted_doc)
            except Exception as e:
                print(f"Error formatting document {doc.get('_id')}: {str(e)}")
                continue
        
        return jsonify({"data": formatted_docs}), 200
        
    except Exception as e:
        print(f"Error in get_all_keywords: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500