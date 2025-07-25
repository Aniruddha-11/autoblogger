import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote_plus

class WeldingScraper:  # Keep the same class name for compatibility
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Make the terms generic instead of welding-specific
        self.relevant_terms = []  # No specific terms needed for generic scraping
    
    def clean_text(self, text):
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
        return text.strip()
    
    def is_relevant_content(self, text):
        """Check if content is relevant - for generic scraping, all content is relevant"""
        return True  # Accept all content for generic blogs
    
    def scrape_duckduckgo(self, query):
        """Scrape DuckDuckGo search results"""
        results = []
        try:
            # Keep the query as-is for generic topics
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.find_all('div', class_='web-result', limit=5):
                title_elem = result.find('h2', class_='result__title')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and snippet_elem:
                    title = self.clean_text(title_elem.get_text())
                    snippet = self.clean_text(snippet_elem.get_text())
                    
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'source': 'DuckDuckGo'
                    })
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping DuckDuckGo: {str(e)}")
        
        return results
    
    def scrape_bing(self, query):
        """Scrape Bing search results"""
        results = []
        try:
            url = f"https://www.bing.com/search?q={quote_plus(query)}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.find_all('li', class_='b_algo', limit=5):
                title_elem = result.find('h2')
                snippet_elem = result.find('div', class_='b_caption')
                
                if title_elem and snippet_elem:
                    title = self.clean_text(title_elem.get_text())
                    snippet = self.clean_text(snippet_elem.get_text())
                    
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'source': 'Bing'
                    })
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping Bing: {str(e)}")
        
        return results
    
    def scrape_welding_specific_sites(self, keyword):
        """Generic site scraping - renamed but kept for compatibility"""
        # For generic blogs, we don't scrape specific sites
        return []
    
    def generate_smart_weld_context(self, keyword):
        """Generate context about Shothik AI product if relevant"""
        # Check if keyword is related to writing/content
        writing_keywords = ['writing', 'content', 'ai', 'paraphrase', 'humanize', 'grammar', 
                           'seo', 'blog', 'article', 'essay', 'plagiarism', 'detection',
                           'translation', 'summarize', 'research', 'academic']
        
        if any(term in keyword.lower() for term in writing_keywords):
            shothik_contexts = [
                f"Shothik AI revolutionizes {keyword} with advanced AI-powered tools for paraphrasing, humanizing, and content enhancement.",
                f"When it comes to {keyword}, Shothik AI offers comprehensive solutions including AI detection bypass and professional writing assistance.",
                f"Shothik AI's intelligent platform transforms {keyword} workflows with tools that save time and improve quality.",
                f"For {keyword} professionals, Shothik AI provides an all-in-one solution with humanization, grammar checking, and translation features.",
                f"Master {keyword} with Shothik AI's suite of tools designed for students, writers, and content creators."
            ]
            
            return {
                'title': f'Shothik AI Solutions for {keyword}',
                'snippet': shothik_contexts[hash(keyword) % len(shothik_contexts)],
                'source': 'Shothik AI Context'
            }
        
        # For non-writing topics, generate generic context
        generic_contexts = [
            f"Explore comprehensive insights and solutions for {keyword} in this detailed guide.",
            f"Understanding {keyword}: key concepts, best practices, and practical applications.",
            f"Everything you need to know about {keyword} - from basics to advanced strategies.",
            f"Mastering {keyword}: expert tips, techniques, and industry insights.",
            f"The complete guide to {keyword} - practical approaches and proven methods."
        ]
        
        return {
            'title': f'Comprehensive Guide to {keyword}',
            'snippet': generic_contexts[hash(keyword) % len(generic_contexts)],
            'source': 'General Context'
        }
    
    def scrape_for_keywords(self, main_keyword, keywords):
        """Main scraping method for all keywords"""
        all_results = {
            'main_keyword': main_keyword,
            'keywords': keywords,
            'scraped_data': {},
            'total_results': 0
        }
        
        # Scrape for main keyword
        print(f"Scraping for main keyword: {main_keyword}")
        main_results = []
        main_results.extend(self.scrape_duckduckgo(main_keyword))
        main_results.extend(self.scrape_bing(main_keyword))
        # Skip welding-specific sites for generic topics
        main_results.append(self.generate_smart_weld_context(main_keyword))
        
        all_results['scraped_data']['main'] = main_results
        all_results['total_results'] += len(main_results)
        
        # Scrape for each additional keyword
        for keyword in keywords:
            print(f"Scraping for keyword: {keyword}")
            keyword_results = []
            
            keyword_results.extend(self.scrape_duckduckgo(keyword))
            keyword_results.extend(self.scrape_bing(keyword))
            keyword_results.append(self.generate_smart_weld_context(keyword))
            
            all_results['scraped_data'][keyword] = keyword_results
            all_results['total_results'] += len(keyword_results)
            
            time.sleep(2)
        
        return all_results