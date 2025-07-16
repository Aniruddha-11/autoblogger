import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote_plus

class WeldingScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.welding_terms = [
            'welding', 'weld', 'fabrication', 'metal joining', 
            'arc welding', 'MIG', 'TIG', 'automated welding',
            'welding technology', 'industrial welding', 'smart weld'
        ]
    
    def clean_text(self, text):
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
        return text.strip()
    
    def is_welding_related(self, text):
        """Check if content is welding-related"""
        text_lower = text.lower()
        return any(term in text_lower for term in self.welding_terms)
    
    def scrape_duckduckgo(self, query):
        """Scrape DuckDuckGo search results"""
        results = []
        try:
            # Add welding-specific terms to query
            enhanced_query = f"{query} welding industry technology"
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(enhanced_query)}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all result links
            for result in soup.find_all('div', class_='web-result', limit=5):
                title_elem = result.find('h2', class_='result__title')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and snippet_elem:
                    title = self.clean_text(title_elem.get_text())
                    snippet = self.clean_text(snippet_elem.get_text())
                    
                    # Only include welding-related content
                    if self.is_welding_related(title + ' ' + snippet):
                        results.append({
                            'title': title,
                            'snippet': snippet,
                            'source': 'DuckDuckGo'
                        })
            
            time.sleep(1)  # Be respectful with rate limiting
            
        except Exception as e:
            print(f"Error scraping DuckDuckGo: {str(e)}")
        
        return results
    
    def scrape_bing(self, query):
        """Scrape Bing search results"""
        results = []
        try:
            # Add welding context to query
            enhanced_query = f"{query} welding manufacturing smart weld"
            url = f"https://www.bing.com/search?q={quote_plus(enhanced_query)}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all search results
            for result in soup.find_all('li', class_='b_algo', limit=5):
                title_elem = result.find('h2')
                snippet_elem = result.find('div', class_='b_caption')
                
                if title_elem and snippet_elem:
                    title = self.clean_text(title_elem.get_text())
                    snippet = self.clean_text(snippet_elem.get_text())
                    
                    # Filter for welding content
                    if self.is_welding_related(title + ' ' + snippet):
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
        """Scrape welding-specific websites"""
        results = []
        welding_sites = [
            {
                'name': 'Welding Industry News',
                'search_url': f'https://www.thefabricator.com/search?q={quote_plus(keyword)}',
                'selector': 'article'
            }
        ]
        
        for site in welding_sites:
            try:
                response = requests.get(site['search_url'], headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                articles = soup.find_all(site['selector'], limit=3)
                for article in articles:
                    title = article.find(['h2', 'h3', 'h4'])
                    content = article.find(['p', 'div'])
                    
                    if title and content:
                        results.append({
                            'title': self.clean_text(title.get_text()),
                            'snippet': self.clean_text(content.get_text())[:200] + '...',
                            'source': site['name']
                        })
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error scraping {site['name']}: {str(e)}")
        
        return results
    
    def generate_smart_weld_context(self, keyword):
        """Generate context about Smart Weld product"""
        smart_weld_contexts = [
            f"Smart Weld technology revolutionizes {keyword} by providing automated precision and real-time monitoring.",
            f"In the context of {keyword}, Smart Weld offers intelligent welding solutions that reduce defects and increase productivity.",
            f"Smart Weld's advanced sensors and AI algorithms optimize {keyword} processes for superior weld quality.",
            f"When it comes to {keyword}, Smart Weld stands out with its innovative approach to automated welding control.",
            f"Smart Weld integrates seamlessly with {keyword} applications, delivering consistent results and reduced operational costs."
        ]
        
        return {
            'title': f'Smart Weld Solutions for {keyword}',
            'snippet': smart_weld_contexts[hash(keyword) % len(smart_weld_contexts)],
            'source': 'Smart Weld Context'
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
        main_results.extend(self.scrape_welding_specific_sites(main_keyword))
        main_results.append(self.generate_smart_weld_context(main_keyword))
        
        all_results['scraped_data']['main'] = main_results
        all_results['total_results'] += len(main_results)
        
        # Scrape for each additional keyword
        for keyword in keywords:
            print(f"Scraping for keyword: {keyword}")
            keyword_results = []
            
            # Combine keyword with welding terms
            keyword_results.extend(self.scrape_duckduckgo(keyword))
            keyword_results.extend(self.scrape_bing(keyword))
            keyword_results.append(self.generate_smart_weld_context(keyword))
            
            all_results['scraped_data'][keyword] = keyword_results
            all_results['total_results'] += len(keyword_results)
            
            # Rate limiting between keywords
            time.sleep(2)
        
        return all_results