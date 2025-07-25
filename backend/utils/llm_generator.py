import google.generativeai as genai
import re
import random
from utils.db import product_knowledge_collection
from config import Config
import time
from datetime import datetime


class BlogGenerator:
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.product_knowledge = self._load_product_knowledge()
        print("Gemini Flash 2.0 initialized successfully!")  # Keep generic message

    def _load_product_knowledge(self):
        """Load product knowledge from MongoDB"""
        try:
            product_doc = product_knowledge_collection.find_one({})
            if not product_doc:
                return self._get_default_product_knowledge()

            # Load Shothik AI specific fields
            return {
                "company_name": product_doc.get("company_name", "Shothik AI"),
                "title": product_doc.get("title", "Shothik AI - AI-Powered Writing Platform"),
                "overview": product_doc.get("overview", ""),
                "main_website": product_doc.get("main_website", "https://www.shothik.ai/"),
                "brochure_link": product_doc.get("about_link", "https://www.shothik.ai/about-us"),
                "benefits_link": product_doc.get("main_website", "https://www.shothik.ai/"),
                "phone_number": product_doc.get("phone_number", ""),
                "email": product_doc.get("email", "support@shothik.ai"),
                "humanize_link": product_doc.get("humanize_link", "https://www.shothik.ai/humanize-gpt"),
                "ai_detector_link": product_doc.get("ai_detector_link", "https://www.shothik.ai/ai-detector"),
                "grammar_check_link": product_doc.get("grammar_check_link", "https://www.shothik.ai/grammar-check"),
                "summarizer_link": product_doc.get("summarizer_link", "https://www.shothik.ai/summarize"),
                "translator_link": product_doc.get("translator_link", "https://www.shothik.ai/translator"),
                "research_link": product_doc.get("research_link", "https://www.shothik.ai/research"),
                "features": product_doc.get("features", []),
                "benefits": product_doc.get("benefits", []),
                "technology": product_doc.get("technology", {}),
                "modules": product_doc.get("modules", []),
                "vision": product_doc.get("vision", ""),
                "business_model": product_doc.get("business_model", {}),
            }
        except Exception as e:
            print(f"Error loading product knowledge: {str(e)}")
            return self._get_default_product_knowledge()

    def _get_default_product_knowledge(self):
        return {
            "company_name": "Shothik AI",
            "main_website": "https://www.shothik.ai/",
            "brochure_link": "https://www.shothik.ai/about-us",
            "benefits_link": "https://www.shothik.ai/",
            "phone_number": "",
            "email": "support@shothik.ai",
            "humanize_link": "https://www.shothik.ai/humanize-gpt",
            "ai_detector_link": "https://www.shothik.ai/ai-detector",
            "grammar_check_link": "https://www.shothik.ai/grammar-check",
            "summarizer_link": "https://www.shothik.ai/summarize",
            "translator_link": "https://www.shothik.ai/translator",
            "research_link": "https://www.shothik.ai/research",
        }

    def _generate_text(self, prompt):
        """Generate text using Gemini with improved prompting to avoid HTML artifacts"""
        try:
            # Add system instruction to avoid HTML artifacts and markers
            enhanced_prompt = f"""SYSTEM INSTRUCTION: You are a professional content writer. Generate clean, readable content using proper HTML formatting when needed. 

    IMPORTANT RULES:
    - Do NOT include HTML document structure (no <!DOCTYPE>, <html>, <head>, <body> tags)
    - Do NOT include code block markers (no ```, no "html" labels)
    - Do NOT start responses with "html" or technical explanations
    - Use <strong> for bold text and <em> for italic text
    - Generate ONLY the requested content without metadata or explanations

    USER REQUEST:
    {prompt}

    Generate clean, professional content that can be directly inserted into a webpage."""

            response = self.model.generate_content(enhanced_prompt)
            time.sleep(0.5)
            
            generated_text = response.text.strip()
            
            # Additional cleaning to remove artifacts
            generated_text = self._clean_generation_artifacts(generated_text)
            generated_text = self._clean_asterisk_formatting(generated_text)
            
            return generated_text
        except Exception as e:
            print(f"Generation error: {str(e)}")
            return ""

    def _clean_generation_artifacts(self, content):
        """Remove common generation artifacts including HTML tag fragments"""
        if not content:
            return ""
        
        # Remove HTML document artifacts
        artifacts_to_remove = [
            r"^html\s*\n?",
            r"^HTML\s*\n?", 
            r"^```html\s*\n?",
            r"^```\s*\n?",
            r"```html\s*$",
            r"```\s*$",
            r"^<!DOCTYPE[^>]*>\s*\n?",
            r"^<html[^>]*>\s*\n?",
            r"^<head[^>]*>.*?</head>\s*\n?",
            r"^<body[^>]*>\s*\n?",
            r"</body>\s*\n?$",
            r"</html>\s*\n?$"
        ]
        
        # Add HTML tag fragment patterns
        tag_fragments = [
            r"^h1>\s*",           # Remove "h1>" at start
            r"^</h1>\s*",         # Remove "</h1>" at start  
            r"^h2>\s*",           # Remove "h2>" at start
            r"^</h2>\s*",         # Remove "</h2>" at start
            r"^h3>\s*",           # Remove "h3>" at start
            r"^</h3>\s*",         # Remove "</h3>" at start
            r"^p>\s*",            # Remove "p>" at start
            r"^</p>\s*",          # Remove "</p>" at start
            r"^div>\s*",          # Remove "div>" at start
            r"^</div>\s*",        # Remove "</div>" at start
            r"^\w+>\s*",          # Remove any word followed by ">" at start
        ]
        
        # Apply all artifact removal patterns
        for pattern in artifacts_to_remove + tag_fragments:
            content = re.sub(pattern, "", content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any remaining HTML tag fragments (more general approach)
        content = re.sub(r"^[a-zA-Z0-9]+>\s*", "", content)  # Remove tag remnants like "h1>", "div>", etc.
        content = re.sub(r"^</[a-zA-Z0-9]+>\s*", "", content)  # Remove closing tag remnants like "</h1>", "</div>", etc.
        
        return content.strip()

    def generate_title_tag(self, main_keyword, additional_keywords, scraped_content):
        """Generate SEO-optimized title tag with keywords"""
        all_keywords = [main_keyword] + additional_keywords
        
        prompt = f"""You are an expert SEO content writer for any industry or topic.

    Generate an SEO-optimized blog title that includes these keywords naturally:
    - Main keyword: {main_keyword}
    - Must also include: {additional_keywords[0]}
    - Try to include: {', '.join(additional_keywords[1:3])}

    Requirements:
    1. 50-60 characters long (STRICT LIMIT)
    2. Include main keyword and at least one additional keyword
    3. Compelling and professional
    4. Natural flow - don't force keywords
    5. NO markdown symbols (no #, ##, *, etc.)
    6. NO colons or special characters at the start
    7. NO HTML tags or code markers
    8. Plain text title only

    Generate ONLY the title text, nothing else. Do not include "html" or any technical terms."""

        title = self._generate_text(prompt)
        
        # Keep all the cleaning logic exactly the same
        title = self._clean_title_text(title)
        title = self._clean_generation_artifacts(title)
        
        if len(title) > 60:
            title = title[:57]
            last_space = title.rfind(' ')
            if last_space > 40:
                title = title[:last_space]
            title = title.rstrip('.,;:') + '...'
        
        if main_keyword.lower() not in title.lower():
            title = f"{main_keyword}: {title}"
            if len(title) > 60:
                title = title[:60]
        
        return title
        
    def _clean_title_text(self, text):
        """Clean title text from any formatting or artifacts including HTML fragments"""
        if not text:
            return ""
        
        # Remove HTML tag fragments first
        text = re.sub(r'^[a-zA-Z0-9]+>\s*', '', text)  # Remove "h1>", "h2>", etc. at start
        text = re.sub(r'^</[a-zA-Z0-9]+>\s*', '', text)  # Remove "</h1>", "</h2>", etc. at start
        
        # Remove markdown symbols
        text = re.sub(r'^#+\s*', '', text)  # Remove # or ## at start
        text = re.sub(r'\*+', '', text)     # Remove asterisks
        text = re.sub(r'^[-=]+\s*', '', text)  # Remove dashes or equals at start
        
        # Remove quotes
        text = re.sub(r'^["\']+|["\']+$', '', text)
        
        # Remove any remaining special characters at the start
        text = re.sub(r'^[^\w]+', '', text)
        
        # Clean multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def generate_h1_heading(self, title, main_keyword):
        """Generate H1 with keyword focus"""
        prompt = f"""Create an H1 heading for a blog post.

        Blog title: {title}
        Main keyword: {main_keyword}

        Requirements:
        1. Similar to the title but can be slightly different
        2. Include the main keyword naturally
        3. 40-70 characters
        4. Engaging and clear
        5. NO HTML tags (no <h1>, </h1>, <h2>, etc.)
        6. NO markdown formatting (no #, ##, etc.)
        7. Plain text only
        8. Do not include "h1" or any HTML terminology

        Generate ONLY the heading text that will go inside the H1 tag."""

        h1 = self._generate_text(prompt)
        h1 = self._clean_title_text(h1)
        h1 = self._clean_generation_artifacts(h1)
        
        if len(h1) > 70:
            h1 = h1[:67] + '...'
        
        return h1

    def generate_opening_paragraph(self, title, h1, main_keyword, scraped_content):
        """Generate engaging opening with keywords - Target: 150-200 words"""
        context = ""
        if scraped_content and "scraped_data" in scraped_content:
            snippets = []
            for keyword_data in scraped_content["scraped_data"].values():
                if isinstance(keyword_data, list):
                    for item in keyword_data[:2]:
                        if "snippet" in item:
                            snippets.append(item["snippet"][:100])
            context = " ".join(snippets[:2])

        prompt = f"""Write a compelling opening paragraph for a blog on any topic.

Title: {title}
Topic: {main_keyword}
Context: {context[:200] if context else 'General information about ' + main_keyword}

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
        prompt = f"""Create {num_headings} engaging H2 subheadings for a blog on any topic.

    Title: {title}
    Main keyword: {main_keyword}
    Additional keywords to incorporate: {', '.join(additional_keywords)}

    Requirements:
    1. Each subheading should include at least one keyword naturally
    2. Make them compelling and benefit-focused
    3. Use different formats (questions, how-to, benefits, etc.)
    4. 5-10 words each
    5. Cover different aspects of the topic

    IMPORTANT: Output ONLY the subheadings, one per line. No introductory text, no numbers, no explanations."""

        # Keep all the existing parsing and cleaning logic
        response = self._generate_text(prompt)
        
        lines = response.strip().split('\n')
        subheadings = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            skip_patterns = [
                'here are', 'subheading', 'following', 'below', 'above',
                'engaging', 'created', 'generated', ':', 'requirements'
            ]
            if any(pattern in line.lower() for pattern in skip_patterns):
                continue
            
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            line = re.sub(r'^[-•*]\s*', '', line)
            line = re.sub(r'^H\d:\s*', '', line)
            line = re.sub(r'^\w\.\s*', '', line)
            
            if 3 <= len(line.split()) <= 15 and len(line) > 10:
                subheadings.append(line)
        
        if len(subheadings) < num_headings:
            defaults = [
                f"How {main_keyword} Transforms Modern Practices",
                f"Essential {additional_keywords[0]} Best Practices",
                f"Why {additional_keywords[1] if len(additional_keywords) > 1 else main_keyword} Matters",
                f"Mastering {main_keyword}: Expert Tips and Techniques",
                f"The Future of {main_keyword} Technology",
                f"Optimize Your {additional_keywords[0] if additional_keywords else 'Process'}"
            ]
            
            while len(subheadings) < num_headings and defaults:
                subheadings.append(defaults.pop(0))
        
        return subheadings[:num_headings]


    def generate_content_section(
        self, subheading, context, main_keyword, section_keywords, word_target=400
    ):
        """Generate well-formatted content section WITHOUT repeating the heading"""
        benefits = self.product_knowledge.get("benefits", [])[:2]

        # Check if the topic is related to writing/content
        writing_keywords = ['writing', 'content', 'ai', 'paraphrase', 'humanize', 'grammar', 
                           'seo', 'blog', 'article', 'essay', 'plagiarism', 'detection',
                           'translation', 'summarize', 'research']
        
        is_writing_related = any(kw.lower() in ' '.join([main_keyword] + section_keywords).lower() 
                                for kw in writing_keywords)

        prompt = f"""Write engaging content for a blog section on any topic.

    Section heading (DO NOT INCLUDE IN OUTPUT): {subheading}
    Main topic: {main_keyword}
    Keywords to include naturally: {', '.join(section_keywords)}
    Context: {context[:200] if context else 'General information'}

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
    {"7. Briefly mention " + self.product_knowledge['company_name'] + " solutions if the topic relates to writing, content creation, or AI tools" if is_writing_related else ""}

    Format with HTML tags:
    - Use <p> for paragraphs
    - Use <ul> and <li> for bullet points
    - Use <strong> for emphasis
    - Do NOT include any headings (no h1, h2, h3, etc.)

    Generate ONLY the section content, no headings."""

        content = self._generate_text(prompt)

        # Keep all existing cleaning logic
        content = re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", content, flags=re.DOTALL)

        # Keep existing HTML formatting logic
        if "<p>" not in content:
            paragraphs = content.split("\n\n")
            formatted_paragraphs = []

            for para in paragraphs:
                para = para.strip()
                if para:
                    if para.startswith(("•", "-", "*")):
                        items = [
                            item.strip() for item in para.split("\n") if item.strip()
                        ]
                        if items:
                            list_html = "<ul>\n"
                            for item in items:
                                clean_item = re.sub(r"^[•\-\*]\s*", "", item)
                                if clean_item:
                                    list_html += f"    <li>{clean_item}</li>\n"
                            list_html += "</ul>"
                            formatted_paragraphs.append(list_html)
                    elif re.match(r"^\d+\.", para):
                        items = [
                            item.strip() for item in para.split("\n") if item.strip()
                        ]
                        if items:
                            list_html = "<ol>\n"
                            for item in items:
                                clean_item = re.sub(r"^\d+\.\s*", "", item)
                                if clean_item:
                                    list_html += f"    <li>{clean_item}</li>\n"
                            list_html += "</ol>"
                            formatted_paragraphs.append(list_html)
                    else:
                        formatted_paragraphs.append(f"<p>{para}</p>")

            content = "\n".join(formatted_paragraphs)

        # Add internal links conditionally
        if is_writing_related:
            content = self.add_internal_links(content)

        return content

    def add_internal_links(self, content):
        """Add Shothik AI internal links naturally"""
        link_opportunities = [
            ("paraphrasing", self.product_knowledge.get("main_website", "")),
            ("humanize ai text", self.product_knowledge.get("humanize_link", "")),
            ("ai detection", self.product_knowledge.get("ai_detector_link", "")),
            ("grammar check", self.product_knowledge.get("grammar_check_link", "")),
            ("summarization", self.product_knowledge.get("summarizer_link", "")),
            ("translation", self.product_knowledge.get("translator_link", "")),
            ("research tool", self.product_knowledge.get("research_link", "")),
            ("writing assistant", self.product_knowledge.get("main_website", "")),
        ]

        links_added = 0
        for phrase, link in link_opportunities:
            if phrase.lower() in content.lower() and links_added < 2 and link:
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
        """Add relevant outbound links based on content topic"""
        # For now, return content as-is since we're generic
        # In the future, this could be made topic-aware
        return content

    def generate_cta(self, main_keyword, title):
        """Generate compelling CTA with formatting - Fixed to avoid meta-commentary"""
        features = ", ".join(self.product_knowledge.get("features", [])[:2])

        prompt = f"""Write a compelling call-to-action section for a blog about {main_keyword}.

    IMPORTANT: Write ONLY the actual CTA content that will appear on the webpage. Do NOT include any technical explanations, HTML comments, or meta-commentary about the code.

    Requirements:
    1. Start with a compelling headline about transforming their {main_keyword} workflow with Shothik AI
    2. Include 3 key benefits as bullet points
    3. Add contact information with proper formatting
    4. Professional but persuasive tone
    5. 150-200 words total
    6. Use HTML tags for formatting

    Include these contact details:
    - Email: {self.product_knowledge.get('email', 'support@shothik.ai')}
    - Website: {self.product_knowledge['main_website']}
    - Special Tool: {self.product_knowledge.get('humanize_link', '')}

    Example format:
    <h3>Transform Your {main_keyword} Workflow with Shothik AI!</h3>
    <p>Ready to revolutionize your content creation? Shothik AI offers cutting-edge AI-powered tools that deliver:</p>
    <ul>
    <li>Advanced paraphrasing with unlimited freeze words</li>
    <li>Humanize AI text to bypass detection tools</li>
    <li>Professional grammar checking and content enhancement</li>
    </ul>
    <p>Don't let outdated methods slow you down. Join thousands who trust Shothik AI for their writing needs.</p>
    <div class="contact-info">
    <p>✉️ Email us: <strong>{self.product_knowledge.get('email', 'support@shothik.ai')}</strong></p>
    <p>🌐 Visit: <a href="{self.product_knowledge['main_website']}" target="_blank">www.shothik.ai</a></p>
    <p>🚀 Try our tool: <a href="{self.product_knowledge.get('humanize_link', '')}" target="_blank">Humanize AI Text</a></p>
    </div>

    Generate ONLY the CTA content, no explanations or technical details."""

        cta = self._generate_text(prompt)
        
        # Keep all existing cleaning logic
        cta = self._clean_meta_commentary(cta)
        
        return cta

    def _clean_meta_commentary(self, content):
        """Remove meta-commentary and technical explanations from content"""
        if not content:
            return ""
        
        # Remove common meta-commentary patterns
        meta_patterns = [
            r'\*\*[^*]+\*\*[^*]*explanation[^.]*\.',
            r'Key improvements and explanations:.*',
            r'The code is properly formatted.*',
            r'Uses Font Awesome icons.*',
            r'Added.*target="_blank".*',
            r'This is generally good UX.*',
            r'Benefits Page Link.*',
            r'Contact Information Formatting.*',
            r'CSS Styling.*',
            r'Complete and Working.*',
            r'Word Count.*',
            r'Emoji Usage.*',
            r'Improved Tone.*',
            r'Emphasis on Action.*',
            r'Mobile-Friendly.*',
            r'The critical addition is.*',
            r'.*adheres to all requirements.*',
            r'.*incorporates best practices.*',
            r'.*FontAwesome.*CSS.*',
        ]
        
        for pattern in meta_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any remaining asterisk explanations
        content = re.sub(r'\*\s*\*\*[^*]+\*\*[^.]*\.', '', content, flags=re.DOTALL)
        
        # Clean up extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        return content

    def generate_conclusion(self, title, main_keyword, key_points):
        """Generate strong conclusion WITHOUT the heading and without meta-commentary"""
        vision = self.product_knowledge.get("vision", "")[:100]

        prompt = f"""Write a strong conclusion for a blog on any topic.

    Title: {title}
    Topic: {main_keyword}
    Key points covered: {', '.join(key_points[:3])}

    IMPORTANT: Write ONLY the actual conclusion content. Do NOT include technical explanations, HTML comments, or meta-commentary about the code structure.

    Requirements:
    1. DO NOT include "Conclusion" as a heading or h2 tag
    2. Start with a strong summary statement
    3. Include 3 main takeaways as a numbered list
    4. Add a forward-looking statement about the industry/topic
    5. End with a thought-provoking question
    6. Write 150-200 words total
    7. Reference how {self.product_knowledge['company_name']} can help if the topic relates to writing or content
    8. Professional but inspiring tone

    Format with proper HTML tags (p, ol, li) but NO headings.

    Generate ONLY the conclusion content, no technical explanations."""

        conclusion = self._generate_text(prompt)

        # Keep all existing cleaning logic
        conclusion = re.sub(
            r"<h[1-6][^>]*>.*?</h[1-6]>", "", conclusion, flags=re.DOTALL
        )
        
        conclusion = self._clean_meta_commentary(conclusion)

        return conclusion

    def _clean_llm_output(self, text, remove_instructions=True):
        """Clean common artifacts from LLM outputs"""
        if not text:
            return ""
        
        # Remove code block markers
        text = re.sub(r'```[\w]*\n?', '', text)
        text = re.sub(r'```', '', text)
        
        if remove_instructions:
            # Remove common instruction artifacts
            instruction_patterns = [
                r'Here are \d+ .+?:?\s*\n',
                r'I\'ve created .+?:?\s*\n',
                r'Below are .+?:?\s*\n',
                r'The following .+?:?\s*\n',
                r'^\d+\.\s*Here are.+?:\s*$',
            ]
            
            for pattern in instruction_patterns:
                text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text.strip()    
    def analyze_blog_quality(self, blog_data, main_keyword, additional_keywords):
        """Lighter quality analysis that doesn't destroy content"""
        # Combine all content
        all_content = []
        all_content.append(blog_data.get("title", ""))
        all_content.append(blog_data.get("h1", ""))
        all_content.append(blog_data.get("opening_paragraph", ""))

        for content in blog_data.get("content_sections", []):
            # Strip HTML tags for word counting
            text_content = re.sub("<.*?>", "", content)
            all_content.append(text_content)

        all_content.append(re.sub("<.*?>", "", blog_data.get("cta", "")))
        all_content.append(re.sub("<.*?>", "", blog_data.get("conclusion", "")))

        full_text = " ".join(all_content)
        word_count = len(full_text.split())

        # Check keyword usage
        all_keywords = [main_keyword] + additional_keywords
        keyword_usage = {}

        for keyword in all_keywords:
            count = len(
                re.findall(
                    r"\b" + re.escape(keyword.lower()) + r"\b", full_text.lower()
                )
            )
            keyword_usage[keyword] = count

        # Only flag if severely under word count or missing critical keywords
        needs_minor_enhancement = word_count < 1500 or keyword_usage[main_keyword] == 0

        quality_report = {
            "word_count": word_count,
            "target_word_count": 2000,
            "minimum_word_count": 1500,
            "word_count_met": word_count >= 1500,
            "keyword_usage": keyword_usage,
            "keywords_missing": [k for k, v in keyword_usage.items() if v == 0],
            "needs_enhancement": needs_minor_enhancement,
        }

        return quality_report

    def enhance_blog_content(self, blog_data, quality_report, main_keyword, additional_keywords):
        """Gentle enhancement that preserves quality"""
        enhanced_data = blog_data.copy()

        if quality_report["word_count"] < 1500:
            faq_section = self._generate_faq_section(main_keyword, additional_keywords)
            enhanced_data["faq_section"] = faq_section

        for keyword in quality_report["keywords_missing"]:
            if keyword.lower() not in enhanced_data.get("conclusion", "").lower():
                # Generic replacement without welding reference
                enhanced_data["conclusion"] = enhanced_data["conclusion"].replace(
                    "the industry", f"the {keyword} landscape", 1
                )

        return enhanced_data

    def _generate_faq_section(self, main_keyword, keywords):
        """Generate FAQ section to add value without modifying existing content"""
        prompt = f"""Generate a FAQ section for a blog about {main_keyword}.

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

    def _clean_html_content(self, content):
        """Clean up HTML content removing artifacts and fixing formatting"""
        if not content:
            return ""

        # Remove HTML code block markers and artifacts
        content = re.sub(r"```html\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        content = re.sub(r"^html\s*", "", content)  # Remove standalone "html" at start
        content = re.sub(r"\bhtml\b", "", content)  # Remove standalone "html" word
        
        # Remove other common artifacts
        content = re.sub(r"^(DOCTYPE|doctype)\s*", "", content, flags=re.MULTILINE)
        
        # Use the safe asterisk cleaning method
        content = self._clean_asterisk_formatting(content)

        # Remove excessive newlines
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Fix spacing around tags
        content = re.sub(r">\s+<", "><", content)

        # Remove any remaining HTML artifacts at the beginning
        content = re.sub(r"^(html|HTML)\s*\n?", "", content)
        
        # Clean up whitespace
        content = content.strip()

        # If content has no HTML tags, convert to proper HTML
        if "<p>" not in content and "<ul>" not in content and "<ol>" not in content:
            # Split into paragraphs
            paragraphs = content.split("\n\n")
            formatted_parts = []

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Skip if it's just "html" or similar artifacts
                if para.lower().strip() in ['html', 'doctype', '<!doctype', 'doctype html']:
                    continue

                # Check if it's a list
                if para.startswith(("•", "-")):
                    # Bullet list
                    items = para.split("\n")
                    list_html = "<ul>\n"
                    for item in items:
                        clean_item = re.sub(r"^[•\-]\s*", "", item.strip())
                        if clean_item:
                            list_html += f"            <li>{clean_item}</li>\n"
                    list_html += "        </ul>"
                    formatted_parts.append(list_html)

                elif re.match(r"^\d+\.", para):
                    # Numbered list
                    items = para.split("\n")
                    list_html = "<ol>\n"
                    for item in items:
                        clean_item = re.sub(r"^\d+\.\s*", "", item.strip())
                        if clean_item:
                            list_html += f"            <li>{clean_item}</li>\n"
                    list_html += "        </ol>"
                    formatted_parts.append(list_html)

                else:
                    # Regular paragraph
                    formatted_parts.append(f"<p>{para}</p>")

            content = "\n        ".join(formatted_parts)

        return content

    def _clean_asterisk_formatting(self, content):
        """Clean asterisk markdown formatting and convert to HTML - Safe version"""
        if not content:
            return ""
        
        # Step 1: Convert **text** to <strong>text</strong>
        content = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', content)
        
        # Step 2: Convert remaining single *text* to <em>text</em>
        # Use a simple approach that avoids complex lookbehinds
        parts = content.split('<strong>')
        processed_parts = []
        
        for i, part in enumerate(parts):
            if i == 0:
                # First part - process normally
                part = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', part)
            else:
                # Parts after <strong> - be more careful
                if '</strong>' in part:
                    before_strong, after_strong = part.split('</strong>', 1)
                    after_strong = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', after_strong)
                    part = before_strong + '</strong>' + after_strong
                
            processed_parts.append(part)
        
        content = '<strong>'.join(processed_parts)
        
        # Step 3: Clean up any remaining problematic asterisks
        content = re.sub(r'\*+', '', content)  # Remove any remaining asterisks
        
        return content       

    def generate_simple_html(self, blog_data):
        """Generate clean HTML without double headings"""
        html = f"""<!DOCTYPE html>
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
                    margin-bottom: 10px;
                    line-height: 1.2;
                    font-weight: 700;
                }}
                .title-tag {{
                    color: #666;
                    font-size: 0.9em;
                    font-style: italic;
                    margin-bottom: 20px;
                    display: block;
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
                    max-height: 400px;
                    object-fit: cover;
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
                
                /* Responsive images */
                @media (max-width: 768px) {{
                    figure img {{
                        max-height: 250px;
                    }}
                }}
            </style>
        </head>
        <body>
            <article>
                <h1>{blog_data.get("h1", "")}</h1>
                <span class="title-tag">{blog_data.get("title", "")}</span>
                
                <div class="opening">
                    {self._clean_asterisk_formatting(self._clean_html_content(blog_data.get("opening_paragraph", "")))}
                </div>
                
                <figure class="featured-image">
                    [Featured Image]
                </figure>
        """
    # Rest of the method remains the same...

        # Add content sections with single headings
        for i, (subheading, content) in enumerate(
            zip(blog_data.get("subheadings", []), blog_data.get("content_sections", []))
        ):
            clean_content = self._clean_asterisk_formatting(self._clean_html_content(content))
            # Remove any h2 tags from content that might duplicate the subheading
            clean_content = re.sub(
                r"<h2[^>]*>.*?</h2>", "", clean_content, flags=re.DOTALL
            )

            html += f"""
            <h2>{subheading}</h2>
            {clean_content}
    """

            # Add content image placeholder after every 2nd section
            if (i + 1) % 2 == 0 and i < len(blog_data.get("subheadings", [])) - 1:
                html += (
                    """
            <figure class="content-image">
                [Content Image """
                    + str((i + 1) // 2)
                    + """]
            </figure>
    """
                )

        # Add FAQ if exists
        if "faq_section" in blog_data and blog_data["faq_section"]:
            faq_content = self._clean_asterisk_formatting(self._clean_html_content(blog_data["faq_section"]))
            html += f"""
            <section class="faq-section">
                {faq_content}
            </section>
    """

        # Add CTA
        if blog_data.get("cta"):
            cta_content = self._clean_asterisk_formatting(self._clean_html_content(blog_data["cta"]))
            # Remove any h3 that says "Ready to transform..."
            cta_content = re.sub(
                r"<h3[^>]*>Ready to transform.*?</h3>",
                "",
                cta_content,
                flags=re.DOTALL | re.IGNORECASE,
            )

            html += f"""
            <section class="cta-section">
                <h3>Shothik.AI</h3>
                {cta_content}
            </section>
    """

        # Add conclusion - ONLY ONCE
        if blog_data.get("conclusion"):
            conclusion_content = self._clean_asterisk_formatting(self._clean_html_content(blog_data["conclusion"]))
            # Remove any h2 tags from the conclusion content
            conclusion_content = re.sub(
                r"<h2[^>]*>.*?</h2>", "", conclusion_content, flags=re.DOTALL
            )

            html += f"""
            <section class="conclusion">
                <h2>Conclusion</h2>
                {conclusion_content}
            </section>
    """

        # Close article tag properly
        html += """    </article>
    </body>
    </html>"""

        return html

    def create_publish_ready_html(self, html_content, metadata, blog_doc):
        """Create final publish-ready HTML with all metadata"""

        # Get the content with images
        if blog_doc.get("html_with_images"):
            html_content = blog_doc["html_with_images"]

        # Extract body content and clean it
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html_content, re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
        else:
            body_content = html_content

        # Clean up any malformed HTML
        body_content = body_content.replace("</article><footer>", "")
        body_content = re.sub(
            r"<footer>.*?</footer>", "", body_content, flags=re.DOTALL
        )

        # Remove duplicate conclusion sections
        # Count how many times "Conclusion" appears as h2
        conclusion_matches = re.findall(
            r"<h2[^>]*>Conclusion</h2>", body_content, re.IGNORECASE
        )
        if len(conclusion_matches) > 1:
            # Keep only the first conclusion section
            parts = body_content.split('<section class="conclusion">')
            if len(parts) > 2:
                # Rebuild with only one conclusion section
                body_content = parts[0] + '<section class="conclusion">' + parts[1]

        # Remove any duplicate "Conclusion: " headings within content
        body_content = re.sub(
            r"<h2[^>]*>Conclusion:\s*[^<]+</h2>", "", body_content, flags=re.DOTALL
        )

        # Clean duplicate consecutive figures
        pattern = r'(<figure[^>]*class="[^"]*"[^>]*>.*?</figure>)\s*\1'
        while re.search(pattern, body_content, re.DOTALL):
            body_content = re.sub(pattern, r"\1", body_content, flags=re.DOTALL)

        # Ensure article tag is properly closed
        if "<article>" in body_content:
            # Remove any existing closing tags
            body_content = body_content.replace("</article>", "")
            # Find where article content should end (before footer if any)
            article_end = len(body_content)
            # Add closing tag at the right place
            body_content = body_content[:article_end] + "\n    </article>"

        # Build the complete HTML document
        html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        
        <!-- Primary Meta Tags -->
        <title>{metadata["meta_title"]}</title>
        <meta name="title" content="{metadata["meta_title"]}">
        <meta name="description" content="{metadata["meta_description"]}">
        <meta name="keywords" content="{metadata["meta_keywords"]}">
        <meta name="author" content="{metadata["author"]}">
        <meta name="robots" content="index, follow">
        <link rel="canonical" href="{metadata["canonical_url"]}">
        
        <!-- Open Graph / Facebook -->
        <meta property="og:type" content="article">
        <meta property="og:url" content="{metadata["canonical_url"]}">
        <meta property="og:title" content="{metadata["og_title"]}">
        <meta property="og:description" content="{metadata["og_description"]}">"""

        # Add featured image meta if available
        if metadata["featured_image"]["url"]:
            html += f"""
        <meta property="og:image" content="{metadata['featured_image']['url']}">
        <meta property="og:image:alt" content="{metadata['featured_image']['alt_text']}">"""

        html += f"""
        
        <!-- Twitter -->
        <meta property="twitter:card" content="summary_large_image">
        <meta property="twitter:url" content="{metadata["canonical_url"]}">
        <meta property="twitter:title" content="{metadata["meta_title"]}">
        <meta property="twitter:description" content="{metadata["meta_description"]}">"""

        if metadata["featured_image"]["url"]:
            html += f"""
        <meta property="twitter:image" content="{metadata['featured_image']['url']}">"""

        html += f"""
        
        <!-- Schema.org Structured Data -->
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": "{metadata["post_title"]}",
            "description": "{metadata["meta_description"]}",
            "image": "{metadata['featured_image']['url']}",
            "author": {{
                "@type": "Organization",
                "name": "{metadata["author"]}",
                "url": "{self.product_knowledge['main_website']}"
            }},
            "publisher": {{
                "@type": "Organization",
                "name": "{metadata["publisher"]}",
                "url": "{self.product_knowledge['main_website']}"
            }},
            "datePublished": "{datetime.utcnow().isoformat()}Z",
            "dateModified": "{datetime.utcnow().isoformat()}Z",
            "mainEntityOfPage": {{
                "@type": "WebPage",
                "@id": "{metadata["canonical_url"]}"
            }}
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
                background-color: #fff;
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
                margin: 40px 0 20px;
                font-weight: 600;
            }}
            
            h3 {{ 
                color: #34495e; 
                font-size: 1.4em; 
                margin: 30px 0 15px;
                font-weight: 600;
            }}
            
            p {{ 
                margin-bottom: 15px; 
                text-align: justify; 
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
            
            .opening {{ 
                font-size: 1.1em; 
                color: #555; 
                margin-bottom: 30px; 
                font-style: italic; 
            }}
            
            .cta-section {{
                background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
                padding: 30px;
                border-radius: 8px;
                margin: 40px 0;
                border: 2px solid #3498db;
            }}
            
            .cta-section h3 {{
                color: #1976d2;
                margin-top: 0;
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
            
            .faq-section {{
                background-color: #f9f9f9;
                padding: 25px;
                border-radius: 8px;
                margin: 40px 0;
            }}
            
            .faq-item {{
                margin-bottom: 20px;
            }}
            
            .faq-item h4 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            
            @media (max-width: 768px) {{
                body {{ padding: 15px; }}
                h1 {{ font-size: 2em; }}
                h2 {{ font-size: 1.5em; }}
            }}
            
            @media print {{
                .cta-section {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <!-- Post Metadata for CMS Integration -->
        <meta name="post-title" content="{metadata["post_title"]}">
        <meta name="post-description" content="{metadata["post_description"]}">
        <meta name="post-slug" content="{metadata["slug"]}">
        
    {body_content}

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

        return html

    def generate_quality_check_step(self, blog_data, main_keyword, additional_keywords):
        """Lighter quality check that preserves content quality and removes meta-commentary"""
        
        # First, clean all content from meta-commentary
        cleaned_blog_data = self._clean_all_content_sections(blog_data)
        
        # Generate original HTML with cleaned data
        original_html = self.generate_simple_html(cleaned_blog_data)

        # Analyze quality
        quality_report = self.analyze_blog_quality(
            cleaned_blog_data, main_keyword, additional_keywords
        )

        if quality_report["needs_enhancement"]:
            # Light enhancement only
            enhanced_data = self.enhance_blog_content(
                cleaned_blog_data, quality_report, main_keyword, additional_keywords
            )

            # Re-analyze
            new_report = self.analyze_blog_quality(
                enhanced_data, main_keyword, additional_keywords
            )

            # Generate enhanced HTML
            enhanced_html = self.generate_simple_html(enhanced_data)

            return {
                "original_report": quality_report,
                "enhanced_report": new_report,
                "enhanced_blog_data": enhanced_data,
                "original_html": original_html,
                "enhanced_html": enhanced_html,
                "enhancement_done": True,
                "final_word_count": new_report["word_count"],
            }

        return {
            "original_report": quality_report,
            "enhanced_report": quality_report,
            "enhanced_blog_data": cleaned_blog_data,
            "original_html": original_html,
            "enhanced_html": original_html,
            "enhancement_done": False,
            "final_word_count": quality_report["word_count"],
        }


    def generate_blog_metadata(self, blog_doc, main_keyword, additional_keywords):
        """Generate comprehensive metadata for the blog"""

        # Extract existing title or generate new one
        existing_title = blog_doc.get("h1", "") or blog_doc.get("title", "")

        # Generate Post Title (for display)
        post_title = self._generate_post_title(
            existing_title, main_keyword, additional_keywords
        )

        # Generate Meta Title (for SEO - can be different from post title)
        meta_title = self._generate_meta_title(post_title, main_keyword)

        # Generate slug from title
        slug = self._generate_slug(post_title, main_keyword)

        # Generate Meta Description
        meta_description = self._generate_meta_description(
            post_title, blog_doc.get("opening_paragraph", ""), main_keyword
        )

        # Generate Post Description (longer than meta description)
        post_description = self._generate_post_description(
            blog_doc.get("opening_paragraph", ""), main_keyword, additional_keywords
        )

        # Get featured image from integrated images
        featured_image = self._extract_featured_image(blog_doc)

        # Generate meta keywords
        all_keywords = [main_keyword] + additional_keywords
        meta_keywords = ", ".join(all_keywords[:8])

        # Generate Open Graph tags
        og_title = meta_title[:60]
        og_description = meta_description[:160]

        metadata = {
            "post_title": post_title,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "post_description": post_description,
            "featured_image": featured_image,
            "slug": slug,
            "meta_keywords": meta_keywords,
            "og_title": og_title,
            "og_description": og_description,
            "canonical_url": f"{self.product_knowledge['main_website']}blog/{slug}",
            "author": self.product_knowledge.get("company_name", "Smart Weld"),
            "publisher": self.product_knowledge.get("company_name", "Smart Weld"),
        }

        return metadata


    def _generate_post_title(self, existing_title, main_keyword, additional_keywords):
        """Generate the main post title"""
        # Clean existing title first
        if existing_title:
            existing_title = self._clean_title_text(existing_title)
            if len(existing_title) > 30 and main_keyword.lower() in existing_title.lower():
                return existing_title[:70]
        
        prompt = f"""Generate a compelling blog post title for display.

    Main keyword: {main_keyword}
    Additional keywords: {', '.join(additional_keywords[:2])}

    Requirements:
    1. 40-70 characters
    2. Include main keyword naturally
    3. Engaging and benefit-focused
    4. Professional tone
    5. Actionable or intriguing
    6. NO markdown symbols or formatting
    7. Plain text only

    Generate ONLY the title text."""

        title = self._generate_text(prompt)
        title = self._clean_title_text(title)
        
        # Ensure main keyword is included
        if main_keyword.lower() not in title.lower():
            title = f"{main_keyword}: {title}"
        
        # Trim if too long
        if len(title) > 70:
            title = title[:67] + '...'
        
        return title


    def _generate_meta_title(self, post_title, main_keyword):
        """Generate SEO meta title"""
        prompt = f"""Generate an SEO meta title based on this post title.

    Post title: {post_title}
    Main keyword: {main_keyword}

    Requirements:
    1. 50-60 characters maximum (STRICT)
    2. Include main keyword at the beginning if possible
    3. Add company name at the end with | separator if space allows
    4. Optimized for search engines
    5. NO markdown formatting (no #, ##, *, etc.)
    6. Plain text only

    Generate ONLY the meta title text."""

        meta_title = self._generate_text(prompt)
        
        # Clean the meta title
        meta_title = self._clean_title_text(meta_title)
        
        # Add company name if not present and there's space
        company_name = self.product_knowledge.get('company_name', 'SmartWeld')
        if company_name not in meta_title and len(meta_title) < 50:
            meta_title = f"{meta_title} | {company_name}"
        
        # Ensure it's not too long
        if len(meta_title) > 60:
            # If it has company name, try removing it first
            if ' | ' in meta_title:
                meta_title = meta_title.split(' | ')[0]
            else:
                meta_title = meta_title[:57] + '...'
        
        return meta_title


    def _generate_slug(self, title, main_keyword):
        """Generate URL-friendly slug"""
        # Start with title
        slug = title.lower()

        # Remove special characters and clean
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        slug = slug.strip("-")

        # Ensure it's not too long
        if len(slug) > 50:
            # Try to cut at word boundary
            slug = slug[:50].rsplit("-", 1)[0]

        # Ensure main keyword is in slug
        main_keyword_slug = main_keyword.lower().replace(" ", "-")
        if main_keyword_slug not in slug and len(slug) < 40:
            slug = f"{main_keyword_slug}-{slug}"

        return slug


    def _generate_meta_description(self, title, opening_paragraph, main_keyword):
        """Generate SEO meta description (155-160 chars)"""
        if opening_paragraph and len(opening_paragraph) > 100:
            # Clean and use opening
            clean_opening = re.sub("<.*?>", "", opening_paragraph)
            meta_desc = clean_opening[:150]
        else:
            prompt = f"""Generate a meta description for SEO.

    Title: {title}
    Topic: {main_keyword}

    Requirements:
    1. 150-160 characters exactly
    2. Include main keyword naturally
    3. Compelling call to action
    4. Describe the value/benefit

    Generate ONLY the meta description."""

            meta_desc = self._generate_text(prompt).strip()

        # Ensure proper length
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."
        elif len(meta_desc) < 150:
            meta_desc += f" Learn more about {main_keyword}."

        return meta_desc


    def _generate_post_description(self, opening_paragraph, main_keyword, keywords):
        """Generate longer post description (200-300 chars)"""
        prompt = f"""Generate a compelling post description.

    Topic: {main_keyword}
    Keywords: {', '.join(keywords[:3])}
    Opening: {opening_paragraph[:100] if opening_paragraph else 'N/A'}

    Requirements:
    1. 200-300 characters
    2. Expand on the blog's value proposition
    3. Include what readers will learn
    4. Professional and engaging

    Generate ONLY the description."""

        description = self._generate_text(prompt).strip()

        # Clean HTML if present
        description = re.sub("<.*?>", "", description)

        if len(description) > 300:
            description = description[:297] + "..."

        return description


    def _extract_featured_image(self, blog_doc):
        """Extract featured image from integrated images"""
        integrated_images = blog_doc.get("integrated_images", [])

        if integrated_images and len(integrated_images) > 0:
            featured = integrated_images[0]
            return {
                "url": featured.get("url", ""),
                "alt_text": featured.get("alt_text", ""),
                "title": featured.get("title", featured.get("alt_text", "")),
            }

        return {"url": "", "alt_text": "Blog featured image", "title": "Featured image"}

    def _clean_all_content_sections(self, blog_data):
        """Clean all content sections from meta-commentary"""
        cleaned_data = blog_data.copy()
        
        # Clean each content section
        if 'content_sections' in cleaned_data:
            cleaned_sections = []
            for section in cleaned_data['content_sections']:
                cleaned_section = self._clean_meta_commentary(section)
                cleaned_sections.append(cleaned_section)
            cleaned_data['content_sections'] = cleaned_sections
        
        # Clean CTA
        if 'cta' in cleaned_data:
            cleaned_data['cta'] = self._clean_meta_commentary(cleaned_data['cta'])
        
        # Clean conclusion
        if 'conclusion' in cleaned_data:
            cleaned_data['conclusion'] = self._clean_meta_commentary(cleaned_data['conclusion'])
        
        # Clean opening paragraph
        if 'opening_paragraph' in cleaned_data:
            cleaned_data['opening_paragraph'] = self._clean_meta_commentary(cleaned_data['opening_paragraph'])
        
        return cleaned_data
    def create_publish_ready_html(self, html_content, metadata, blog_doc):
        """Create final publish-ready HTML with all metadata"""

        # Ensure we have the right content
        if blog_doc.get("html_with_images"):
            html_content = blog_doc["html_with_images"]

        # Extract body content
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html_content, re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
        else:
            body_content = html_content

        # Build complete HTML
        html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        
        <!-- Primary Meta Tags -->
        <title>{metadata["meta_title"]}</title>
        <meta name="title" content="{metadata["meta_title"]}">
        <meta name="description" content="{metadata["meta_description"]}">
        <meta name="keywords" content="{metadata["meta_keywords"]}">
        <meta name="author" content="{metadata["author"]}">
        <meta name="robots" content="index, follow">
        <link rel="canonical" href="{metadata["canonical_url"]}">
        
        <!-- Open Graph / Facebook -->
        <meta property="og:type" content="article">
        <meta property="og:url" content="{metadata["canonical_url"]}">
        <meta property="og:title" content="{metadata["og_title"]}">
        <meta property="og:description" content="{metadata["og_description"]}">"""

        # Add featured image meta if available
        if metadata["featured_image"]["url"]:
            html += f"""
        <meta property="og:image" content="{metadata['featured_image']['url']}">
        <meta property="og:image:alt" content="{metadata['featured_image']['alt_text']}">"""

        html += f"""
        
        <!-- Twitter -->
        <meta property="twitter:card" content="summary_large_image">
        <meta property="twitter:url" content="{metadata["canonical_url"]}">
        <meta property="twitter:title" content="{metadata["meta_title"]}">
        <meta property="twitter:description" content="{metadata["meta_description"]}">"""

        if metadata["featured_image"]["url"]:
            html += f"""
        <meta property="twitter:image" content="{metadata['featured_image']['url']}">"""

        html += f"""
        
        <!-- Schema.org Structured Data -->
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": "{metadata["post_title"]}",
            "description": "{metadata["meta_description"]}",
            "image": "{metadata['featured_image']['url']}",
            "author": {{
                "@type": "Organization",
                "name": "{metadata["author"]}",
                "url": "{self.product_knowledge['main_website']}"
            }},
            "publisher": {{
                "@type": "Organization",
                "name": "{metadata["publisher"]}",
                "url": "{self.product_knowledge['main_website']}"
            }},
            "datePublished": "{datetime.utcnow().isoformat()}Z",
            "dateModified": "{datetime.utcnow().isoformat()}Z",
            "mainEntityOfPage": {{
                "@type": "WebPage",
                "@id": "{metadata["canonical_url"]}"
            }}
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
                background-color: #fff;
            }}
            
            h1 {{ color: #1a1a1a; font-size: 2.5em; margin-bottom: 20px; line-height: 1.2; }}
            h2 {{ color: #2c3e50; font-size: 1.8em; margin: 40px 0 20px; }}
            h3 {{ color: #34495e; font-size: 1.4em; margin: 30px 0 15px; }}
            
            p {{ margin-bottom: 15px; text-align: justify; }}
            
            ul, ol {{ margin-bottom: 20px; padding-left: 30px; }}
            li {{ margin-bottom: 8px; }}
            
            figure {{ margin: 30px 0; text-align: center; }}
            figure img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            figcaption {{ margin-top: 10px; font-style: italic; color: #666; font-size: 0.9em; }}
            
            .opening {{ font-size: 1.1em; color: #555; margin-bottom: 30px; font-style: italic; }}
            
            .cta-section {{
                background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
                padding: 30px;
                border-radius: 8px;
                margin: 40px 0;
                border: 2px solid #3498db;
            }}
            
            .conclusion {{ border-top: 2px solid #e0e0e0; padding-top: 30px; margin-top: 40px; }}
            
            a {{ color: #3498db; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            
            @media print {{
                .cta-section {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <!-- Post Title for Display -->
        <meta name="post-title" content="{metadata["post_title"]}">
        <meta name="post-description" content="{metadata["post_description"]}">
        
    {body_content}

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

        return html
