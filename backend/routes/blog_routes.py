from flask import Blueprint, request, jsonify
from bson import ObjectId
from utils.db import (
    keywords_collection,
    scraped_data_collection,
    blogs_collection,
    product_knowledge_collection,
    images_collection,
)
from models.blog_model import BlogModel
from utils.llm_generator import BlogGenerator
import traceback
from datetime import datetime,timedelta
from bs4 import BeautifulSoup
import re
import time 

blog_bp = Blueprint("blog", __name__)

# Store generation sessions in memory (in production, use Redis)
generation_sessions = {}


@blog_bp.route("/generate-blog/<keyword_id>/start", methods=["POST"])
def start_blog_generation(keyword_id):
    try:
        keyword_doc = keywords_collection.find_one({"_id": ObjectId(keyword_id)})
        if not keyword_doc:
            return jsonify({"error": "Keyword batch not found"}), 404

        scraped_doc = scraped_data_collection.find_one(
            {"keyword_id": ObjectId(keyword_id)}
        )
        if not scraped_doc:
            return (
                jsonify(
                    {"error": "No scraped data found. Please complete scraping first."}
                ),
                400,
            )

        session_id = f"{keyword_id}_blog_{int(time.time())}"
        
        # Store session in database instead of memory
        session_data = {
            "_id": session_id,
            "keyword_id": keyword_id,
            "main_keyword": keyword_doc["main_keyword"],
            "keywords": keyword_doc["keywords"],
            "scraped_content": scraped_doc["content"],
            "current_step": 1,
            "blog_data": {},
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=2)  # 2 hour expiry
        }
        
        # Use a sessions collection in MongoDB
        from utils.db import db
        sessions_collection = db['generation_sessions']
        sessions_collection.insert_one(session_data)

        return (
            jsonify(
                {
                    "message": "Blog generation started",
                    "session_id": session_id,
                    "current_step": 1,
                    "next_step": "title_tag",
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error starting blog generation: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@blog_bp.route("/generate-blog/<keyword_id>/step", methods=["POST"])
def generate_blog_step(keyword_id):
    try:
        data = request.json
        step = data.get("step")
        session_id = data.get("session_id")
        
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400

        # Get session from database instead of memory
        from utils.db import db
        sessions_collection = db['generation_sessions']
        session_doc = sessions_collection.find_one({"_id": session_id})
        
        if not session_doc:
            return jsonify({"error": "No active generation session found"}), 400
            
        # Check if session expired
        if session_doc.get("expires_at") and session_doc["expires_at"] < datetime.utcnow():
            sessions_collection.delete_one({"_id": session_id})
            return jsonify({"error": "Generation session expired"}), 400

        # Convert database document to session format
        session = {
            "keyword_id": session_doc["keyword_id"],
            "main_keyword": session_doc["main_keyword"],
            "keywords": session_doc["keywords"],
            "scraped_content": session_doc["scraped_content"],
            "current_step": session_doc["current_step"],
            "blog_data": session_doc["blog_data"]
        }

        generator = BlogGenerator()
        result = {}

        if step == "title_tag":
            title = generator.generate_title_tag(
                session["main_keyword"], session["keywords"], session["scraped_content"]
            )
            session["blog_data"]["title"] = title
            result = {"title": title}
            session["current_step"] = 2

        elif step == "h1_heading":
            if "title" not in session["blog_data"]:
                return jsonify({"error": "Title must be generated first"}), 400

            h1 = generator.generate_h1_heading(
                session["blog_data"]["title"], session["main_keyword"]
            )
            session["blog_data"]["h1"] = h1
            result = {"h1": h1}
            session["current_step"] = 3

        elif step == "opening_paragraph":
            if "h1" not in session["blog_data"]:
                return jsonify({"error": "H1 must be generated first"}), 400

            opening = generator.generate_opening_paragraph(
                session["blog_data"]["title"],
                session["blog_data"]["h1"],
                session["main_keyword"],
                session["scraped_content"],
            )
            session["blog_data"]["opening_paragraph"] = opening
            result = {"opening_paragraph": opening}
            session["current_step"] = 4

        elif step == "subheadings":
            subheadings = generator.generate_subheadings(
                session["blog_data"]["title"],
                session["main_keyword"],
                session["keywords"],
            )
            session["blog_data"]["subheadings"] = subheadings
            result = {"subheadings": subheadings}
            session["current_step"] = 5

        elif step == "content_sections":
            if "subheadings" not in session["blog_data"]:
                return jsonify({"error": "Subheadings must be generated first"}), 400

            content_sections = []
            scraped_snippets = []

            # Extract snippets from scraped content
            if (
                session["scraped_content"]
                and "scraped_data" in session["scraped_content"]
            ):
                for keyword_data in session["scraped_content"]["scraped_data"].values():
                    if isinstance(keyword_data, list):
                        for item in keyword_data:
                            if "snippet" in item:
                                scraped_snippets.append(item["snippet"])

            # Calculate word distribution
            # Opening: 150-200, Conclusion: 150-200, CTA: 150-200
            # Remaining for content sections: 1200-1400 words
            num_sections = len(session["blog_data"]["subheadings"])
            words_per_section = (
                350 if num_sections == 4 else 300
            )  # Aim for 300-350 per section

            # Generate each section with proper keywords
            keywords = session.get("keywords", [])

            for i, subheading in enumerate(session["blog_data"]["subheadings"]):
                # Use different context for each section
                context = (
                    " ".join(scraped_snippets[i * 2 : (i + 1) * 2])
                    if scraped_snippets
                    else ""
                )

                # Assign keywords to sections
                section_keywords = [session["main_keyword"]]
                if i < len(keywords):
                    section_keywords.append(keywords[i])

                content = generator.generate_content_section(
                    subheading,
                    context,
                    session["main_keyword"],
                    section_keywords,
                    word_target=words_per_section,
                )

                # Add outbound links to some sections
                if i % 2 == 1:  # Every other section
                    content = generator.add_outbound_links(content)

                content_sections.append(content)

            session["blog_data"]["content_sections"] = content_sections
            result = {"content_sections": content_sections}
            session["current_step"] = 6

        elif step == "cta":
            cta = generator.generate_cta(
                session["main_keyword"], session["blog_data"]["title"]
            )
            session["blog_data"]["cta"] = cta
            result = {"cta": cta}
            session["current_step"] = 7

        elif step == "conclusion":
            conclusion = generator.generate_conclusion(
                session["blog_data"]["title"],
                session["main_keyword"],
                session["blog_data"]["subheadings"],
            )
            session["blog_data"]["conclusion"] = conclusion
            result = {"conclusion": conclusion}
            session["current_step"] = 8

        elif step == "quality_check":
            if "conclusion" not in session["blog_data"]:
                return jsonify({"error": "All content must be generated first"}), 400

            keywords = session.get("keywords", [])

            quality_result = generator.generate_quality_check_step(
                session["blog_data"], session["main_keyword"], keywords
            )

            # Store HTML versions in session for database storage
            session["original_html"] = quality_result["original_html"]
            session["enhanced_html"] = quality_result["enhanced_html"]

            if quality_result["enhancement_done"]:
                session["blog_data"] = quality_result["enhanced_blog_data"]
                session["blog_data"]["quality_enhanced"] = True
                session["blog_data"]["word_count"] = quality_result["final_word_count"]

            result = {
                "quality_report": quality_result["original_report"],
                "enhanced_report": quality_result["enhanced_report"],
                "enhancement_done": quality_result["enhancement_done"],
                "final_word_count": quality_result["final_word_count"],
                "topic_complexity": quality_result["original_report"].get(
                    "topic_complexity", "unknown"
                ),
                "target_range": f"{quality_result['enhanced_report'].get('min_words', 0)}-{quality_result['enhanced_report'].get('target_words', 0)} words",
            }

            session["current_step"] = 9

        elif step == "finalize":
            html_content = session.get(
                "enhanced_html"
            ) or generator.generate_simple_html(session["blog_data"])
            original_html = session.get("original_html")

            blog_doc = BlogModel.create_blog_document(
                keyword_id, session["blog_data"], html_content, original_html
            )

            result_doc = blogs_collection.insert_one(blog_doc)

            keywords_collection.update_one(
                {"_id": ObjectId(keyword_id)},
                {
                    "$set": {
                        "blog_id": result_doc.inserted_id,
                        "status": "blog_generated",
                        "final_word_count": session["blog_data"].get("word_count", 0),
                    }
                },
            )

            # Clean up session from database after finalization
            sessions_collection.delete_one({"_id": session_id})

            blog_doc["_id"] = result_doc.inserted_id
            formatted_blog = BlogModel.format_blog_response(blog_doc)

            result = {
                "message": "Blog generated successfully",
                "blog": formatted_blog,
                "has_original_version": bool(original_html),
            }

        else:
            return jsonify({"error": "Invalid step"}), 400

        # Update session in database after each step (except finalize which deletes it)
        if step != "finalize":
            update_data = {
                "blog_data": session["blog_data"],
                "current_step": session["current_step"],
                "updated_at": datetime.utcnow()
            }
            
            # Include HTML versions if they exist (for quality_check step)
            if "original_html" in session:
                update_data["original_html"] = session["original_html"]
            if "enhanced_html" in session:
                update_data["enhanced_html"] = session["enhanced_html"]
                
            sessions_collection.update_one(
                {"_id": session_id},
                {"$set": update_data}
            )

        return (
            jsonify(
                {
                    "result": result,
                    "current_step": session.get("current_step", 8),
                    "session_id": session_id,
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error in blog generation step: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@blog_bp.route("/blog/<keyword_id>", methods=["GET"])
def get_blog(keyword_id):
    try:
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})

        if not blog_doc:
            return jsonify({"error": "No blog found for this keyword batch"}), 404

        response = BlogModel.format_blog_response(blog_doc)

        return jsonify({"data": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blog_bp.route("/integrate-images/<keyword_id>", methods=["POST"])
def integrate_images(keyword_id):
    try:
        data = request.json
        selected_image_ids = data.get("selected_images", [])

        # Get the blog document
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        # Get the images document from MongoDB
        images_doc = images_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not images_doc:
            return jsonify({"error": "Images not found"}), 404

        # Debug: Print the structure
        print(f"Images document structure: {images_doc.keys()}")
        if "images" in images_doc:
            print(f"Images field type: {type(images_doc['images'])}")
            if isinstance(images_doc["images"], dict):
                print(f"Images keys: {images_doc['images'].keys()}")

        # Extract all images - handle MongoDB structure
        all_images = []

        # The structure appears to be: images_doc['images']['images']['main'], etc.
        if "images" in images_doc:
            images_data = images_doc["images"]

            # Check if it's nested
            if isinstance(images_data, dict) and "images" in images_data:
                # It's nested: images.images.{keyword}
                for keyword, keyword_images in images_data["images"].items():
                    if isinstance(keyword_images, list):
                        for idx, img in enumerate(keyword_images):
                            if isinstance(img, dict):
                                # Generate better alt text based on context
                                keyword_clean = keyword.replace("_", " ").replace(
                                    "-", " "
                                )

                                # Check multiple fields for alt text
                                alt_text = (
                                    img.get("alt_text", "")
                                    or img.get("title", "")
                                    or img.get("alt", "")
                                    or img.get("description", "")
                                )

                                # If still no alt text, generate contextual one
                                if not alt_text:
                                    # Generate generic contextual alt text
                                    if keyword == "main":
                                        alt_text = f"{keyword_clean} illustration"
                                    else:
                                        alt_text = f"{keyword_clean.title()} concept image"

                                # Clean up the alt text
                                alt_text = alt_text.strip()
                                if len(alt_text) > 100:
                                    alt_text = alt_text[:97] + "..."

                                processed_img = {
                                    "url": img.get("url", ""),
                                    "alt_text": alt_text,
                                    "title": img.get("title", "") or alt_text,
                                    "source": img.get("source", "Web"),
                                    "keyword_context": keyword,
                                    "unique_id": f"{img.get('url', '')}_{keyword}_{idx}",
                                }
                                if processed_img["url"]:
                                    all_images.append(processed_img)
                                    print(
                                        f"Added image from {keyword}: {processed_img['url'][:50]}..."
                                    )

        print(f"Total images extracted: {len(all_images)}")

        # Select images
        if selected_image_ids and len(selected_image_ids) > 0:
            selected_images = [
                img for img in all_images if img["unique_id"] in selected_image_ids
            ]
        else:
            # Auto-select first 4 images
            selected_images = all_images[:4]

        print(f"Selected {len(selected_images)} images for integration")

        # Get the HTML content - try different fields
        html_content = (
            blog_doc.get("html_with_images")
            or blog_doc.get("enhanced_html")
            or blog_doc.get("html_content")
            or blog_doc.get("original_html", "")
        )

        if not html_content:
            return jsonify({"error": "No HTML content found in blog"}), 400

        # Integrate images
        html_with_images = integrate_images_into_html_v2(html_content, selected_images)

        # Save the updated HTML
        update_result = blogs_collection.update_one(
            {"_id": blog_doc["_id"]},
            {
                "$set": {
                    "html_with_images": html_with_images,
                    "integrated_images": selected_images,
                    "image_integration_complete": True,
                    "status": "images_integrated",
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        print(f"Blog updated: {update_result.modified_count} document(s) modified")

        # Update keyword status
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)}, {"$set": {"status": "images_integrated"}}
        )

        return (
            jsonify(
                {
                    "message": "Images integrated successfully",
                    "html_preview": html_with_images,
                    "images_used": len(selected_images),
                    "image_urls": [img["url"] for img in selected_images],
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error integrating images: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def integrate_images_into_html_v2(html_content, selected_images):
    """Image integration with proper alt text and captions for ALL images"""
    if not selected_images:
        print("No images to integrate")
        # Remove image placeholders if no images available
        html_content = re.sub(r'\[Featured Image\]', 'Featured image not available', html_content)
        html_content = re.sub(r'\[Content Image \d+\]', 'Content image not available', html_content)
        html_content = re.sub(r'\[Image \d+\]', 'Image not available', html_content)
        return html_content

    html = html_content
    images_replaced = set()

    # Image 1: Featured Image
    if len(selected_images) > 0 and "featured" not in images_replaced:
        img = selected_images[0]
        
        # Validate image URL
        if img.get('url') and img['url'].strip():
            alt_text = (
                img.get("alt_text", "")
                or img.get("title", "")
                or f"{img.get('keyword_context', 'featured')} image"
            )

            featured_html = f"""<figure class="featured-image">
<img src="{img['url']}" alt="{alt_text}" loading="lazy" onerror="this.style.display='none'">
<figcaption>{alt_text}</figcaption>
</figure>"""
        else:
            # If no valid URL, show placeholder
            featured_html = """<figure class="featured-image">
<div style="background-color: #f0f0f0; padding: 100px; text-align: center; color: #999;">Featured Image</div>
</figure>"""

        patterns_to_try = [
            (r"\[Featured Image\]", featured_html),
            (
                r'<figure class="featured-image">\s*\[Featured Image\]\s*</figure>',
                featured_html,
            ),
            (r"<div[^>]*>\s*\[Featured Image[^\]]*\]\s*</div>", featured_html),
        ]

        for pattern, replacement in patterns_to_try:
            new_html = re.sub(
                pattern, replacement, html, count=1, flags=re.IGNORECASE | re.DOTALL
            )
            if new_html != html:
                html = new_html
                images_replaced.add("featured")
                print(f"Replaced featured image with alt: {alt_text if img.get('url') else 'placeholder'}")
                break

    # Similar validation for other images...
    # Rest of the function continues with similar URL validation

    # Images 2-3: Content Images
    content_image_count = 0
    for i in range(1, min(len(selected_images), 3)):
        if f"content_{i}" in images_replaced:
            continue

        img = selected_images[i]
        alt_text = (
            img.get("alt_text", "")
            or img.get("title", "")
            or f"{img.get('keyword_context', 'welding')} technology"
        )

        content_html = f"""<figure class="content-image">
<img src="{img['url']}" alt="{alt_text}" loading="lazy">
<figcaption>{alt_text}</figcaption>
</figure>"""

        patterns_to_try = [
            (rf"\[Content Image {content_image_count + 1}\]", content_html),
            (
                rf'<figure class="content-image">\s*\[Content Image {content_image_count + 1}\]\s*</figure>',
                content_html,
            ),
            (rf"\[Image {content_image_count + 1}\]", content_html),
        ]

        replaced = False
        for pattern, replacement in patterns_to_try:
            new_html = re.sub(
                pattern, replacement, html, count=1, flags=re.IGNORECASE | re.DOTALL
            )
            if new_html != html:
                html = new_html
                content_image_count += 1
                images_replaced.add(f"content_{i}")
                print(
                    f"Replaced content image {content_image_count} with alt: {alt_text}"
                )
                replaced = True
                break

        if not replaced and f"content_{i}" not in images_replaced:
            h2_positions = list(re.finditer(r"</h2>", html))
            if len(h2_positions) >= (content_image_count + 1) * 2:
                insert_pos = h2_positions[(content_image_count + 1) * 2 - 1].end()
                next_section = re.search(r"<h2|<section|</article", html[insert_pos:])
                if next_section:
                    insert_pos += next_section.start()
                    html = (
                        html[:insert_pos]
                        + "\n"
                        + content_html
                        + "\n"
                        + html[insert_pos:]
                    )
                    content_image_count += 1
                    images_replaced.add(f"content_{i}")
                    print(
                        f"Inserted content image {content_image_count} with alt: {alt_text}"
                    )

    # Image 4: Before CTA - WITH CAPTION
    if len(selected_images) > 3 and "cta" not in images_replaced:
        img = selected_images[3]
        alt_text = (
            img.get("alt_text", "")
            or img.get("title", "")
            or "Smart welding technology in action"
        )

        # CTA image WITH caption
        cta_html = f"""<figure class="cta-image">
<img src="{img['url']}" alt="{alt_text}" loading="lazy">
<figcaption>{alt_text}</figcaption>
</figure>"""

        cta_pattern = r'<section class="cta-section">'
        if re.search(cta_pattern, html):
            html = re.sub(
                cta_pattern,
                cta_html + "\n" + r'<section class="cta-section">',
                html,
                count=1,
            )
            images_replaced.add("cta")
            print(f"Inserted CTA image with alt: {alt_text}")

    # Clean up any duplicate figures
    html = clean_duplicate_images(html)

    return html


def clean_duplicate_images(html):
    """Remove duplicate consecutive image figures"""
    # Pattern to find consecutive identical figures
    pattern = r"(<figure[^>]*>.*?</figure>)\s*\1"

    # Keep removing duplicates until none are found
    while re.search(pattern, html, re.DOTALL):
        html = re.sub(pattern, r"\1", html, flags=re.DOTALL)

    return html


# Add a route to check current blog status with images
@blog_bp.route("/blog-with-images/<keyword_id>", methods=["GET"])
def get_blog_with_images(keyword_id):
    try:
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        # Get the best available HTML
        html_content = (
            blog_doc.get("publish_ready_html")
            or blog_doc.get("html_with_images")
            or blog_doc.get("enhanced_html")
            or blog_doc.get("html_content", "")
        )

        return (
            jsonify(
                {
                    "html": html_content,
                    "has_images": blog_doc.get("image_integration_complete", False),
                    "integrated_images": blog_doc.get("integrated_images", []),
                    "status": blog_doc.get("status", "unknown"),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Add route to get image integration status
@blog_bp.route("/image-integration-status/<keyword_id>", methods=["GET"])
def get_image_integration_status(keyword_id):
    try:
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})

        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        return (
            jsonify(
                {
                    "integration_complete": blog_doc.get(
                        "image_integration_complete", False
                    ),
                    "images_integrated": len(blog_doc.get("integrated_images", [])),
                    "has_final_html": bool(blog_doc.get("html_with_images")),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blog_bp.route("/generate-metadata/<keyword_id>", methods=["POST"])
def generate_metadata(keyword_id):
    try:
        # Get the blog document
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        # Get keyword document for context
        keyword_doc = keywords_collection.find_one({"_id": ObjectId(keyword_id)})

        generator = BlogGenerator()

        # Generate metadata
        metadata = generator.generate_blog_metadata(
            blog_doc, keyword_doc["main_keyword"], keyword_doc["keywords"]
        )

        # Get the final HTML (with images if available)
        final_html = (
            blog_doc.get("html_with_images")
            or blog_doc.get("enhanced_html")
            or blog_doc.get("html_content", "")
        )

        # Create the final publish-ready HTML
        publish_ready_html = generator.create_publish_ready_html(
            final_html, metadata, blog_doc
        )

        # Clean the metadata values
        for key in ["post_title", "meta_title", "meta_description", "post_description"]:
            if key in metadata:
                # Remove markdown symbols
                metadata[key] = re.sub(r"^#+\s*", "", metadata[key])
                metadata[key] = metadata[key].strip()

        # Update blog document with ALL fields
        update_data = {
            # Metadata fields
            "post_title": metadata["post_title"],
            "meta_title": metadata["meta_title"],
            "meta_description": metadata["meta_description"],
            "post_description": metadata["post_description"],
            "featured_image": metadata["featured_image"],
            "slug": metadata["slug"],
            "meta_keywords": metadata["meta_keywords"],
            "og_title": metadata["og_title"],
            "og_description": metadata["og_description"],
            "canonical_url": metadata["canonical_url"],
            "author": metadata["author"],
            "publisher": metadata["publisher"],
            # HTML versions
            "publish_ready_html": publish_ready_html,
            "final_html": publish_ready_html,  # Store as final_html too
            # Status fields
            "metadata_complete": True,
            "status": "ready_to_publish",
            "updated_at": datetime.utcnow(),
        }

        # Perform the update
        result = blogs_collection.update_one(
            {"_id": blog_doc["_id"]}, {"$set": update_data}
        )

        if result.modified_count == 0:
            print(f"Warning: No documents were updated for blog {blog_doc['_id']}")

        # Also update keyword document status
        keywords_collection.update_one(
            {"_id": ObjectId(keyword_id)},
            {
                "$set": {
                    "status": "ready_to_publish",
                    "final_blog_id": str(blog_doc["_id"]),
                }
            },
        )

        # Return clean metadata
        return (
            jsonify(
                {
                    "message": "Metadata generated successfully",
                    "metadata": metadata,
                    "final_html": publish_ready_html,
                    "blog_id": str(blog_doc["_id"]),
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error generating metadata: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@blog_bp.route("/download-blog/<keyword_id>/<format>", methods=["GET"])
def download_blog(keyword_id, format="html"):
    try:
        from flask import Response
        import json

        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        if format == "html":
            # Get the publish-ready HTML
            html_content = blog_doc.get("publish_ready_html", "")

            if not html_content:
                return jsonify({"error": "Blog not ready for download"}), 400

            # Create filename from slug
            filename = f"{blog_doc.get('slug', 'blog')}.html"

            return Response(
                html_content,
                mimetype="text/html",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/html; charset=utf-8",
                },
            )

        elif format == "txt":
            # Convert HTML to plain text
            from bs4 import BeautifulSoup

            html_content = blog_doc.get("publish_ready_html", "")
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract text content
            text_content = (
                f"POST TITLE: {blog_doc.get('post_title', '')}\n"
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

            filename = f"{blog_doc.get('slug', 'blog')}.txt"

            return Response(
                text_content,
                mimetype="text/plain",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/plain; charset=utf-8",
                },
            )

        elif format == "json":
            # Return all metadata as JSON
            metadata = {
                "post_title": blog_doc.get("post_title", ""),
                "meta_title": blog_doc.get("meta_title", ""),
                "meta_description": blog_doc.get("meta_description", ""),
                "post_description": blog_doc.get("post_description", ""),
                "slug": blog_doc.get("slug", ""),
                "featured_image": blog_doc.get("featured_image", {}),
                "meta_keywords": blog_doc.get("meta_keywords", ""),
                "author": blog_doc.get("author", ""),
                "canonical_url": blog_doc.get("canonical_url", ""),
                "html_content": blog_doc.get("publish_ready_html", ""),
            }

            filename = f"{blog_doc.get('slug', 'blog')}.json"

            return Response(
                json.dumps(metadata, indent=2),
                mimetype="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "application/json; charset=utf-8",
                },
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@blog_bp.route("/blog-summary/<keyword_id>", methods=["GET"])
def get_blog_summary(keyword_id):
    try:
        blog_doc = blogs_collection.find_one({"keyword_id": ObjectId(keyword_id)})
        if not blog_doc:
            return jsonify({"error": "Blog not found"}), 404

        # Calculate final statistics
        final_html = blog_doc.get("publish_ready_html", "")
        final_word_count = len(
            BeautifulSoup(final_html, "html.parser").get_text().split()
        )

        summary = {
            "title": blog_doc.get("title", ""),
            "slug": blog_doc.get("slug", ""),
            "meta_description": blog_doc.get("meta_description", ""),
            "word_count": blog_doc.get("word_count", final_word_count),
            "images_integrated": len(blog_doc.get("integrated_images", [])),
            "status": blog_doc.get("status", ""),
            "created_at": (
                blog_doc.get("created_at", "").isoformat()
                if blog_doc.get("created_at")
                else ""
            ),
            "quality_enhanced": blog_doc.get("quality_enhanced", False),
        }

        return jsonify({"data": summary}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
