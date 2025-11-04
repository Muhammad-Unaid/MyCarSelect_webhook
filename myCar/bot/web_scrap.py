import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .models import PageContent

def scrape_all_pages(domain, limit=20):
    visited = set()
    to_visit = [domain]
    base_domain = urlparse(domain).netloc  # Extract base domain

    while to_visit and len(visited) < limit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        
        print(f"Scraping: {url}")  # Progress dekho
        
        try:
            res = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if res.status_code != 200:
                print(f"❌ Status {res.status_code}: {url}")
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Remove script and style tags
            for tag in soup(["script", "style"]):
                tag.decompose()
            
            # Get title
            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else ""
            
            # Get clean text
            text = soup.get_text(" ", strip=True)
            
            # Save to DB
            PageContent.objects.update_or_create(
                url=url,
                defaults={
                    "title": title_text[:255],
                    "content": text[:5000]  # Increased limit
                }
            )
            print(f"✅ Saved: {url}")

            # Extract links from same domain only
            for link in soup.find_all("a", href=True):
                new_url = urljoin(url, link["href"])
                new_domain = urlparse(new_url).netloc
                
                # Only same domain
                if new_domain == base_domain and new_url not in visited:
                    to_visit.append(new_url)

            visited.add(url)
            
        except Exception as e:
            print(f"❌ Error on {url}: {e}")

    return visited