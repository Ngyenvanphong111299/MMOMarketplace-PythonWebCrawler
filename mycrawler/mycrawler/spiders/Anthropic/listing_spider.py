import scrapy
from scrapy_playwright.page import PageMethod
from ...items import MycrawlerItem
import re


class AnthropicNewsListingSpider(scrapy.Spider):
    name = "anthropic-listing"
    start_urls = ["https://www.anthropic.com/news"]
    
    # Custom settings cho output file routes theo source
    custom_settings = {
        'FEEDS': {
            'data/Anthropic/anthropic-listing.json': {
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
            url = "https://www.anthropic.com/news"
        
        yield scrapy.Request(
            url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle", timeout=60000),
                    PageMethod("wait_for_timeout", 5000),  # Đợi thêm 5 giây để JS load xong
                    # Scroll nhiều lần để load thêm content (infinite scroll)
                    PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight / 3)"),
                    PageMethod("wait_for_timeout", 2000),
                    PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight * 2 / 3)"),
                    PageMethod("wait_for_timeout", 2000),
                    PageMethod("evaluate", "window.scrollTo(0, document.body.scrollHeight)"),
                    PageMethod("wait_for_timeout", 3000),  # Đợi sau khi scroll
                    # Scroll lại lên đầu để đảm bảo tất cả content đã load
                    PageMethod("evaluate", "window.scrollTo(0, 0)"),
                    PageMethod("wait_for_timeout", 2000),
                ],
            },
            callback=self.parse
        )

    def parse(self, response):
        # Trang Anthropic news sử dụng cấu trúc HTML với các bài viết
        # Extract title, link và date trực tiếp từ listing page
        
        count = 0
        seen_links = set()
        
        # Tìm tất cả các links đến các bài viết
        # Anthropic news có thể sử dụng các selector như:
        # - article elements
        # - links có format /news/...
        # - links trong main content area
        
        # Strategy 1: Tìm các article elements
        articles = response.css("article")
        
        for article in articles:
            # Tìm link trong article
            link = article.css("a::attr(href)").get()
            
            if not link or link.startswith('#'):
                continue
            
            # Làm sạch URL
            full_url = response.urljoin(link)
            if full_url in seen_links:
                continue
            
            # Chỉ lấy các URL có format /news/... (bài viết)
            if '/news/' not in full_url:
                continue
            
            # Bỏ qua các link không phải bài viết cụ thể
            if full_url in ['https://www.anthropic.com/news', 'https://www.anthropic.com/news/']:
                continue
            
            # Bỏ qua các link category hoặc filter
            if any(skip in full_url.lower() for skip in ['/category/', '/tag/', '/author/', '/search']):
                continue
            
            seen_links.add(full_url)
            
            # Extract title từ link hoặc article
            title = article.css("h1::text, h2::text, h3::text, h4::text, a::text").get()
            if not title or len(title.strip()) < 3:
                # Thử lấy từ các thẻ con
                title = article.css("h1::text, h2::text, h3::text, h4::text, h5::text, h6::text, span::text, div::text").get()
            
            # Làm sạch title
            if title:
                title = " ".join(title.split()).strip()
                if len(title) < 3:
                    title = None
            
            # Extract date từ listing page
            date = self._extract_date_from_listing(article, response)
            
            # Không bắt buộc phải có date - có thể extract sau từ detail page
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
        
        # Strategy 2: Luôn tìm trực tiếp tất cả các links có pattern /news/
        # Để đảm bảo không bỏ sót bất kỳ article nào
        all_links = response.css("a[href]")
        
        # Debug: log số lượng links tìm được
        total_links = len(all_links)
        self.logger.debug(f"Tổng số links tìm được: {total_links}")
        
        potential_news_links = 0
        
        for link in all_links:
            href = link.css("::attr(href)").get()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Chỉ lấy các link có format /news/... (bài viết)
            full_url = response.urljoin(href)
            if '/news/' not in full_url:
                continue
            
            # Bỏ qua các link không phải bài viết cụ thể
            if full_url in ['https://www.anthropic.com/news', 'https://www.anthropic.com/news/']:
                continue
            
            # Bỏ qua các link category, tag, author, search
            if any(skip in full_url.lower() for skip in ['/category/', '/tag/', '/author/', '/search']):
                continue
            
            # Bỏ qua các link đến file assets
            if any(ext in full_url for ext in ['.css', '.js', '.json', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.pdf']):
                continue
            
            if full_url in seen_links:
                continue
            
            potential_news_links += 1
            seen_links.add(full_url)
            
            # Extract title từ link hoặc parent elements
            title = link.css("::text").get()
            if not title or len(title.strip()) < 3:
                # Thử lấy từ các thẻ con hoặc parent
                title = link.css("h1::text, h2::text, h3::text, h4::text, h5::text, h6::text, span::text, div::text").get()
                if not title:
                    # Thử lấy từ parent container
                    parent = link.xpath("ancestor::*[position() <= 3]")
                    if parent:
                        title = parent.css("h1::text, h2::text, h3::text, h4::text, h5::text, h6::text").get()
            
            # Làm sạch title
            if title:
                title = " ".join(title.split()).strip()
                # Bỏ qua các title là category hoặc navigation text
                category_keywords = ['read more', 'read', 'more', 'view all', 'view', 'all', 'learn more', 'learn', 
                                    'newsroom', 'announcements', 'policy', 'product', 'research', 'safety']
                if len(title) < 3 or title.lower() in category_keywords:
                    # Nếu title không tốt, thử extract từ URL
                    url_parts = full_url.split('/')
                    if len(url_parts) > 0:
                        slug = url_parts[-1]
                        if slug and slug != 'news' and len(slug) > 3:
                            # Convert slug to title (replace hyphens with spaces, capitalize)
                            title = slug.replace('-', ' ').title()
                        else:
                            # Nếu không có slug, vẫn yield với title từ URL
                            title = full_url.split('/')[-1] if full_url.split('/')[-1] else full_url
                    else:
                        title = full_url
                # Nếu title vẫn là category, thử extract từ URL slug
                elif title.lower() in category_keywords:
                    url_parts = full_url.split('/')
                    if len(url_parts) > 0:
                        slug = url_parts[-1]
                        if slug and slug != 'news' and len(slug) > 3:
                            title = slug.replace('-', ' ').title()
            
            # Extract date từ listing page (không bắt buộc)
            date = self._extract_date_from_listing(link, response)
            
            # Yield item nếu có title hợp lệ (hoặc ít nhất có link)
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
        self.logger.debug(f"Tìm thấy {potential_news_links} links có pattern /news/")
        
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
            ancestors = element.xpath("ancestor::*[position() <= 5]")  # Chỉ tìm 5 levels up
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

