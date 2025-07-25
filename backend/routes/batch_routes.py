from flask import Blueprint, request, jsonify, current_app
import pandas as pd
import os
import traceback
from datetime import datetime
from bson import ObjectId
import time
import threading
from utils.db import keywords_collection, batch_jobs_collection
from models.keyword_model import KeywordModel
import requests
import tempfile
from flask import send_file, Response
import io
import json
from bs4 import BeautifulSoup

batch_bp = Blueprint('batch', __name__)

# Store batch processing status in memory (use Redis in production)
batch_jobs = {}

class BatchProcessor:
    def __init__(self, job_id, excel_data, base_url):
        self.job_id = job_id
        self.excel_data = excel_data
        self.base_url = base_url
        self.total_keywords = len(excel_data)
        self.processed = 0
        self.failed = 0
        self.current_status = "starting"
        self.results = []
        
    def update_status(self, status, current_keyword="", error=None):
        try:
            batch_jobs[self.job_id] = {
                'status': status,
                'total_keywords': self.total_keywords,
                'processed': self.processed,
                'failed': self.failed,
                'current_keyword': current_keyword,
                'progress_percentage': round((self.processed / self.total_keywords) * 100, 2) if self.total_keywords > 0 else 0,
                'results': self.results,
                'error': error,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Also update in MongoDB
            batch_jobs_collection.update_one(
                {'job_id': self.job_id},
                {
                    '$set': {
                        'status': status,
                        'processed': self.processed,
                        'failed': self.failed,
                        'current_keyword': current_keyword,
                        'progress_percentage': round((self.processed / self.total_keywords) * 100, 2) if self.total_keywords > 0 else 0,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"Error updating status: {str(e)}")
    
    def process_single_keyword_set(self, main_keyword, subsidiary_keywords):
        """Process a single keyword set through the entire pipeline with detailed stage tracking"""
        try:
            print(f"Processing: {main_keyword} with keywords: {subsidiary_keywords}")
            
            # Step 1: Create keywords
            self.update_status_with_stage("processing", main_keyword, "🔧 Creating keyword batch...")
            
            try:
                keyword_response = requests.post(
                    f"{self.base_url}/api/keywords",
                    json={
                        'main_keyword': main_keyword,
                        'keywords': subsidiary_keywords
                    },
                    timeout=30
                )
                
                if keyword_response.status_code != 201:
                    raise Exception(f"Failed to create keywords: {keyword_response.text}")
                
                keyword_data = keyword_response.json()
                keyword_id = keyword_data['data']['_id']
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error creating keywords: {str(e)}")
            
            # Step 2: Scrape content
            self.update_status_with_stage("processing", main_keyword, "🔍 Scraping industry content...")
            try:
                scrape_response = requests.post(f"{self.base_url}/api/scrape/{keyword_id}", timeout=120)
                
                if scrape_response.status_code != 200:
                    raise Exception(f"Failed to scrape content: {scrape_response.text}")
                    
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error scraping content: {str(e)}")
            
            # Step 3: Search images
            self.update_status_with_stage("processing", main_keyword, "🖼️ Finding relevant images...")
            try:
                images_response = requests.post(f"{self.base_url}/api/search-images/{keyword_id}", timeout=60)
                
                if images_response.status_code != 200:
                    print(f"Warning: Image search failed for {main_keyword}: {images_response.text}")
                    # Continue without images
                    
            except requests.exceptions.RequestException as e:
                print(f"Warning: Network error searching images: {str(e)}")
                # Continue without images
            
            # Step 4: Generate blog (all steps with detailed tracking)
            self.update_status_with_stage("processing", main_keyword, "✍️ Generating blog content...")
            
            try:
                # Start blog generation
                start_response = requests.post(f"{self.base_url}/api/generate-blog/{keyword_id}/start", timeout=30)
                if start_response.status_code != 200:
                    raise Exception(f"Failed to start blog generation: {start_response.text}")
                
                # Execute all blog generation steps with individual stage updates
                blog_steps = [
                    ("title_tag", "📝 Creating SEO title..."),
                    ("h1_heading", "📋 Generating H1 heading..."),
                    ("opening_paragraph", "🎯 Writing opening paragraph..."),
                    ("subheadings", "📑 Creating subheadings..."),
                    ("content_sections", "📄 Writing content sections..."),
                    ("cta", "📢 Crafting call-to-action..."),
                    ("conclusion", "🏁 Writing conclusion..."),
                    ("quality_check", "🔍 Quality check & enhancement..."),
                    ("finalize", "✅ Finalizing blog...")
                ]
                
                for step_id, step_description in blog_steps:
                    self.update_status_with_stage("processing", main_keyword, step_description)
                    
                    step_response = requests.post(
                        f"{self.base_url}/api/generate-blog/{keyword_id}/step",
                        json={'step': step_id},
                        timeout=120
                    )
                    
                    if step_response.status_code != 200:
                        raise Exception(f"Failed at blog step {step_id}: {step_response.text}")
                    
                    # Brief pause between steps for UX
                    time.sleep(0.5)
                    
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error generating blog: {str(e)}")
            
            # Step 5: Integrate images (auto-select first 4)
            self.update_status_with_stage("processing", main_keyword, "🎨 Integrating images into blog...")
            try:
                integrate_response = requests.post(
                    f"{self.base_url}/api/integrate-images/{keyword_id}",
                    json={'selected_images': []},  # Auto-select
                    timeout=60
                )
                
                if integrate_response.status_code != 200:
                    print(f"Warning: Image integration failed for {main_keyword}: {integrate_response.text}")
                    # Continue without image integration
                    
            except requests.exceptions.RequestException as e:
                print(f"Warning: Network error integrating images: {str(e)}")
                # Continue without image integration
            
            # Step 6: Generate metadata
            self.update_status_with_stage("processing", main_keyword, "🏷️ Generating SEO metadata...")
            try:
                metadata_response = requests.post(f"{self.base_url}/api/generate-metadata/{keyword_id}", timeout=60)
                
                if metadata_response.status_code != 200:
                    raise Exception(f"Failed to generate metadata: {metadata_response.text}")
                    
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error generating metadata: {str(e)}")
            
            # Final success update
            self.update_status_with_stage("processing", main_keyword, "🎉 Blog completed successfully!")
            
            # Success
            self.processed += 1
            self.results.append({
                'main_keyword': main_keyword,
                'keyword_id': keyword_id,
                'status': 'success',
                'completed_at': datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.failed += 1
            error_msg = str(e)
            print(f"Error processing {main_keyword}: {error_msg}")
            
            self.results.append({
                'main_keyword': main_keyword,
                'status': 'failed',
                'error': error_msg,
                'failed_at': datetime.utcnow().isoformat()
            })
            
            return False
    
    def run_batch_processing(self):
        """Run the entire batch processing"""
        try:
            self.update_status("processing")
            
            for index, row in self.excel_data.iterrows():
                main_keyword = str(row.iloc[0]).strip()
                
                # Extract subsidiary keywords (columns 1-5, filter out empty ones)
                subsidiary_keywords = []
                for i in range(1, min(6, len(row))):  # Max 5 subsidiary keywords
                    if pd.notna(row.iloc[i]) and str(row.iloc[i]).strip():
                        subsidiary_keywords.append(str(row.iloc[i]).strip())
                
                if not main_keyword or len(subsidiary_keywords) < 4:
                    self.failed += 1
                    self.results.append({
                        'main_keyword': main_keyword,
                        'status': 'failed',
                        'error': 'Insufficient keywords (need main + 4-5 subsidiary)',
                        'failed_at': datetime.utcnow().isoformat()
                    })
                    continue
                
                # Process this keyword set
                success = self.process_single_keyword_set(main_keyword, subsidiary_keywords)
                
                # Small delay between keyword sets
                time.sleep(2)
            
            # Final status update
            if self.failed == 0:
                self.update_status("completed_successfully")
            else:
                self.update_status("completed_with_errors")
                
        except Exception as e:
            self.update_status("failed", error=str(e))
            print(f"Batch processing failed: {str(e)}")
            traceback.print_exc()
    def update_status_with_stage(self, status, current_keyword="", stage="", error=None):
        try:
            batch_jobs[self.job_id] = {
                'status': status,
                'total_keywords': self.total_keywords,
                'processed': self.processed,
                'failed': self.failed,
                'current_keyword': current_keyword,
                'current_stage': stage,  # Add current stage
                'progress_percentage': round((self.processed / self.total_keywords) * 100, 2) if self.total_keywords > 0 else 0,
                'results': self.results,
                'error': error,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Also update in MongoDB
            batch_jobs_collection.update_one(
                {'job_id': self.job_id},
                {
                    '$set': {
                        'status': status,
                        'processed': self.processed,
                        'failed': self.failed,
                        'current_keyword': current_keyword,
                        'current_stage': stage,
                        'progress_percentage': round((self.processed / self.total_keywords) * 100, 2) if self.total_keywords > 0 else 0,
                        'updated_at': datetime.utcnow()
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"Error updating status: {str(e)}")
@batch_bp.route('/batch-upload', methods=['POST'])
def upload_excel_batch():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
        
        # Save uploaded file to temporary directory
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            file.save(temp_file.name)
            temp_filepath = temp_file.name
        
        # Read Excel file
        try:
            df = pd.read_excel(temp_filepath, header=None)  # No headers expected
        except Exception as e:
            os.unlink(temp_filepath)  # Clean up temp file
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        finally:
            # Clean up temporary file if it still exists
            if os.path.exists(temp_filepath):
                try:
                    os.unlink(temp_filepath)
                except:
                    pass
        
        # Validate data
        if df.empty:
            return jsonify({'error': 'Excel file is empty'}), 400
        
        if len(df.columns) < 5:
            return jsonify({'error': 'Excel file should have at least 5 columns (1 main keyword + 4 subsidiary keywords)'}), 400
        
        # Create batch job
        job_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(ObjectId())}"
        
        # Get base URL for internal API calls
        base_url = request.url_root.rstrip('/')
        
        # Initialize batch job in database
        batch_job_doc = {
            'job_id': job_id,
            'filename': file.filename,
            'total_keywords': len(df),
            'status': 'queued',
            'created_at': datetime.utcnow(),
            'processed': 0,
            'failed': 0
        }
        batch_jobs_collection.insert_one(batch_job_doc)
        
        # Create processor
        processor = BatchProcessor(job_id, df, base_url)
        
        # Start processing in background thread
        thread = threading.Thread(target=processor.run_batch_processing)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Batch processing started',
            'job_id': job_id,
            'total_keywords': len(df),
            'status': 'queued'
        }), 200
        
    except Exception as e:
        print(f"Error in batch upload: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@batch_bp.route('/batch-status/<job_id>', methods=['GET'])
def get_batch_status(job_id):
    try:
        if job_id in batch_jobs:
            return jsonify(batch_jobs[job_id]), 200
        
        # Check database if not in memory
        batch_doc = batch_jobs_collection.find_one({'job_id': job_id})
        if batch_doc:
            batch_doc['_id'] = str(batch_doc['_id'])
            batch_doc['created_at'] = batch_doc['created_at'].isoformat()
            if 'updated_at' in batch_doc:
                batch_doc['updated_at'] = batch_doc['updated_at'].isoformat()
            return jsonify(batch_doc), 200
        
        return jsonify({'error': 'Batch job not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@batch_bp.route('/batch-results/<job_id>', methods=['GET'])
def get_batch_results(job_id):
    try:
        if job_id in batch_jobs:
            job_data = batch_jobs[job_id]
            return jsonify({
                'job_id': job_id,
                'status': job_data['status'],
                'total_keywords': job_data['total_keywords'],
                'processed': job_data['processed'],
                'failed': job_data['failed'],
                'results': job_data['results']
            }), 200
        
        return jsonify({'error': 'Batch job not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@batch_bp.route('/batch-jobs', methods=['GET'])
def get_all_batch_jobs():
    try:
        jobs = list(batch_jobs_collection.find().sort('created_at', -1).limit(20))
        
        formatted_jobs = []
        for job in jobs:
            try:
                job['_id'] = str(job['_id'])
                job['created_at'] = job['created_at'].isoformat()
                if 'updated_at' in job:
                    job['updated_at'] = job['updated_at'].isoformat()
                formatted_jobs.append(job)
            except Exception as e:
                print(f"Error formatting job {job.get('_id')}: {str(e)}")
                continue
        
        return jsonify({'data': formatted_jobs}), 200
        
    except Exception as e:
        print(f"Error in get_all_batch_jobs: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@batch_bp.route('/batch-download-blog/<keyword_id>/<format>', methods=['GET'])
def download_batch_blog(keyword_id, format='html'):
    """Download individual blog from batch processing"""
    try:
        from utils.db import blogs_collection
        
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        if format == 'html':
            # Get the publish-ready HTML
            html_content = (
                blog_doc.get("publish_ready_html") or 
                blog_doc.get("html_with_images") or
                blog_doc.get("enhanced_html") or
                blog_doc.get("html_content", "")
            )

            if not html_content:
                return jsonify({"error": "Blog not ready for download"}), 400

            # Create filename from slug or title
            filename = f"{blog_doc.get('slug', blog_doc.get('title', 'blog'))}.html"
            
            return Response(
                html_content,
                mimetype="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/html; charset=utf-8",
                },
            )

        elif format == 'txt':
            # Convert HTML to plain text
            html_content = (
                blog_doc.get("publish_ready_html") or 
                blog_doc.get("html_with_images") or
                blog_doc.get("enhanced_html") or
                blog_doc.get("html_content", "")
            )
            
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract text content
            text_content = (
                f"POST TITLE: {blog_doc.get('post_title', blog_doc.get('title', ''))}\n"
                f"META TITLE: {blog_doc.get('meta_title', '')}\n"
                f"META DESCRIPTION: {blog_doc.get('meta_description', '')}\n"
                f"POST DESCRIPTION: {blog_doc.get('post_description', '')}\n"
                f"SLUG: {blog_doc.get('slug', '')}\n"
                f"FEATURED IMAGE: {blog_doc.get('featured_image', {}).get('url', '')}\n"
                f"KEYWORDS: {blog_doc.get('meta_keywords', '')}\n\n"
                "=====================================\n"
                "BLOG CONTENT\n"
                "=====================================\n\n"
                + soup.get_text(separator="\n", strip=True)
            )

            filename = f"{blog_doc.get('slug', blog_doc.get('title', 'blog'))}.txt"

            return Response(
                text_content,
                mimetype="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/plain; charset=utf-8",
                },
            )

        elif format == 'json':
            # Return all metadata as JSON
            metadata = {
                "post_title": blog_doc.get("post_title", blog_doc.get("title", "")),
                "meta_title": blog_doc.get("meta_title", ""),
                "meta_description": blog_doc.get("meta_description", ""),
                "post_description": blog_doc.get("post_description", ""),
                "slug": blog_doc.get("slug", ""),
                "featured_image": blog_doc.get("featured_image", {}),
                "meta_keywords": blog_doc.get("meta_keywords", ""),
                "author": blog_doc.get("author", ""),
                "canonical_url": blog_doc.get("canonical_url", ""),
                "word_count": blog_doc.get("word_count", 0),
                "html_content": (
                    blog_doc.get("publish_ready_html") or 
                    blog_doc.get("html_with_images") or
                    blog_doc.get("enhanced_html") or
                    blog_doc.get("html_content", "")
                ),
                "created_at": blog_doc.get("created_at", "").isoformat() if blog_doc.get("created_at") else "",
                "status": blog_doc.get("status", "")
            }

            filename = f"{blog_doc.get('slug', blog_doc.get('title', 'blog'))}.json"

            return Response(
                json.dumps(metadata, indent=2),
                mimetype="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/json; charset=utf-8",
                },
            )
            
        else:
            return jsonify({"error": "Invalid format. Use 'html', 'txt', or 'json'"}), 400

    except Exception as e:
        print(f"Error downloading batch blog: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@batch_bp.route('/batch-blog-preview/<keyword_id>', methods=['GET'])
def preview_batch_blog(keyword_id):
    """Get blog preview for batch processing"""
    try:
        from utils.db import blogs_collection
        
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        # Get the best available HTML
        html_content = (
            blog_doc.get("publish_ready_html") or 
            blog_doc.get("html_with_images") or
            blog_doc.get("enhanced_html") or
            blog_doc.get("html_content", "")
        )

        # Get blog metadata
        metadata = {
            "title": blog_doc.get("post_title", blog_doc.get("title", "")),
            "meta_title": blog_doc.get("meta_title", ""),
            "slug": blog_doc.get("slug", ""),
            "word_count": blog_doc.get("word_count", 0),
            "status": blog_doc.get("status", ""),
            "created_at": blog_doc.get("created_at", "").isoformat() if blog_doc.get("created_at") else "",
            "has_images": blog_doc.get("image_integration_complete", False),
            "images_count": len(blog_doc.get("integrated_images", [])),
        }

        return jsonify({
            "html": html_content,
            "metadata": metadata,
            "ready_for_download": bool(html_content)
        }), 200

    except Exception as e:
        print(f"Error previewing batch blog: {str(e)}")
        return jsonify({"error": str(e)}), 500
