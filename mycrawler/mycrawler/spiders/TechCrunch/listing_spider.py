import scrapy
from scrapy_playwright.page import PageMethod
from ...items import MycrawlerItem
import re


class TechCrunchListingSpider(scrapy.Spider):
    name = "techcrunch-listing"
    start_urls = ["https://techcrunch.com/category/artificial-intelligence/"]
    
    # Custom settings cho output file routes theo source
    custom_settings = {
        'FEEDS': {
            'data/TechCrunch/techcrunch-listing.json': {
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
            url = "https://techcrunch.com/category/artificial-intelligence/"
        
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
        # TechCrunch category page sử dụng cấu trúc HTML với các bài viết
        # Extract title, link và date trực tiếp từ listing page
        
        count = 0
        seen_links = set()
        
        # Tìm tất cả các links đến các bài viết
        # TechCrunch có thể sử dụng các selector như:
        # - article h2 a, article h3 a (cho title links)
        # - a[href*="/YYYY/MM/DD/"] (cho article links)
        # - .post-block__title a (nếu có class này)
        
        # Strategy 1: Tìm các article elements
        articles = response.css("article")
        
        for article in articles:
            # Tìm link trong article
            link = article.css("h2 a::attr(href), h3 a::attr(href), .post-block__title a::attr(href), a::attr(href)").get()
            
            if not link or link.startswith('#'):
                continue
            
            # Làm sạch URL
            full_url = response.urljoin(link)
            if full_url in seen_links:
                continue
            
            # Chỉ lấy các URL có format bài viết (có /YYYY/MM/DD/ trong URL)
            if not re.search(r'/\d{4}/\d{2}/\d{2}/', full_url):
                # Cũng có thể là format khác, nhưng ít nhất phải là link đến bài viết
                if '/category/' in full_url or '/tag/' in full_url or '/author/' in full_url:
                    continue
            
            seen_links.add(full_url)
            
            # Extract title từ link
            title = article.css("h2 a::text, h3 a::text, .post-block__title a::text, h2::text, h3::text").get()
            if not title:
                # Thử lấy từ các thẻ con
                title = article.css("h1::text, h2::text, h3::text, h4::text, h5::text, h6::text, span::text").get()
            
            # Làm sạch title
            if title:
                title = " ".join(title.split()).strip()
                if len(title) < 3:
                    title = None
            
            # Extract date từ listing page
            date = self._extract_date_from_listing(article, response)
            
            # Extract author nếu có trên listing page
            author = self._extract_author_from_listing(article, response)
            authors = [author] if author else None
            
            # Chỉ yield item nếu có title và link hợp lệ
            if title and full_url:
                item = MycrawlerItem()
                item["title"] = title
                item["link"] = full_url
                item["date"] = date
                item["authors"] = authors
                # Set các field không cần thiết về None
                item["description"] = None
                item["content"] = None
                item["content_length"] = 0
                item["tags"] = None
                item["images"] = None
                
                yield item
                count += 1
        
        # Strategy 2: Nếu không tìm được qua articles, thử tìm trực tiếp các links
        if count == 0:
            all_links = response.css("a[href]")
            
            for link in all_links:
                href = link.css("::attr(href)").get()
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue
                
                # Chỉ lấy các link có format bài viết
                full_url = response.urljoin(href)
                if not re.search(r'/\d{4}/\d{2}/\d{2}/', full_url):
                    continue
                
                if full_url in seen_links:
                    continue
                
                # Kiểm tra xem có phải link category, tag, author không
                if '/category/' in full_url or '/tag/' in full_url or '/author/' in full_url:
                    continue
                
                seen_links.add(full_url)
                
                # Extract title từ link
                title = link.css("::text").get()
                if not title or len(title.strip()) < 3:
                    # Thử lấy từ các thẻ con
                    title = link.css("h1::text, h2::text, h3::text, h4::text, h5::text, h6::text, span::text").get()
                
                if title:
                    title = " ".join(title.split()).strip()
                    if len(title) < 3:
                        continue
                
                # Extract date từ listing page
                date = self._extract_date_from_listing(link, response)
                
                # Extract author
                author = self._extract_author_from_listing(link, response)
                authors = [author] if author else None
                
                if title:
                    item = MycrawlerItem()
                    item["title"] = title
                    item["link"] = full_url
                    item["date"] = date
                    item["authors"] = authors
                    item["description"] = None
                    item["content"] = None
                    item["content_length"] = 0
                    item["tags"] = None
                    item["images"] = None
                    
                    yield item
                    count += 1
        
        # Log kết quả
        if count == 0:
            self.logger.warning("⚠️ Không tìm thấy dữ liệu. HTML length: %d", len(response.text))
            self.logger.debug("Response URL: %s", response.url)
        else:
            self.logger.info("✅ Found %d articles from listing page", count)
    
    def _extract_date_from_listing(self, element, response):
        """Extract date từ listing page, tìm time element gần với element"""
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
        
        # Strategy 4: Tìm trong các class có chứa date/publish
        if not date:
            date_selectors = [
                "span[class*='date']::text",
                "div[class*='date']::text",
                "time[class*='date']::text",
                "span[class*='time']::text",
            ]
            
            for selector in date_selectors:
                date_elem = element.xpath("ancestor::*[position() <= 3]").css(selector).get()
                if date_elem:
                    date = date_elem.strip()
                    break
        
        return date
    
    def _extract_author_from_listing(self, element, response):
        """Extract author từ listing page"""
        author = None
        
        # Strategy 1: Tìm author element trong cùng parent container
        parent = element.xpath("..")
        if parent:
            author_elements = parent.xpath(".//*[contains(@class, 'author')]")
            if author_elements:
                author_text = author_elements[0].xpath("normalize-space(.)").get()
                if author_text:
                    author = author_text.strip()
        
        # Strategy 2: Tìm trong ancestor container
        if not author:
            ancestors = element.xpath("ancestor::*[position() <= 5]")
            for ancestor in ancestors:
                author_elem = ancestor.xpath(".//*[contains(@class, 'author')]")
                if author_elem:
                    author_text = author_elem[0].xpath("normalize-space(.)").get()
                    if author_text:
                        author = author_text.strip()
                        break
        
        # Strategy 3: Tìm link có /author/ trong URL
        if not author:
            author_link = element.xpath("ancestor::*[position() <= 5]//a[contains(@href, '/author/')]")
            if author_link:
                author_text = author_link[0].xpath("normalize-space(.)").get()
                if author_text:
                    author = author_text.strip()
        
        return author

