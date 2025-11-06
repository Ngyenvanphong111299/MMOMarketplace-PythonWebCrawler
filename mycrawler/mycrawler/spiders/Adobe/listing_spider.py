import scrapy
from scrapy_playwright.page import PageMethod
from ...items import MycrawlerItem
import re


class AdobeComListingSpider(scrapy.Spider):
    name = "adobe-com-listing"
    start_urls = ["https://techcrunch.com/tag/adobe/"]
    
    # Custom settings cho output file routes theo source
    custom_settings = {
        'FEEDS': {
            'data/Adobe/adobe-com-listing.json': {
                'format': 'json',
                'encoding': 'utf-8',
                'store_empty': False,
                'overwrite': True,
            },
        },
    }

    async def start(self):
        """Khởi tạo và crawl trang listing"""
        # Lấy URL từ start_urls hoặc từ command line argument
        if hasattr(self, 'start_url') and self.start_url:
            url = self.start_url
        elif self.start_urls:
            url = self.start_urls[0]
        else:
            url = "https://techcrunch.com/tag/adobe/"
        
        yield scrapy.Request(
            url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle", timeout=60000),
                        PageMethod("wait_for_timeout", 5000),  # Đợi 5 giây để JS load xong
                        # Scroll nhiều lần để trigger lazy load và infinite scroll
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight / 3)"),
                        PageMethod("wait_for_timeout", 2000),
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight * 2 / 3)"),
                        PageMethod("wait_for_timeout", 2000),
                        PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                        PageMethod("wait_for_timeout", 3000),  # Đợi sau khi scroll đến cuối
                        # Scroll lại lên đầu để đảm bảo tất cả content đã render
                        PageMethod("evaluate", "window.scrollTo(0, 0)"),
                        PageMethod("wait_for_timeout", 2000),
                    ],
                },
            callback=self.parse
        )

    def parse(self, response):
        """Parse listing page từ TechCrunch tag page về Adobe"""
        # Crawl từ TechCrunch tag page: https://techcrunch.com/tag/adobe/
        # Extract title, link và date từ các articles trên TechCrunch
        
        count = 0
        # Sử dụng class-level seen_links để tránh duplicates
        if not hasattr(self, '_seen_links'):
            self._seen_links = set()
        seen_links = self._seen_links
        
        self.logger.debug(f"Parsing URL: {response.url}")
        self.logger.debug(f"HTML length: {len(response.text)}")
        
        # Strategy 1: Tìm các article elements trên TechCrunch
        # TechCrunch sử dụng article tags hoặc post-block elements
        articles = response.css(
            "article, "
            "[class*='post-block'], "
            "[class*='river-block'], "
            "[class*='post-title'], "
            ".post-block"
        )
        
        for article in articles:
            # Tìm link trong article - TechCrunch thường có link trong heading hoặc article
            link = article.css(
                "h2 a::attr(href), "
                "h3 a::attr(href), "
                "h4 a::attr(href), "
                "[class*='post-title'] a::attr(href), "
                "[class*='river-block'] a::attr(href), "
                "a[href]::attr(href)"
            ).get()
            
            if not link or link.startswith('#') or link.startswith('javascript:'):
                continue
            
            # Làm sạch URL
            full_url = response.urljoin(link)
            if full_url in seen_links:
                continue
            
            # Chỉ lấy các URL từ TechCrunch về Adobe
            if 'techcrunch.com' not in full_url:
                continue
            
            # Bỏ qua các link không phải bài viết
            if any(skip in full_url for skip in ['/tag/', '/author/', '/category/', '/about/', '/contact/']):
                continue
            
            seen_links.add(full_url)
            
            # Extract title từ article - TechCrunch format
            title = article.css(
                "h2 a::text, "
                "h3 a::text, "
                "h4 a::text, "
                "h2::text, "
                "h3::text, "
                "h4::text, "
                "[class*='post-title']::text, "
                "[class*='river-block'] a::text"
            ).get()
            if not title:
                # Thử lấy từ link text
                title = article.css("a::text").get()
            
            # Làm sạch title
            if title:
                title = " ".join(title.split()).strip()
                if len(title) < 3:
                    title = None
            
            # Extract date từ listing page - TechCrunch format
            date = article.css(
                "time::attr(datetime), "
                "time::text, "
                "[class*='timestamp']::text, "
                "[class*='date']::text, "
                "[class*='byline'] time::attr(datetime), "
                "[class*='byline'] time::text"
            ).get()
            if not date:
                date = self._extract_date_from_listing(article, response)
            
            # Làm sạch date
            if date:
                date = date.strip()
            
            # Nếu không có title, thử extract từ URL
            if not title or len(title) < 3:
                url_parts = full_url.split('/')
                if len(url_parts) >= 3:
                    # TechCrunch URL format: https://techcrunch.com/YYYY/MM/DD/article-title/
                    for part in reversed(url_parts):
                        if part and part != 'tag' and part != 'adobe' and len(part) > 3 and not part.isdigit():
                            title = part.replace('-', ' ').title()
                            break
            
            # Chỉ yield item nếu có title và link hợp lệ
            if title and full_url:
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
        
        # Strategy 2: Tìm tất cả các links từ TechCrunch về Adobe articles
        # TechCrunch có thể có nhiều links trong page
        all_links = response.css("a[href]")
        
        # Debug: log số lượng links tìm được
        total_links = len(all_links)
        self.logger.debug(f"Tổng số links tìm được: {total_links}")
        
        potential_article_links = 0
        
        for link in all_links:
            href = link.css("::attr(href)").get()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Chỉ lấy các link từ TechCrunch
            full_url = response.urljoin(href)
            if 'techcrunch.com' not in full_url:
                continue
            
            # Bỏ qua các link không phải bài viết
            if any(skip in full_url for skip in [
                '/tag/', '/author/', '/category/', '/about/', '/contact/', 
                '/events/', '/podcasts/', '/newsletters/', '/staff/', '/videos/'
            ]):
                continue
            
            # Bỏ qua các link đến file assets
            if any(ext in full_url for ext in ['.css', '.js', '.json', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.pdf', '.webp']):
                continue
            
            # Bỏ qua các link đến trang listing hoặc trang chủ
            if full_url in ['https://techcrunch.com/tag/adobe/', 'https://techcrunch.com/tag/adobe', 'https://techcrunch.com/', 'https://techcrunch.com']:
                continue
            
            # Chỉ lấy các link có pattern TechCrunch article: /YYYY/MM/DD/article-title/
            if not re.search(r'/20\d{2}/\d{2}/\d{2}/', full_url):
                continue
            
            if full_url in seen_links:
                continue
            
            potential_article_links += 1
            seen_links.add(full_url)
            
            # Extract title từ link hoặc parent elements
            title = link.css("::text").get()
            if not title or len(title.strip()) < 3:
                # Tìm từ parent container
                parent = link.xpath("ancestor::*[position() <= 5]")
                if parent:
                    title = parent.css("h2::text, h3::text, h4::text, h5::text, h6::text").get()
                    if not title:
                        title = parent.css("[class*='title']::text, [class*='headline']::text").get()
            
            # Làm sạch title
            if title:
                title = " ".join(title.split()).strip()
            
            # Nếu không có title, extract từ URL slug
            if not title or len(title.strip()) < 3:
                url_parts = full_url.split('/')
                if len(url_parts) >= 3:
                    # TechCrunch URL: https://techcrunch.com/YYYY/MM/DD/article-title/
                    for part in reversed(url_parts):
                        if part and part != 'tag' and part != 'adobe' and len(part) > 3 and not part.isdigit():
                            title = part.replace('-', ' ').title()
                            break
            
            # Extract date từ listing page
            date = self._extract_date_from_listing(link, response)
            
            # Yield item nếu có title hợp lệ
            if title and len(title) > 0:
                item = MycrawlerItem()
                item["title"] = title
                item["link"] = full_url
                item["date"] = date
                item["description"] = None
                item["content"] = None
                item["content_length"] = 0
                item["authors"] = None
                item["tags"] = None
                item["images"] = None
                
                yield item
                count += 1
        
        # Debug log
        self.logger.debug(f"Tìm thấy {potential_article_links} links có pattern TechCrunch article")
        
        # Log kết quả
        if count == 0:
            self.logger.warning("⚠️ Không tìm thấy dữ liệu. HTML length: %d", len(response.text))
            self.logger.debug("Response URL: %s", response.url)
        else:
            self.logger.info("✅ Found %d articles from listing page", count)
    
    def _extract_date_from_listing(self, element, response):
        """Extract date từ listing page, tìm time element hoặc date text gần với element"""
        date = None
        
        # Strategy 1: Tìm time element trong cùng parent container với element
        parent = element.xpath("..")
        if parent:
            # Tìm time element trong parent
            time_elements = parent.xpath(".//time")
            if time_elements:
                # Lấy time element đầu tiên
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
            preceding = element.xpath("preceding-sibling::time")
            if preceding:
                date_text = preceding.xpath("@datetime").get()
                if date_text:
                    date = date_text.strip()
                else:
                    date_text = preceding.xpath("normalize-space(.)").get()
                    if date_text:
                        date = date_text.strip()
        
        # Strategy 3: Tìm time element trong ancestor container
        if not date:
            ancestors = element.xpath("ancestor::*[position() <= 5]")
            for ancestor in ancestors:
                time_elem = ancestor.xpath(".//time[1]")
                if time_elem:
                    date_text = time_elem.xpath("@datetime").get()
                    if date_text:
                        date = date_text.strip()
                        break
        
        # Strategy 4: Tìm trong các class có chứa date/publish/time
        if not date:
            date_selectors = [
                "span[class*='date']::text",
                "div[class*='date']::text",
                "time[class*='date']::text",
                "span[class*='time']::text",
                "div[class*='time']::text",
                "span[class*='publish']::text",
                "div[class*='publish']::text",
            ]
            
            for selector in date_selectors:
                date_elem = element.xpath("ancestor::*[position() <= 3]").css(selector).get()
                if date_elem:
                    date = date_elem.strip()
                    # Validate date format (có thể là "October 28, 2025" hoặc ISO format)
                    if date and len(date) > 5:
                        break
        
        # Strategy 5: Tìm text có pattern date (Month DD, YYYY hoặc YYYY-MM-DD)
        if not date:
            ancestor_text = element.xpath("ancestor::*[position() <= 3]//text()").getall()
            for text in ancestor_text:
                text = text.strip()
                # Tìm pattern date: "October 28, 2025" hoặc "2025-10-28"
                date_match = re.search(r'(\w+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})', text)
                if date_match:
                    date = date_match.group(1).strip()
                    break
        
        return date

