import requests
from bs4 import BeautifulSoup
from config import Config
import time
import json
from urllib.parse import quote_plus
import hashlib

class ImageSearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_duckduckgo_images(self, query, count=5):
        """Search DuckDuckGo for images"""
        images = []
        try:
            # DuckDuckGo image search URL
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}&iax=images&ia=images"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            # Parse the token from the page
            vqd_token = None
            for line in response.text.split('\n'):
                if 'vqd=' in line:
                    try:
                        vqd_token = line.split('vqd=')[1].split('&')[0].split('"')[0]
                        break
                    except:
                        continue
            
            if vqd_token:
                # Get actual image results
                api_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={quote_plus(query)}&vqd={vqd_token}&f=,,,&p=1"
                
                img_response = requests.get(api_url, headers=self.headers, timeout=10)
                
                if img_response.status_code == 200:
                    try:
                        data = img_response.json()
                        results = data.get('results', [])
                        
                        for idx, result in enumerate(results[:count]):
                            image_data = {
                                'url': result.get('image', ''),
                                'thumbnail': result.get('thumbnail', ''),
                                'alt_text': result.get('title', '') or f'{query} image {idx+1}',
                                'title': result.get('title', ''),
                                'source': result.get('source', '') or 'DuckDuckGo',
                                'width': result.get('width', 800),
                                'height': result.get('height', 600),
                                'domain': result.get('url', '').split('/')[2] if '/' in result.get('url', '') else 'Unknown'
                            }
                            
                            if image_data['url']:
                                images.append(image_data)
                    except:
                        pass
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching DuckDuckGo images: {str(e)}")
        
        return images
    
    def search_bing_images(self, query, count=5):
        """Search Bing for images"""
        images = []
        try:
            search_url = f"https://www.bing.com/images/search?q={quote_plus(query)}&form=HDRSC2"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find image elements
            img_elements = soup.find_all('a', class_='iusc')[:count]
            
            for idx, elem in enumerate(img_elements):
                try:
                    # Extract metadata from the element
                    m_attr = elem.get('m', '{}')
                    metadata = json.loads(m_attr)
                    
                    image_data = {
                        'url': metadata.get('murl', ''),
                        'thumbnail': metadata.get('turl', ''),
                        'alt_text': metadata.get('t', '') or f'{query} image {idx+1}',
                        'title': metadata.get('t', ''),
                        'source': 'Bing Images',
                        'width': metadata.get('mw', 800),
                        'height': metadata.get('mh', 600),
                        'domain': metadata.get('dom', 'Unknown')
                    }
                    
                    if image_data['url']:
                        images.append(image_data)
                except:
                    continue
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching Bing images: {str(e)}")
        
        return images
    
    def search_images_for_keywords(self, main_keyword, keywords):
        """Search images for all keywords with welding context"""
        all_images = {
            'main_keyword': main_keyword,
            'keywords': keywords,
            'images': {},
            'total_images': 0
        }
        
        # Search for main keyword with welding context
        print(f"Searching images for main keyword: {main_keyword}")
        main_query = f"{main_keyword} welding industry"
        
        # Try DuckDuckGo first
        main_images = self.search_duckduckgo_images(main_query, 5)
        
        # If not enough images, try Bing
        if len(main_images) < 3:
            bing_images = self.search_bing_images(main_query, 5 - len(main_images))
            main_images.extend(bing_images)
        
        all_images['images']['main'] = main_images
        all_images['total_images'] += len(main_images)
        
        # Search for each additional keyword
        for keyword in keywords:
            print(f"Searching images for keyword: {keyword}")
            
            # Add welding context to keyword
            keyword_query = f"{keyword} welding"
            
            # Search with DuckDuckGo
            keyword_images = self.search_duckduckgo_images(keyword_query, 4)
            
            # If not enough, try Bing
            if len(keyword_images) < 2:
                bing_images = self.search_bing_images(keyword_query, 4 - len(keyword_images))
                keyword_images.extend(bing_images)
            
            all_images['images'][keyword] = keyword_images
            all_images['total_images'] += len(keyword_images)
            
            time.sleep(1.5)  # Rate limiting between searches
        
        return all_images