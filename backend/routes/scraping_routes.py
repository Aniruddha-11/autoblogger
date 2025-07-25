from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.db import keywords_collection, scraped_data_collection
from models.scraped_data_model import ScrapedDataModel
from utils.scraper import WeldingScraper

scraping_bp = Blueprint('scraping', __name__)

@scraping_bp.route('/scrape/<keyword_id>', methods=['POST'])
def scrape_content(keyword_id):
    try:
        # Get keyword batch
        keyword_doc = keywords_collection.find_one({"_id": ObjectId(keyword_id)})
        
        if not keyword_doc:
            return jsonify({"error": "Keyword batch not found"}), 404
        
        # Check if already scraped
        if keyword_doc.get('status') == 'scraped':
            return jsonify({"error": "Content already scraped for this keyword batch"}), 400
        
        # Update status to scraping
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {"$set": {"status": "scraping"}}
        )
        
        # Initialize scraper
        scraper = WeldingScraper()
        
        # Perform scraping
        scraped_results = scraper.scrape_for_keywords(
            keyword_doc['main_keyword'],
            keyword_doc['keywords']
        )
        
        # Save scraped data
        scraped_doc = ScrapedDataModel.create_scraped_data(keyword_id, scraped_results)
        result = scraped_data_collection.insert_one(scraped_doc)
        
        # Update keyword document
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {
                "$set": {
                    "status": "scraped",
                    "scraped_data_id": result.inserted_id
                }
            }
        )
        
        scraped_doc['_id'] = result.inserted_id
        response = ScrapedDataModel.format_scraped_response(scraped_doc)
        
        return jsonify({
            "message": "Content scraped successfully",
            "data": response,
            "total_results": scraped_results['total_results']
        }), 200
        
    except Exception as e:
        # Update status to failed
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {"$set": {"status": "scraping_failed"}}
        )
        return jsonify({"error": str(e)}), 500

@scraping_bp.route('/scraped-data/<keyword_id>', methods=['GET'])
def get_scraped_data(keyword_id):
    try:
        # Find scraped data for this keyword batch
        scraped_doc = scraped_data_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        
        if not scraped_doc:
            return jsonify({"error": "No scraped data found for this keyword batch"}), 404
        
        response = ScrapedDataModel.format_scraped_response(scraped_doc)
        
        return jsonify({"data": response}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500