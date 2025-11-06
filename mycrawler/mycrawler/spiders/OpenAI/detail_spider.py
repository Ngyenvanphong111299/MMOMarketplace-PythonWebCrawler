import scrapy
from scrapy_playwright.page import PageMethod
from ...items import MycrawlerItem
import re


class OpenAIComDetailSpider(scrapy.Spider):
    name = "openai-com-detail"
    start_urls = []
    
    # Custom settings cho output file routes theo source
    custom_settings = {
        'FEEDS': {
            'data/OpenAI/openai-com-detail.json': {
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
            self.logger.error("⚠️ Không có URL được cung cấp. Sử dụng: scrapy crawl openai-com-detail -a start_url=<URL>")
            return
        
        yield scrapy.Request(
            url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle", timeout=60000),
                    PageMethod("wait_for_timeout", 5000),  # Đợi thêm 5 giây để JS load xong và content render
                ],
            },
            callback=self.parse
        )

    def parse(self, response):
        """Parse detail page của OpenAI research article"""
        
        item = MycrawlerItem()
        
        # Extract title
        title = self._extract_title(response)
        item["title"] = title
        
        # Extract link
        item["link"] = response.url
        
        # Extract description
        description = self._extract_description(response)
        item["description"] = description
        
        # Extract content
        content = self._extract_content(response)
        item["content"] = content
        item["content_length"] = len(content) if content else 0
        
        # Extract authors
        authors = self._extract_authors(response)
        item["authors"] = authors
        
        # Extract date
        date = self._extract_date(response)
        item["date"] = date
        
        # Extract tags
        tags = self._extract_tags(response)
        item["tags"] = tags
        
        # Extract images
        images = self._extract_images(response)
        item["images"] = images
        
        if title:
            self.logger.info("✅ Crawled detail page: %s", title)
            yield item
        else:
            self.logger.warning("⚠️ Không tìm thấy title. URL: %s", response.url)
    
    def _extract_title(self, response):
        """Extract title từ detail page"""
        # Thử các selector khác nhau cho title
        title = None
        
        # Strategy 1: Tìm h1 chính
        title = response.css("h1::text").get()
        if title:
            title = " ".join(title.split()).strip()
            if len(title) > 0:
                return title
        
        # Strategy 2: Tìm title từ meta tag
        title = response.css("meta[property='og:title']::attr(content)").get()
        if title:
            title = title.strip()
            if len(title) > 0:
                return title
        
        # Strategy 3: Tìm title từ head
        title = response.css("title::text").get()
        if title:
            title = title.strip()
            if len(title) > 0:
                return title
        
        return None
    
    def _extract_description(self, response):
        """Extract description từ detail page"""
        # Strategy 1: Meta description
        description = response.css("meta[name='description']::attr(content)").get()
        if description:
            description = description.strip()
            if len(description) > 0:
                return description
        
        # Strategy 2: Open Graph description
        description = response.css("meta[property='og:description']::attr(content)").get()
        if description:
            description = description.strip()
            if len(description) > 0:
                return description
        
        # Strategy 3: Tìm excerpt hoặc summary từ content
        description = response.css("p.lead::text, p.summary::text, div.summary p::text").get()
        if description:
            description = " ".join(description.split()).strip()
            if len(description) > 0:
                return description
        
        return None
    
    def _extract_content(self, response):
        """Extract nội dung chính từ detail page"""
        # Tìm main content area - sử dụng nhiều strategy để lấy toàn bộ content
        
        content_parts = []
        content_text = None
        
        # Strategy 1: Tìm main content container và lấy tất cả text trong đó
        # Sử dụng XPath để lấy toàn bộ text từ main content area
        main_content_xpaths = [
            "//main//article//text()[normalize-space()]",
            "//article//text()[normalize-space()]",
            "//main//div[contains(@class, 'content')]//text()[normalize-space()]",
            "//main//div[contains(@class, 'article')]//text()[normalize-space()]",
            "//div[contains(@class, 'content')]//text()[normalize-space()]",
        ]
        
        for xpath in main_content_xpaths:
            texts = response.xpath(xpath).getall()
            if texts and len(texts) > 3:  # Có ít nhất 3 text nodes
                # Lọc bỏ các text quá ngắn (có thể là navigation, button text)
                filtered_texts = [t.strip() for t in texts if t.strip() and len(t.strip()) > 5]
                if filtered_texts:
                    content_text = "\n\n".join(filtered_texts)
                    break
        
        # Strategy 2: Nếu không tìm được bằng XPath, thử CSS selector
        if not content_text or len(content_text) < 100:
            # Tìm tất cả paragraphs và headings trong main content
            content_selectors = [
                "main article p::text, main article h1::text, main article h2::text, main article h3::text, main article h4::text, main article h5::text, main article h6::text",
                "article p::text, article h1::text, article h2::text, article h3::text, article h4::text, article h5::text, article h6::text",
                "main p::text, main h1::text, main h2::text, main h3::text, main h4::text, main h5::text, main h6::text",
                "div[class*='content'] p::text, div[class*='content'] h1::text, div[class*='content'] h2::text, div[class*='content'] h3::text",
                "div[class*='article'] p::text, div[class*='article'] h1::text, div[class*='article'] h2::text, div[class*='article'] h3::text",
            ]
            
            for selector in content_selectors:
                elements = response.css(selector).getall()
                if elements:
                    content_parts = [e.strip() for e in elements if e.strip() and len(e.strip()) > 5]
                    if content_parts and len("\n\n".join(content_parts)) > 100:
                        content_text = "\n\n".join(content_parts)
                        break
        
        # Strategy 3: Nếu vẫn chưa có, thử lấy tất cả text từ body (loại bỏ script, style, nav, footer)
        if not content_text or len(content_text) < 100:
            # Lấy text từ body nhưng loại bỏ các phần không phải content
            body_text = response.xpath("//body//text()[normalize-space()]").getall()
            if body_text:
                # Lọc bỏ các text từ script, style, nav, footer, header
                filtered_body = []
                for text in body_text:
                    text = text.strip()
                    if text and len(text) > 10:  # Chỉ lấy text dài hơn 10 ký tự
                        # Loại bỏ các text có vẻ như navigation hoặc metadata
                        if not any(skip in text.lower() for skip in ['skip', 'menu', 'navigation', 'footer', 'cookie', 'privacy', 'terms']):
                            filtered_body.append(text)
                
                if filtered_body:
                    content_text = "\n\n".join(filtered_body)
        
        # Làm sạch content: loại bỏ các dòng trống liên tiếp
        if content_text:
            # Loại bỏ các khoảng trắng thừa trong mỗi dòng (nhưng giữ nguyên cấu trúc paragraphs)
            lines = content_text.split('\n')
            cleaned_lines = []
            prev_empty = False
            for line in lines:
                # Loại bỏ khoảng trắng thừa trong dòng nhưng giữ nguyên nếu là dòng trống
                cleaned_line = re.sub(r'\s+', ' ', line.strip()) if line.strip() else ''
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
                    prev_empty = False
                elif not prev_empty:
                    # Chỉ thêm một dòng trống nếu trước đó không phải dòng trống
                    cleaned_lines.append('')
                    prev_empty = True
            
            content_text = '\n\n'.join(cleaned_lines)
            
            # Loại bỏ các dòng trống thừa (3+ dòng trống liên tiếp)
            content_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', content_text)
        
        return content_text if content_text and len(content_text) > 50 else None
    
    def _extract_authors(self, response):
        """Extract danh sách tác giả"""
        authors = []
        
        # Strategy 1: Tìm authors từ các selector phổ biến
        author_selectors = [
            "span[class*='author']::text",
            "div[class*='author']::text",
            "a[class*='author']::text",
            "meta[name='author']::attr(content)",
        ]
        
        for selector in author_selectors:
            author_elements = response.css(selector).getall()
            if author_elements:
                authors = [a.strip() for a in author_elements if a.strip()]
                break
        
        # Strategy 2: Tìm trong structured data
        if not authors:
            # Tìm JSON-LD hoặc schema.org
            script_tags = response.css("script[type='application/ld+json']::text").getall()
            for script in script_tags:
                # Có thể parse JSON để tìm authors, nhưng để đơn giản sẽ skip
                pass
        
        return authors if authors else None
    
    def _extract_date(self, response):
        """Extract ngày publish"""
        date = None
        
        # Strategy 1: Tìm time element với datetime attribute
        date = response.css("time::attr(datetime)").get()
        if date:
            date = date.strip()
            if len(date) > 0:
                return date
        
        # Strategy 2: Tìm time element text
        date = response.css("time::text").get()
        if date:
            date = date.strip()
            if len(date) > 0:
                return date
        
        # Strategy 3: Tìm meta published time
        date = response.css("meta[property='article:published_time']::attr(content)").get()
        if date:
            date = date.strip()
            if len(date) > 0:
                return date
        
        # Strategy 4: Tìm trong các class có chứa date/publish
        date_selectors = [
            "span[class*='date']::text",
            "div[class*='date']::text",
            "time[class*='date']::text",
        ]
        
        for selector in date_selectors:
            date = response.css(selector).get()
            if date:
                date = date.strip()
                if len(date) > 0:
                    return date
        
        return None
    
    def _extract_tags(self, response):
        """Extract danh sách tags/categories"""
        tags = []
        
        # Strategy 1: Tìm tags từ các selector phổ biến
        tag_selectors = [
            "a[class*='tag']::text",
            "span[class*='tag']::text",
            "div[class*='tag']::text",
            "meta[property='article:tag']::attr(content)",
        ]
        
        for selector in tag_selectors:
            tag_elements = response.css(selector).getall()
            if tag_elements:
                tags = [t.strip() for t in tag_elements if t.strip()]
                break
        
        # Strategy 2: Tìm categories
        if not tags:
            category_elements = response.css("a[class*='category']::text, span[class*='category']::text").getall()
            if category_elements:
                tags = [c.strip() for c in category_elements if c.strip()]
        
        return tags if tags else None
    
    def _extract_images(self, response):
        """Extract danh sách URLs hình ảnh"""
        images = []
        
        # Strategy 1: Tìm images trong main content
        img_selectors = [
            "article img::attr(src)",
            "main img::attr(src)",
            "div[class*='content'] img::attr(src)",
            "div[class*='article'] img::attr(src)",
        ]
        
        for selector in img_selectors:
            img_urls = response.css(selector).getall()
            if img_urls:
                for img_url in img_urls:
                    if img_url:
                        full_url = response.urljoin(img_url)
                        if full_url not in images:
                            images.append(full_url)
                break
        
        # Strategy 2: Tìm Open Graph image
        og_image = response.css("meta[property='og:image']::attr(content)").get()
        if og_image:
            full_url = response.urljoin(og_image)
            if full_url not in images:
                images.insert(0, full_url)  # Thêm vào đầu danh sách
        
        return images if images else None

