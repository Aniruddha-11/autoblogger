import requests
from bs4 import BeautifulSoup
from config import Config
import time
import json
from urllib.parse import quote_plus, urlparse
import hashlib

class ImageSearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Prioritize reliable image sources
        self.preferred_domains = [
            'wikipedia.org',
            'wikimedia.org',
            'pexels.com',
            'unsplash.com',
            'pixabay.com',
            'freepik.com',
            'istockphoto.com',
            'gettyimages.com',
            'shutterstock.com',
            'adobe.com',
            'canva.com',
            'flaticon.com',
            'medium.com',
            'wordpress.com',
            'blogspot.com'
        ]
        
        # Domains to avoid
        self.blocked_domains = [
            'pinterest.com',  # Often has access issues
            'instagram.com',  # Requires login
            'facebook.com',   # Requires login
            'twitter.com',    # May require login
            'linkedin.com',   # Requires login
        ]
    
    def is_valid_image_url(self, url):
        """Check if image URL is valid and accessible"""
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        try:
            # Parse URL to check domain
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Skip blocked domains
            if any(blocked in domain for blocked in self.blocked_domains):
                return False
            
            # Quick HEAD request to check if URL is accessible
            response = requests.head(url, headers=self.headers, timeout=3, allow_redirects=True)
            
            # Check if response is successful
            if response.status_code != 200:
                return False
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'jpeg', 'jpg', 'png', 'gif', 'webp']):
                return False
            
            return True
            
        except Exception as e:
            print(f"URL validation failed for {url}: {str(e)}")
            return False
    
    def get_domain_priority(self, url):
        """Get priority score for domain (lower is better)"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if it's a preferred domain
            for i, pref_domain in enumerate(self.preferred_domains):
                if pref_domain in domain:
                    return i  # Return position in preferred list
            
            # If not in preferred list, return high number
            return 999
        except:
            return 999
    
    def search_duckduckgo_images(self, query, count=5):
        """Search DuckDuckGo for images with validation"""
        images = []
        valid_images = []
        
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
                        
                        # Get more results than needed to account for invalid ones
                        for idx, result in enumerate(results[:count*3]):
                            image_url = result.get('image', '')
                            
                            # Skip if no URL
                            if not image_url:
                                continue
                            
                            # Create image data
                            image_data = {
                                'url': image_url,
                                'thumbnail': result.get('thumbnail', ''),
                                'alt_text': result.get('title', '') or f'{query} image {idx+1}',
                                'title': result.get('title', ''),
                                'source': result.get('source', '') or 'DuckDuckGo',
                                'width': result.get('width', 800),
                                'height': result.get('height', 600),
                                'domain': urlparse(image_url).netloc if image_url else 'Unknown'
                            }
                            
                            images.append(image_data)
                            
                    except Exception as e:
                        print(f"Error parsing DuckDuckGo results: {str(e)}")
            
            # Validate images
            print(f"Validating {len(images)} images from DuckDuckGo...")
            for img in images:
                if self.is_valid_image_url(img['url']):
                    img['priority'] = self.get_domain_priority(img['url'])
                    valid_images.append(img)
                    print(f"✓ Valid image from {img['domain']}")
                else:
                    print(f"✗ Invalid/inaccessible image from {img['domain']}")
                
                if len(valid_images) >= count:
                    break
            
            # Sort by priority (prefer reliable sources)
            valid_images.sort(key=lambda x: x.get('priority', 999))
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching DuckDuckGo images: {str(e)}")
        
        return valid_images[:count]
    
    def search_bing_images(self, query, count=5):
        """Search Bing for images with validation"""
        images = []
        valid_images = []
        
        try:
            search_url = f"https://www.bing.com/images/search?q={quote_plus(query)}&form=HDRSC2"
            
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find image elements
            img_elements = soup.find_all('a', class_='iusc')[:count*3]
            
            for idx, elem in enumerate(img_elements):
                try:
                    # Extract metadata from the element
                    m_attr = elem.get('m', '{}')
                    metadata = json.loads(m_attr)
                    
                    image_url = metadata.get('murl', '')
                    
                    if not image_url:
                        continue
                    
                    image_data = {
                        'url': image_url,
                        'thumbnail': metadata.get('turl', ''),
                        'alt_text': metadata.get('t', '') or f'{query} image {idx+1}',
                        'title': metadata.get('t', ''),
                        'source': 'Bing Images',
                        'width': metadata.get('mw', 800),
                        'height': metadata.get('mh', 600),
                        'domain': urlparse(image_url).netloc if image_url else 'Unknown'
                    }
                    
                    images.append(image_data)
                    
                except Exception as e:
                    continue
            
            # Validate images
            print(f"Validating {len(images)} images from Bing...")
            for img in images:
                if self.is_valid_image_url(img['url']):
                    img['priority'] = self.get_domain_priority(img['url'])
                    valid_images.append(img)
                    print(f"✓ Valid image from {img['domain']}")
                else:
                    print(f"✗ Invalid/inaccessible image from {img['domain']}")
                
                if len(valid_images) >= count:
                    break
            
            # Sort by priority
            valid_images.sort(key=lambda x: x.get('priority', 999))
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching Bing images: {str(e)}")
        
        return valid_images[:count]
    
    def search_free_stock_images(self, query, count=3):
        """Search free stock photo sites for reliable images"""
        valid_images = []
        
        # Search Pexels (has good API but we'll use web scraping)
        try:
            pexels_url = f"https://www.pexels.com/search/{quote_plus(query)}/"
            response = requests.get(pexels_url, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                img_elements = soup.find_all('img', class_='photo-item__img')[:count]
                
                for idx, img in enumerate(img_elements):
                    src = img.get('src') or img.get('data-src')
                    if src and src.startswith('http'):
                        valid_images.append({
                            'url': src.split('?')[0],  # Remove query parameters
                            'thumbnail': src,
                            'alt_text': img.get('alt', f'{query} stock photo {idx+1}'),
                            'title': img.get('alt', f'{query} stock photo'),
                            'source': 'Pexels',
                            'domain': 'pexels.com',
                            'priority': 0  # High priority
                        })
                print(f"Found {len(valid_images)} images from Pexels")
        except Exception as e:
            print(f"Error searching Pexels: {str(e)}")
        
        return valid_images
    
    def search_images_for_keywords(self, main_keyword, keywords):
        """Search images for all keywords with validation"""
        all_images = {
            'main_keyword': main_keyword,
            'keywords': keywords,
            'images': {},
            'total_images': 0
        }
        
        # Search for main keyword
        print(f"Searching images for main keyword: {main_keyword}")
        
        # Try free stock images first for main keyword
        main_images = self.search_free_stock_images(main_keyword, 2)
        
        # Then try DuckDuckGo
        if len(main_images) < 5:
            ddg_images = self.search_duckduckgo_images(main_keyword, 5 - len(main_images))
            main_images.extend(ddg_images)
        
        # If still not enough, try Bing
        if len(main_images) < 5:
            bing_images = self.search_bing_images(main_keyword, 5 - len(main_images))
            main_images.extend(bing_images)
        
        # If still no images, use placeholder
        if len(main_images) == 0:
            main_images.append({
                'url': f'https://via.placeholder.com/800x600.png?text={quote_plus(main_keyword)}',
                'thumbnail': f'https://via.placeholder.com/400x300.png?text={quote_plus(main_keyword)}',
                'alt_text': f'{main_keyword} placeholder image',
                'title': f'{main_keyword} image',
                'source': 'Placeholder',
                'domain': 'via.placeholder.com'
            })
        
        all_images['images']['main'] = main_images
        all_images['total_images'] += len(main_images)
        
        # Search for each additional keyword
        for keyword in keywords:
            print(f"Searching images for keyword: {keyword}")
            
            keyword_images = []
            
            # Search with DuckDuckGo first
            keyword_images = self.search_duckduckgo_images(keyword, 4)
            
            # If not enough, try Bing
            if len(keyword_images) < 2:
                bing_images = self.search_bing_images(keyword, 4 - len(keyword_images))
                keyword_images.extend(bing_images)
            
            # Use placeholder if no valid images found
            if len(keyword_images) == 0:
                keyword_images.append({
                    'url': f'https://via.placeholder.com/800x600.png?text={quote_plus(keyword)}',
                    'thumbnail': f'https://via.placeholder.com/400x300.png?text={quote_plus(keyword)}',
                    'alt_text': f'{keyword} placeholder image',
                    'title': f'{keyword} image',
                    'source': 'Placeholder',
                    'domain': 'via.placeholder.com'
                })
            
            all_images['images'][keyword] = keyword_images
            all_images['total_images'] += len(keyword_images)
            
            time.sleep(1.5)  # Rate limiting between searches
        
        print(f"Total valid images found: {all_images['total_images']}")
        return all_images