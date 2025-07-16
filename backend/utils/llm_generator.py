import google.generativeai as genai
import re
import random
from utils.db import product_knowledge_collection
from config import Config
import time

class BlogGenerator:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.product_knowledge = self._load_product_knowledge()
        print("Gemini Flash 2.0 initialized successfully!")
    
    def _load_product_knowledge(self):
        """Load product knowledge from MongoDB"""
        try:
            product_doc = product_knowledge_collection.find_one({})
            if not product_doc:
                return self._get_default_product_knowledge()
            
            return {
                "company_name": "SmartWeld",
                "title": product_doc.get('title', 'SmartWeld - Welding Management Software'),
                "overview": product_doc.get('overview', ''),
                "main_website": "https://www.smart-weld.com/",
                "brochure_link": "https://www.smart-weld.com/brochure",
                "benefits_link": "https://www.smart-weld.com/benefits",
                "phone_number": "(+91) 94346-41479",
                "features": product_doc.get('features', []),
                "benefits": product_doc.get('benefits', []),
                "technology": product_doc.get('technology', {}),
                "modules": product_doc.get('modules', []),
                "vision": product_doc.get('vision', ''),
                "business_model": product_doc.get('business_model', {})
            }
        except Exception as e:
            print(f"Error loading product knowledge: {str(e)}")
            return self._get_default_product_knowledge()
    
    def _get_default_product_knowledge(self):
        return {
            "company_name": "Smart Weld",
            "main_website": "https://www.smart-weld.com/",
            "brochure_link": "https://www.smart-weld.com/brochure",
            "benefits_link": "https://www.smart-weld.com/benefits",
            "phone_number": "(+91) 94346-41479"
        }
    
    def _generate_text(self, prompt):
        """Generate text using Gemini"""
        try:
            response = self.model.generate_content(prompt)
            time.sleep(0.5)
            return response.text.strip()
        except Exception as e:
            print(f"Generation error: {str(e)}")
            return ""
    
    def generate_title_tag(self, main_keyword, additional_keywords, scraped_content):
        """Generate SEO-optimized title tag with keywords"""
        # Include all keywords for better distribution
        all_keywords = [main_keyword] + additional_keywords
        
        prompt = f"""You are an expert SEO content writer for the welding industry.

Generate an SEO-optimized blog title that includes these keywords naturally:
- Main keyword: {main_keyword}
- Must also include: {additional_keywords[0]}
- Try to include: {', '.join(additional_keywords[1:3])}

Requirements:
1. 50-60 characters long
2. Include main keyword and at least one additional keyword
3. Compelling and professional
4. Natural flow - don't force keywords

Generate ONLY the title, nothing else."""

        title = self._generate_text(prompt)
        title = re.sub(r'^["\']+|["\']+$', '', title).strip()
        
        # Ensure main keyword is included
        if main_keyword.lower() not in title.lower():
            title = f"{main_keyword}: {title}"[:60]
            
        return title
    
    def generate_h1_heading(self, title, main_keyword):
        """Generate H1 with keyword focus"""
        prompt = f"""Create an H1 heading for a welding industry blog.

Blog title: {title}
Main keyword: {main_keyword}

Make it similar to the title but can be slightly different. Include the main keyword naturally.
Generate ONLY the H1 heading."""

        h1 = self._generate_text(prompt)
        return h1.strip()
    
    def generate_opening_paragraph(self, title, h1, main_keyword, scraped_content):
        """Generate engaging opening with keywords - Target: 150-200 words"""
        context = ""
        if scraped_content and 'scraped_data' in scraped_content:
            snippets = []
            for keyword_data in scraped_content['scraped_data'].values():
                if isinstance(keyword_data, list):
                    for item in keyword_data[:2]:
                        if 'snippet' in item:
                            snippets.append(item['snippet'][:100])
            context = ' '.join(snippets[:2])
        
        prompt = f"""Write a compelling opening paragraph for a welding industry blog.

Title: {title}
Topic: {main_keyword}
Context: {context[:200] if context else 'Welding industry innovations'}

Requirements:
1. Start with a thought-provoking question or surprising statistic
2. Include the main keyword "{main_keyword}" naturally
3. Write 150-200 words (not shorter!)
4. Use engaging, conversational tone
5. Set up what the article will cover
6. Include a preview of key benefits or insights

Generate ONLY the opening paragraph with proper formatting."""

        opening = self._generate_text(prompt)
        return opening
    
    def generate_subheadings(self, title, main_keyword, additional_keywords, num_headings=4):
        """Generate subheadings that incorporate keywords"""
        prompt = f"""Create {num_headings} engaging H2 subheadings for a welding industry blog.

Title: {title}
Main keyword: {main_keyword}
Additional keywords to incorporate: {', '.join(additional_keywords)}

Requirements:
1. Each subheading should include at least one keyword naturally
2. Make them compelling and benefit-focused
3. Use different formats (questions, how-to, benefits, etc.)
4. 5-10 words each
5. Cover different aspects of the topic

Format: List each subheading on a new line, no numbers."""

        response = self._generate_text(prompt)
        
        subheadings = []
        for line in response.split('\n'):
            line = re.sub(r'^\d+[\.\)]\s*|^[-•]\s*|^H2:\s*', '', line.strip())
            if line and len(line) > 10:
                subheadings.append(line)
        
        # Ensure we have enough subheadings with keywords
        if len(subheadings) < num_headings:
            defaults = [
                f"How {main_keyword} Transforms Modern Welding",
                f"Essential {additional_keywords[0]} Best Practices",
                f"Why {additional_keywords[1]} Matters in Welding",
                f"Future of {main_keyword}: Industry Insights"
            ]
            subheadings.extend(defaults[len(subheadings):num_headings])
        
        return subheadings[:num_headings]
    
    def generate_content_section(self, subheading, context, main_keyword, section_keywords, word_target=400):
        """Generate well-formatted content section WITHOUT repeating the heading"""
        benefits = self.product_knowledge.get('benefits', [])[:2]
        
        prompt = f"""Write engaging content for a welding industry blog section.

    Section heading (DO NOT INCLUDE IN OUTPUT): {subheading}
    Main topic: {main_keyword}
    Keywords to include naturally: {', '.join(section_keywords)}
    Context: {context[:200] if context else 'General welding information'}

    Requirements:
    1. Write {word_target} words (reach this target!)
    2. Do NOT include the section heading in your response
    3. Structure the content with:
    - Start with a strong statement directly related to the heading topic
    - Include 3-4 key points as a bulleted list
    - Expand on each point with examples
    - Add a practical tip or industry insight
    - Include statistics or facts when possible
    4. Use keywords naturally: {', '.join(section_keywords)}
    5. Short paragraphs (2-3 sentences each)
    6. Include one rhetorical question
    7. Briefly mention {self.product_knowledge['company_name']} solutions

    Format with HTML tags:
    - Use <p> for paragraphs
    - Use <ul> and <li> for bullet points
    - Use <strong> for emphasis
    - Do NOT include any headings (no h1, h2, h3, etc.)

    Generate ONLY the section content, no headings."""

        content = self._generate_text(prompt)
        
        # Remove any headings that might have been generated
        content = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', '', content, flags=re.DOTALL)
        
        # Ensure proper HTML formatting
        if '<p>' not in content:
            # Convert to HTML if plain text
            paragraphs = content.split('\n\n')
            formatted_paragraphs = []
            
            for para in paragraphs:
                para = para.strip()
                if para:
                    if para.startswith(('•', '-', '*')):
                        # Convert bullet points to list
                        items = [item.strip() for item in para.split('\n') if item.strip()]
                        if items:
                            list_html = '<ul>\n'
                            for item in items:
                                clean_item = re.sub(r'^[•\-\*]\s*', '', item)
                                if clean_item:
                                    list_html += f'    <li>{clean_item}</li>\n'
                            list_html += '</ul>'
                            formatted_paragraphs.append(list_html)
                    elif re.match(r'^\d+\.', para):
                        # Convert numbered list
                        items = [item.strip() for item in para.split('\n') if item.strip()]
                        if items:
                            list_html = '<ol>\n'
                            for item in items:
                                clean_item = re.sub(r'^\d+\.\s*', '', item)
                                if clean_item:
                                    list_html += f'    <li>{clean_item}</li>\n'
                            list_html += '</ol>'
                            formatted_paragraphs.append(list_html)
                    else:
                        # Regular paragraph
                        formatted_paragraphs.append(f'<p>{para}</p>')
            
            content = '\n'.join(formatted_paragraphs)
        
        # Add internal links
        content = self.add_internal_links(content)
        
        return content
    
    
    def add_internal_links(self, content):
        """Add Smart Weld internal links naturally"""
        link_opportunities = [
            ("welding management", self.product_knowledge['main_website']),
            ("smart welding", self.product_knowledge['main_website']),
            ("automated welding", self.product_knowledge['benefits_link']),
            ("real-time monitoring", self.product_knowledge['benefits_link']),
            ("welding technology", self.product_knowledge['main_website']),
            ("quality control", self.product_knowledge['benefits_link'])
        ]
        
        links_added = 0
        for phrase, link in link_opportunities:
            if phrase.lower() in content.lower() and links_added < 2:
                pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                replacement = f'<a href="{link}">{phrase}</a>'
                new_content = pattern.sub(replacement, content, count=1)
                if new_content != content:
                    content = new_content
                    links_added += 1
                    if links_added >= 2:
                        break
        
        return content
    
    def add_outbound_links(self, content):
        """Add relevant outbound links"""
        outbound_links = [
            ("AWS", "American Welding Society", "https://www.aws.org/"),
            ("ISO", "ISO standards", "https://www.iso.org/"),
            ("OSHA", "welding safety", "https://www.osha.gov/welding-cutting-brazing"),
        ]
        
        for short_name, full_name, link in outbound_links:
            if any(term in content.lower() for term in [short_name.lower(), full_name.lower()]):
                if '</p>' in content:
                    # Add after the last paragraph
                    content = content.replace('</p>', f' Learn more at <a href="{link}" rel="noopener">{short_name}</a>.</p>', 1)
                break
        
        return content
    
    def generate_cta(self, main_keyword, title):
        """Generate compelling CTA with formatting"""
        features = ', '.join(self.product_knowledge.get('features', [])[:2])
        
        prompt = f"""Write a compelling call-to-action for a welding blog about {main_keyword}.

Requirements:
1. Start with "Ready to transform your {main_keyword} operations?"
2. Include 3 key benefits as bullet points
3. Add contact information with icons
4. Professional but persuasive tone
5. 150-200 words total

Include these details:
- Phone: {self.product_knowledge['phone_number']}
- Brochure: {self.product_knowledge['brochure_link']}
- Website: {self.product_knowledge['main_website']}
- Benefits page: {self.product_knowledge['benefits_link']}

Format with HTML tags and use emoji icons."""

        cta = self._generate_text(prompt)
        return cta
    
    def generate_conclusion(self, title, main_keyword, key_points):
        """Generate strong conclusion - Target: 150-200 words"""
        vision = self.product_knowledge.get('vision', '')[:100]
        
        prompt = f"""Write a strong conclusion for a welding industry blog.

Title: {title}
Topic: {main_keyword}
Key points covered: {', '.join(key_points[:3])}

Requirements:
1. Summarize 3 main takeaways as a numbered list
2. Include a forward-looking statement about the industry
3. End with a thought-provoking question
4. Write 150-200 words total
5. Reference how {self.product_knowledge['company_name']} is shaping the future
6. Professional but inspiring tone

Format with proper HTML tags."""

        conclusion = self._generate_text(prompt)
        return conclusion
    
    def analyze_blog_quality(self, blog_data, main_keyword, additional_keywords):
        """Lighter quality analysis that doesn't destroy content"""
        # Combine all content
        all_content = []
        all_content.append(blog_data.get('title', ''))
        all_content.append(blog_data.get('h1', ''))
        all_content.append(blog_data.get('opening_paragraph', ''))
        
        for content in blog_data.get('content_sections', []):
            # Strip HTML tags for word counting
            text_content = re.sub('<.*?>', '', content)
            all_content.append(text_content)
        
        all_content.append(re.sub('<.*?>', '', blog_data.get('cta', '')))
        all_content.append(re.sub('<.*?>', '', blog_data.get('conclusion', '')))
        
        full_text = ' '.join(all_content)
        word_count = len(full_text.split())
        
        # Check keyword usage
        all_keywords = [main_keyword] + additional_keywords
        keyword_usage = {}
        
        for keyword in all_keywords:
            count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', full_text.lower()))
            keyword_usage[keyword] = count
        
        # Only flag if severely under word count or missing critical keywords
        needs_minor_enhancement = word_count < 1500 or keyword_usage[main_keyword] == 0
        
        quality_report = {
            'word_count': word_count,
            'target_word_count': 2000,
            'minimum_word_count': 1500,
            'word_count_met': word_count >= 1500,
            'keyword_usage': keyword_usage,
            'keywords_missing': [k for k, v in keyword_usage.items() if v == 0],
            'needs_enhancement': needs_minor_enhancement
        }
        
        return quality_report
    
    def enhance_blog_content(self, blog_data, quality_report, main_keyword, additional_keywords):
        """Gentle enhancement that preserves quality"""
        enhanced_data = blog_data.copy()
        
        # Only enhance if really needed
        if quality_report['word_count'] < 1500:
            # Add a FAQ section instead of modifying existing content
            faq_section = self._generate_faq_section(main_keyword, additional_keywords)
            enhanced_data['faq_section'] = faq_section
        
        # Add missing keywords subtly
        for keyword in quality_report['keywords_missing']:
            # Add to conclusion if not present
            if keyword.lower() not in enhanced_data.get('conclusion', '').lower():
                enhanced_data['conclusion'] = enhanced_data['conclusion'].replace(
                    'welding industry',
                    f'{keyword} and the welding industry',
                    1
                )
        
        return enhanced_data
    
    def _generate_faq_section(self, main_keyword, keywords):
        """Generate FAQ section to add value without modifying existing content"""
        prompt = f"""Generate a FAQ section for a welding blog about {main_keyword}.

Create 3-4 relevant questions and detailed answers.
Include these keywords naturally: {', '.join(keywords[:3])}

Format:
<h3>Frequently Asked Questions</h3>
<div class="faq-item">
  <h4>Question here?</h4>
  <p>Detailed answer here...</p>
</div>

Make each answer 50-75 words. Focus on practical value."""

        faq = self._generate_text(prompt)
        return faq
    
    def generate_simple_html(self, blog_data):
        """Generate clean HTML without double headings"""
        html = f'''<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{blog_data.get("title", "Blog Post")}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            h1 {{
                color: #1a1a1a;
                font-size: 2.5em;
                margin-bottom: 20px;
                line-height: 1.2;
                font-weight: 700;
            }}
            
            h2 {{
                color: #2c3e50;
                font-size: 1.8em;
                margin-top: 40px;
                margin-bottom: 20px;
                font-weight: 600;
            }}
            
            h3 {{
                color: #34495e;
                font-size: 1.4em;
                margin-top: 30px;
                margin-bottom: 15px;
                font-weight: 600;
            }}
            
            p {{
                margin-bottom: 15px;
            }}
            
            ul, ol {{
                margin-bottom: 20px;
                padding-left: 30px;
            }}
            
            li {{
                margin-bottom: 8px;
            }}
            
            figure {{
                margin: 30px 0;
                text-align: center;
            }}
            
            figure img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            
            figcaption {{
                margin-top: 10px;
                font-style: italic;
                color: #666;
                font-size: 0.9em;
            }}
            
            .opening {{
                font-size: 1.1em;
                color: #555;
                margin-bottom: 30px;
                font-style: italic;
            }}
            
            .cta-section {{
                background-color: #f0f8ff;
                padding: 30px;
                border-radius: 8px;
                margin: 40px 0;
                border: 2px solid #3498db;
            }}
            
            .conclusion {{
                border-top: 2px solid #e0e0e0;
                padding-top: 30px;
                margin-top: 40px;
            }}
            
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <article>
            <h1>{blog_data.get("h1", "")}</h1>
            
            <div class="opening">
                {self._clean_html_content(blog_data.get("opening_paragraph", ""))}
            </div>
            
            <figure class="featured-image">
                [Featured Image]
            </figure>
    '''
        
        # Add content sections with single headings
        for i, (subheading, content) in enumerate(zip(
            blog_data.get("subheadings", []), 
            blog_data.get("content_sections", [])
        )):
            # Clean the content to ensure no duplicate headings
            clean_content = self._clean_html_content(content)
            # Remove any h2 tags from content that might duplicate the subheading
            clean_content = re.sub(r'<h2[^>]*>.*?</h2>', '', clean_content, flags=re.DOTALL)
            
            html += f'''
            <h2>{subheading}</h2>
            {clean_content}
    '''
            
            # Add content image placeholder after every 2nd section
            if (i + 1) % 2 == 0 and i < len(blog_data.get("subheadings", [])) - 1:
                html += '''
            <figure class="content-image">
                [Content Image ''' + str((i+1)//2) + ''']
            </figure>
    '''
        
        # Add FAQ if exists
        if 'faq_section' in blog_data and blog_data['faq_section']:
            faq_content = self._clean_html_content(blog_data['faq_section'])
            html += f'''
            <section class="faq-section">
                {faq_content}
            </section>
    '''
        
        # Add CTA
        if blog_data.get("cta"):
            cta_content = self._clean_html_content(blog_data["cta"])
            # Remove any h3 that says "Ready to transform..."
            cta_content = re.sub(r'<h3[^>]*>Ready to transform.*?</h3>', '', cta_content, flags=re.DOTALL | re.IGNORECASE)
            
            html += f'''
            <section class="cta-section">
                <h3>Transform Your Welding Operations Today!</h3>
                {cta_content}
            </section>
    '''
        
        # Add conclusion
        if blog_data.get("conclusion"):
            conclusion_content = self._clean_html_content(blog_data["conclusion"])
            # Remove any h2 that says "Conclusion"
            conclusion_content = re.sub(r'<h2[^>]*>Conclusion</h2>', '', conclusion_content, flags=re.DOTALL | re.IGNORECASE)
            
            html += f'''
            <section class="conclusion">
                <h2>Conclusion</h2>
                {conclusion_content}
            </section>
    '''
        
        html += '''    </article>
    </body>
    </html>'''
        
        return html

    def _clean_html_content(self, content):
        """Clean up HTML content removing artifacts and fixing formatting"""
        if not content:
            return ""
        
        # Remove ```html and ``` markers
        content = re.sub(r'```html\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Remove excessive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Fix spacing around tags
        content = re.sub(r'>\s+<', '><', content)
        
        # Ensure proper paragraph formatting
        if '<p>' not in content and not content.strip().startswith('<'):
            # Convert plain text paragraphs to HTML
            paragraphs = content.split('\n\n')
            formatted_parts = []
            
            for para in paragraphs:
                para = para.strip()
                if para:
                    if para.startswith('•') or para.startswith('-') or para.startswith('*'):
                        # Convert to list
                        items = para.split('\n')
                        list_html = '<ul>\n'
                        for item in items:
                            clean_item = re.sub(r'^[•\-\*]\s*', '', item.strip())
                            if clean_item:
                                list_html += f'            <li>{clean_item}</li>\n'
                        list_html += '        </ul>'
                        formatted_parts.append(list_html)
                    elif re.match(r'^\d+\.', para):
                        # Convert to ordered list
                        items = para.split('\n')
                        list_html = '<ol>\n'
                        for item in items:
                            clean_item = re.sub(r'^\d+\.\s*', '', item.strip())
                            if clean_item:
                                list_html += f'            <li>{clean_item}</li>\n'
                        list_html += '        </ol>'
                        formatted_parts.append(list_html)
                    else:
                        formatted_parts.append(f'<p>{para}</p>')
            
            content = '\n        '.join(formatted_parts)
        
        return content

    def create_publish_ready_html(self, html_content, metadata, blog_doc):
        """Create final publish-ready HTML with proper formatting"""
        # Clean the HTML content first
        html_content = re.sub(r'```html\s*', '', html_content)
        html_content = re.sub(r'```\s*', '', html_content)
        
        # Extract body content if it exists
        if '<body>' in html_content and '</body>' in html_content:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
            if body_match:
                body_content = body_match.group(1)
            else:
                body_content = html_content
        else:
            body_content = html_content
        
        # Build clean HTML
        html = f'''<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        
        <!-- SEO Meta Tags -->
        <title>{metadata["title"]}</title>
        <meta name="description" content="{metadata["meta_description"]}">
        <meta name="keywords" content="{metadata["meta_keywords"]}">
        <meta name="author" content="{metadata["author"]}">
        <link rel="canonical" href="{metadata["canonical_url"]}">
        
        <!-- Open Graph Tags -->
        <meta property="og:title" content="{metadata["og_title"]}">
        <meta property="og:description" content="{metadata["og_description"]}">
        <meta property="og:type" content="article">
        <meta property="og:url" content="{metadata["canonical_url"]}">
        
        <!-- Schema.org Markup -->
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": "{metadata["title"]}",
            "description": "{metadata["meta_description"]}",
            "author": {{
                "@type": "Organization",
                "name": "{metadata["author"]}"
            }},
            "datePublished": "{datetime.utcnow().isoformat()}"
        }}
        </script>
        
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            h1 {{
                color: #1a1a1a;
                font-size: 2.5em;
                margin-bottom: 20px;
                line-height: 1.2;
            }}
            
            h2 {{
                color: #2c3e50;
                font-size: 1.8em;
                margin-top: 40px;
                margin-bottom: 20px;
            }}
            
            h3 {{
                color: #34495e;
                font-size: 1.4em;
                margin: 25px 0 15px;
            }}
            
            p {{
                margin-bottom: 15px;
            }}
            
            ul, ol {{
                margin-bottom: 20px;
                padding-left: 30px;
            }}
            
            li {{
                margin-bottom: 8px;
            }}
            
            figure {{
                margin: 30px 0;
                text-align: center;
            }}
            
            figure img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            
            figcaption {{
                margin-top: 10px;
                font-style: italic;
                color: #666;
                font-size: 0.9em;
            }}
            
            .cta-section {{
                background-color: #f0f8ff;
                padding: 30px;
                border-radius: 8px;
                margin: 40px 0;
            }}
            
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
    {body_content}
    </body>
    </html>'''
        
        return html
    
    def generate_quality_check_step(self, blog_data, main_keyword, additional_keywords):
        """Lighter quality check that preserves content quality"""
        # Generate original HTML
        original_html = self.generate_simple_html(blog_data)
        
        # Analyze quality
        quality_report = self.analyze_blog_quality(blog_data, main_keyword, additional_keywords)
        
        if quality_report['needs_enhancement']:
            # Light enhancement only
            enhanced_data = self.enhance_blog_content(
                blog_data, quality_report, main_keyword, additional_keywords
            )
            
            # Re-analyze
            new_report = self.analyze_blog_quality(enhanced_data, main_keyword, additional_keywords)
            
            # Generate enhanced HTML
            enhanced_html = self.generate_simple_html(enhanced_data)
            
            return {
                'original_report': quality_report,
                'enhanced_report': new_report,
                'enhanced_blog_data': enhanced_data,
                'original_html': original_html,
                'enhanced_html': enhanced_html,
                'enhancement_done': True,
                'final_word_count': new_report['word_count']
            }
        
        return {
            'original_report': quality_report,
            'enhanced_report': quality_report,
            'enhanced_blog_data': blog_data,
            'original_html': original_html,
            'enhanced_html': original_html,
            'enhancement_done': False,
            'final_word_count': quality_report['word_count']
        }



def generate_blog_metadata(self, blog_doc, main_keyword, additional_keywords):
    """Generate comprehensive metadata for the blog"""
    
    # Extract title from H1 or generate new one
    title = blog_doc.get('h1', '') or blog_doc.get('title', '')
    
    # Generate SEO-optimized title if needed
    if not title or len(title) < 30:
        prompt = f"""Generate an SEO-optimized blog post title.

Topic: {main_keyword}
Keywords: {', '.join(additional_keywords[:3])}
Content summary: {blog_doc.get('opening_paragraph', '')[:100]}

Requirements:
1. 50-70 characters
2. Include main keyword naturally
3. Compelling and clickable
4. Professional tone

Generate ONLY the title."""

        title = self._generate_text(prompt, 100).strip()
    
    # Generate slug
    slug = self._generate_slug(title, main_keyword)
    
    # Generate meta description
    meta_description = self._generate_meta_description(
        title, 
        blog_doc.get('opening_paragraph', ''),
        main_keyword
    )
    
    # Generate meta keywords
    all_keywords = [main_keyword] + additional_keywords
    meta_keywords = ', '.join(all_keywords[:8])  # Limit to 8 keywords
    
    # Generate Open Graph tags
    og_title = title[:60] + '...' if len(title) > 60 else title
    og_description = meta_description[:160]
    
    metadata = {
        'title': title,
        'slug': slug,
        'meta_description': meta_description,
        'meta_keywords': meta_keywords,
        'og_title': og_title,
        'og_description': og_description,
        'canonical_url': f"{self.product_knowledge['main_website']}blog/{slug}",
        'author': self.product_knowledge.get('company_name', 'Smart Weld'),
        'publisher': self.product_knowledge.get('company_name', 'Smart Weld')
    }
    
    return metadata

def _generate_slug(self, title, main_keyword):
    """Generate URL-friendly slug"""
    # Start with title
    slug = title.lower()
    
    # Remove special characters
    slug = re.sub(r'[^\w\s-]', '', slug)
    
    # Replace spaces with hyphens
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Ensure main keyword is in slug
    if main_keyword.lower().replace(' ', '-') not in slug:
        slug = f"{main_keyword.lower().replace(' ', '-')}-{slug}"
    
    # Limit length
    if len(slug) > 60:
        slug = slug[:60].rsplit('-', 1)[0]
    
    return slug

def _generate_meta_description(self, title, opening_paragraph, main_keyword):
    """Generate meta description"""
    if opening_paragraph and len(opening_paragraph) > 100:
        # Use opening paragraph as base
        meta_desc = opening_paragraph[:150] + '...'
    else:
        # Generate new meta description
        prompt = f"""Generate a meta description for SEO.

Title: {title}
Topic: {main_keyword}

Requirements:
1. 150-160 characters
2. Include main keyword
3. Compelling and informative
4. End with call to action

Generate ONLY the meta description."""

        meta_desc = self._generate_text(prompt, 50).strip()
    
    # Ensure it includes company name
    if self.product_knowledge['company_name'] not in meta_desc:
        meta_desc = meta_desc[:130] + f" | {self.product_knowledge['company_name']}"
    
    return meta_desc[:160]  # Enforce limit

def create_publish_ready_html(self, html_content, metadata, blog_doc):
    """Create final publish-ready HTML with all metadata and proper structure"""
    
    # Extract body content from existing HTML
    if '<body>' in html_content:
        body_content = html_content.split('<body>')[1].split('</body>')[0]
    else:
        body_content = html_content
    
    # Remove any existing style tags from body
    body_content = re.sub(r'<style>.*?</style>', '', body_content, flags=re.DOTALL)
    
    publish_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    
    <!-- SEO Meta Tags -->
    <title>{metadata['title']}</title>
    <meta name="description" content="{metadata['meta_description']}">
    <meta name="keywords" content="{metadata['meta_keywords']}">
    <meta name="author" content="{metadata['author']}">
    <meta name="publisher" content="{metadata['publisher']}">
    <link rel="canonical" href="{metadata['canonical_url']}">
    
    <!-- Open Graph Tags -->
    <meta property="og:title" content="{metadata['og_title']}">
    <meta property="og:description" content="{metadata['og_description']}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{metadata['canonical_url']}">
    <meta property="og:site_name" content="{self.product_knowledge['company_name']}">
    
    <!-- Twitter Card Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{metadata['og_title']}">
    <meta name="twitter:description" content="{metadata['og_description']}">
    
    <!-- Schema.org Markup -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{metadata['title']}",
        "description": "{metadata['meta_description']}",
        "author": {{
            "@type": "Organization",
            "name": "{metadata['author']}",
            "url": "{self.product_knowledge['main_website']}"
        }},
        "publisher": {{
            "@type": "Organization",
            "name": "{metadata['publisher']}",
            "url": "{self.product_knowledge['main_website']}"
        }},
        "datePublished": "{datetime.utcnow().isoformat()}",
        "dateModified": "{datetime.utcnow().isoformat()}",
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "{metadata['canonical_url']}"
        }}
    }}
    </script>
    
    <!-- Clean CSS Styling -->
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        
        h1 {{
            color: #1a1a1a;
            font-size: 2.5em;
            margin-bottom: 20px;
            line-height: 1.2;
        }}
        
        h2 {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        h3 {{
            color: #34495e;
            font-size: 1.4em;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        figure {{
            margin: 30px 0;
            text-align: center;
        }}
        
        figure img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        figcaption {{
            margin-top: 10px;
            font-style: italic;
            color: #666;
            font-size: 0.9em;
        }}
        
        .cta-box {{
            background-color: #f0f8ff;
            padding: 30px;
            border-radius: 8px;
            margin: 40px 0;
            border: 2px solid #3498db;
        }}
        
        .cta-box h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        
        hr {{
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 40px 0;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 15px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <article>
        {body_content}
    </article>
    
    <!-- Footer -->
    <footer style="margin-top: 60px; padding-top: 30px; border-top: 1px solid #e0e0e0; text-align: center; color: #666;">
        <p>&copy; {datetime.utcnow().year} {self.product_knowledge['company_name']}. All rights reserved.</p>
        <p>
            <a href="{self.product_knowledge['main_website']}">Website</a> | 
            <a href="{self.product_knowledge['brochure_link']}">Download Brochure</a> | 
            <a href="{self.product_knowledge['benefits_link']}">Benefits</a>
        </p>
    </footer>
</body>
</html>"""
    
    return publish_html