import scrapy
from scrapy_playwright.page import PageMethod
from ...items import MycrawlerItem
import re


class OpenAIComListingSpider(scrapy.Spider):
    name = "openai-com-listing"
    start_urls = ["https://openai.com/research/index/"]
    
    # Custom settings cho output file routes theo source
    custom_settings = {
        'FEEDS': {
            'data/OpenAI/openai-com-listing.json': {
                'format': 'json',
                'encoding': 'utf-8',
                'store_empty': False,
                'overwrite': True,
            },
        },
    }

    async def start(self):
        # Lấy URL từ start_urls hoặc từ command line argument
        if hasattr(self, 'start_url') and self.start_url:
            url = self.start_url
        elif self.start_urls:
            url = self.start_urls[0]
        else:
            url = "https://openai.com/research/index/"
        
        yield scrapy.Request(
            url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle", timeout=60000),
                    PageMethod("wait_for_timeout", 3000),  # Đợi thêm 3 giây để JS load xong
                ],
            },
            callback=self.parse
        )

    def parse(self, response):
        # Trang OpenAI research index sử dụng Next.js và load nội dung qua API
        # Extract title, link và date trực tiếp từ listing page, không vào detail page
        # CHỈ lấy links từ main content area, không lấy từ sidebar
        
        count = 0
        seen_links = set()
        
        # Tìm tất cả các links đến các bài research
        # Format: /index/[slug] (bài research)
        # Sẽ filter để loại bỏ sidebar links (chúng không có date)
        all_links = response.css("a[href]")
        
        for link in all_links:
            href = link.css("::attr(href)").get()
            if not href or href.startswith('#'):
                continue
            
            # Chỉ lấy các link có format /index/[slug] (bài research)
            if '/index/' not in href:
                continue
            
            # Bỏ qua các link không phải bài research cụ thể
            if href in ['/research/index/', '/research/', '/index/', '/research/index']:
                continue
            
            # Bỏ qua các link filter tabs (Publication, Conclusion, Milestone, Release)
            if href in ['/research/index/publication/', '/research/index/conclusion/', 
                        '/research/index/milestone/', '/research/index/release/',
                        '/research/index/publication', '/research/index/conclusion',
                        '/research/index/milestone', '/research/index/release']:
                continue
            
            # Làm sạch URL
            full_url = response.urljoin(href)
            if full_url in seen_links:
                continue
            
            # Chỉ lấy các URL có /index/ và có slug sau đó (không phải chỉ /index/)
            if '/index/' in full_url and full_url.count('/index/') == 1:
                # Kiểm tra có slug sau /index/ không
                parts = full_url.split('/index/')
                if len(parts) < 2 or not parts[1] or parts[1].strip() == '':
                    continue
            else:
                continue
            
            seen_links.add(full_url)
            
            # Extract title từ link
            title = link.css("::text").get()
            if not title or len(title.strip()) < 3:
                # Thử lấy từ các thẻ con
                title = link.css("h1::text, h2::text, h3::text, h4::text, h5::text, h6::text, span::text, div::text").get()
            
            # Làm sạch title
            if title:
                title = " ".join(title.split()).strip()
                if len(title) < 3:
                    title = None
            
            # Extract date từ listing page (tìm element date gần với link)
            date = self._extract_date_from_listing(link, response)
            
            # BỎ QUA các links không có date (thường là từ sidebar, không phải main listing)
            # Các links trong main listing page đều có date element gần đó
            if not date:
                continue
            
            # Chỉ yield item nếu có title
            if title:
                item = MycrawlerItem()
                item["title"] = title
                item["link"] = full_url
                item["date"] = date
                # Set các field không cần thiết về None
                item["description"] = None
                item["content"] = None
                item["content_length"] = 0
                item["authors"] = None
                item["tags"] = None
                item["images"] = None
                
                yield item
                count += 1
        
        # Log kết quả
        if count == 0:
            self.logger.warning("⚠️ Không tìm thấy dữ liệu. HTML length: %d", len(response.text))
            self.logger.debug("Response URL: %s", response.url)
        else:
            self.logger.info("✅ Found %d research articles from listing page", count)
    
    def _extract_date_from_listing(self, link_element, response):
        """Extract date từ listing page, tìm time element gần với link"""
        date = None
        
        # Strategy 1: Tìm time element trong cùng parent container với link
        # Dựa trên phân tích HTML: time element nằm trước link trong cùng container
        parent = link_element.xpath("..")
        if parent:
            # Tìm time element trong parent (có thể là sibling trước link)
            time_elements = parent.xpath(".//time")
            if time_elements:
                # Lấy time element đầu tiên (thường là gần nhất)
                time_elem = time_elements[0]
                # Ưu tiên lấy từ datetime attribute
                date_text = time_elem.xpath("@datetime").get()
                if date_text:
                    date = date_text.strip()
                else:
                    # Nếu không có datetime, lấy text
                    date_text = time_elem.xpath("normalize-space(.)").get()
                    if date_text:
                        date = date_text.strip()
        
        # Strategy 2: Tìm time element trong preceding siblings
        if not date:
            preceding = link_element.xpath("preceding-sibling::time")
            if preceding:
                date_text = preceding.xpath("@datetime").get()
                if date_text:
                    date = date_text.strip()
                else:
                    date_text = preceding.xpath("normalize-space(.)").get()
                    if date_text:
                        date = date_text.strip()
        
        # Strategy 3: Tìm time element trong ancestor container (cùng row/item)
        if not date:
            # Tìm ancestor container và tìm time trong đó
            ancestors = link_element.xpath("ancestor::*[position() <= 5]")  # Chỉ tìm 5 levels up
            for ancestor in ancestors:
                time_elem = ancestor.xpath(".//time[1]")
                if time_elem:
                    date_text = time_elem.xpath("@datetime").get()
                    if date_text:
                        date = date_text.strip()
                        break
        
        return date

