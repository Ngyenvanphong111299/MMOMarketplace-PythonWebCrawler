import scrapy
from scrapy_playwright.page import PageMethod
from ...items import MycrawlerItem
import re
from lxml import html


class TechCrunchDetailSpider(scrapy.Spider):
    name = "techcrunch-detail"
    start_urls = []
    
    # Custom settings cho output file routes theo source
    custom_settings = {
        'FEEDS': {
            'data/TechCrunch/techcrunch-detail.json': {
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
            self.logger.error("⚠️ Không có URL được cung cấp. Sử dụng: scrapy crawl techcrunch-detail -a start_url=<URL>")
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
        """Parse detail page của TechCrunch article"""
        
        item = MycrawlerItem()
        
        # Extract title
        title = self._extract_title(response)
        item["title"] = title
        
        # Extract link
        item["link"] = response.url
        
        # Extract description
        description = self._extract_description(response)
        item["description"] = description
        
        # Extract content với đánh dấu vị trí ảnh
        content_result = self._extract_content(response)
        if content_result:
            content, images = content_result
            item["content"] = content
            item["content_length"] = len(content) if content else 0
            item["images"] = images
        else:
            item["content"] = None
            item["content_length"] = 0
            item["images"] = None
        
        # Extract authors
        authors = self._extract_authors(response)
        item["authors"] = authors
        
        # Extract date
        date = self._extract_date(response)
        item["date"] = date
        
        # Extract tags
        tags = self._extract_tags(response)
        item["tags"] = tags
        
        if title:
            self.logger.info("✅ Crawled detail page: %s", title)
            yield item
        else:
            self.logger.warning("⚠️ Không tìm thấy title. URL: %s", response.url)
    
    def _extract_title(self, response):
        """Extract title từ detail page"""
        # Thử các selector khác nhau cho title
        title = None
        
        # Strategy 1: Tìm h1 chính (TechCrunch thường dùng h1 cho title)
        title = response.css("h1::text, h1.article__title::text, h1.entry-title::text").get()
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
            # Loại bỏ " | TechCrunch" nếu có
            title = re.sub(r'\s*\|\s*TechCrunch.*$', '', title, flags=re.IGNORECASE)
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
        description = response.css("p.lead::text, p.summary::text, div.summary p::text, .article__excerpt::text").get()
        if description:
            description = " ".join(description.split()).strip()
            if len(description) > 0:
                return description
        
        return None
    
    def _extract_featured_image(self, response):
        """Extract featured image (header image) từ TechCrunch article
        
        Returns:
            str: URL của featured image hoặc None
        """
        # Strategy 1: Tìm từ meta og:image (Open Graph)
        featured_img = response.css("meta[property='og:image']::attr(content)").get()
        if featured_img:
            featured_img = featured_img.strip()
            if featured_img and not featured_img.startswith('data:'):
                self.logger.debug(f"Tìm thấy featured image từ og:image: {featured_img}")
                return response.urljoin(featured_img)
        
        # Strategy 2: Tìm từ meta twitter:image
        featured_img = response.css("meta[name='twitter:image']::attr(content), meta[property='twitter:image']::attr(content)").get()
        if featured_img:
            featured_img = featured_img.strip()
            if featured_img and not featured_img.startswith('data:'):
                self.logger.debug(f"Tìm thấy featured image từ twitter:image: {featured_img}")
                return response.urljoin(featured_img)
        
        # Strategy 3: Tìm từ article header/figure (featured image container)
        featured_selectors = [
            "article figure img",
            "article header img",
            "article .featured-image img",
            "article .article-featured-image img",
            "article .post-thumbnail img",
            "article .entry-thumbnail img",
        ]
        
        for selector in featured_selectors:
            img_url = response.css(f"{selector}::attr(src), {selector}::attr(data-src), {selector}::attr(data-lazy-src)").get()
            if img_url:
                img_url = img_url.strip()
                if img_url and not img_url.startswith('data:') and 'placeholder' not in img_url.lower():
                    self.logger.debug(f"Tìm thấy featured image từ selector {selector}: {img_url}")
                    return response.urljoin(img_url)
        
        # Strategy 4: Tìm ảnh đầu tiên trong article (trước content)
        article_first_img = response.css("article img::attr(src), article img::attr(data-src)").get()
        if article_first_img:
            article_first_img = article_first_img.strip()
            if article_first_img and not article_first_img.startswith('data:') and 'placeholder' not in article_first_img.lower():
                self.logger.debug(f"Tìm thấy featured image (ảnh đầu tiên trong article): {article_first_img}")
                return response.urljoin(article_first_img)
        
        self.logger.debug("Không tìm thấy featured image")
        return None
    
    def _extract_content(self, response):
        """Extract nội dung chính từ detail page với đánh dấu vị trí ảnh
        
        Returns:
            tuple: (content_with_placeholders, images_in_order) hoặc None
        """
        # Tìm featured image trước
        featured_image_url = self._extract_featured_image(response)
        
        # Tìm main content container
        content_container = None
        content_selectors = [
            "article div[class*='article-content']",
            "article div[class*='entry-content']",
            "article div[class*='post-content']",
            "main article",
            "article",
            "main div[class*='content']",
            "div[class*='article-content']",
        ]
        
        for selector in content_selectors:
            container = response.css(selector).get()
            if container:
                # Kiểm tra xem container có đủ nội dung không
                container_text = response.css(selector + " ::text").getall()
                if container_text and len([t.strip() for t in container_text if t.strip() and len(t.strip()) > 5]) > 3:
                    content_container = container
                    self.logger.debug(f"Tìm thấy content container với selector: {selector}")
                    break
        
        if not content_container:
            self.logger.warning("Không tìm thấy content container")
            return None
        
        # Parse HTML của content container
        try:
            tree = html.fromstring(content_container)
        except Exception as e:
            self.logger.warning(f"Không thể parse HTML content container: {e}")
            return None
        
        # Duyệt qua các phần tử theo thứ tự và extract content với đánh dấu ảnh
        content_parts = []
        images = []
        image_counter = 1  # Bắt đầu từ 1 vì IMAGE_0 dành cho featured image
        seen_image_urls = set()
        
        # Thêm featured image vào đầu content nếu có
        if featured_image_url:
            images.insert(0, featured_image_url)  # Thêm vào đầu danh sách
            seen_image_urls.add(featured_image_url)
            content_parts.append("{{IMAGE_0}}")
            self.logger.info(f"Đã thêm featured image: {featured_image_url}")
        
        def process_element(element):
            """Recursive function để process element và children theo thứ tự"""
            nonlocal image_counter
            
            # Bỏ qua comment nodes
            if element.tag is html.HtmlComment:
                return
            
            # Xử lý text trước element (text node đầu tiên)
            if element.text:
                text = element.text.strip()
                if text and len(text) > 0:
                    content_parts.append(text)
            
            # Xử lý children theo thứ tự
            for child in element:
                if child.tag == 'img':
                    # Xử lý ảnh: thay thế bằng placeholder
                    # Thử nhiều attribute để tìm URL ảnh
                    img_url = (child.get('src') or 
                              child.get('data-src') or 
                              child.get('data-lazy-src') or
                              child.get('data-original'))
                    
                    # Nếu không có, thử data-srcset
                    if not img_url:
                        srcset = child.get('data-srcset')
                        if srcset:
                            # Parse srcset format: "url1 1x, url2 2x" -> lấy url1
                            img_url = srcset.split(',')[0].strip().split()[0] if srcset else None
                    
                    if img_url:
                        # Bỏ qua data URIs và placeholder images
                        if img_url.startswith('data:') or 'placeholder' in img_url.lower() or '1x1' in img_url:
                            continue
                            
                        full_url = response.urljoin(img_url)
                        # Chỉ thêm nếu chưa thấy (tránh trùng lặp, bao gồm cả featured image)
                        if full_url not in seen_image_urls:
                            seen_image_urls.add(full_url)
                            images.append(full_url)
                            content_parts.append(f"{{{{IMAGE_{image_counter}}}}}")
                            self.logger.debug(f"Tìm thấy ảnh {image_counter}: {full_url}")
                            image_counter += 1
                        # else: Ảnh đã tồn tại (có thể là featured image), bỏ qua
                else:
                    # Xử lý các element khác (recursive)
                    process_element(child)
                
                # Xử lý tail text sau element (text node sau element)
                if child.tail:
                    tail_text = child.tail.strip()
                    if tail_text and len(tail_text) > 0:
                        content_parts.append(tail_text)
        
        # Process root element
        process_element(tree)
        
        # Nếu không tìm thấy ảnh trong content container, thử tìm trong toàn bộ article
        if not images:
            # Tìm tất cả ảnh trong article (bao gồm featured image)
            article_imgs = response.css("article img").getall()
            if article_imgs:
                self.logger.debug(f"Tìm thấy {len(article_imgs)} ảnh trong article, đang parse...")
                for img_html in article_imgs:
                    try:
                        img_tree = html.fromstring(img_html)
                        if img_tree.tag == 'img':
                            img_url = (img_tree.get('src') or 
                                      img_tree.get('data-src') or 
                                      img_tree.get('data-lazy-src') or
                                      img_tree.get('data-original'))
                            if not img_url:
                                srcset = img_tree.get('data-srcset')
                                if srcset:
                                    img_url = srcset.split(',')[0].strip().split()[0] if srcset else None
                            
                            if img_url and not img_url.startswith('data:') and 'placeholder' not in img_url.lower() and '1x1' not in img_url:
                                full_url = response.urljoin(img_url)
                                # Bỏ qua nếu là featured image (đã được thêm ở đầu)
                                if featured_image_url and full_url == featured_image_url:
                                    continue
                                if full_url not in seen_image_urls:
                                    seen_image_urls.add(full_url)
                                    images.append(full_url)
                                    self.logger.debug(f"Tìm thấy ảnh từ article: {full_url}")
                    except Exception as e:
                        self.logger.debug(f"Lỗi khi parse img HTML: {e}")
        
        # Log số lượng ảnh tìm được
        if images:
            self.logger.info(f"Tìm thấy {len(images)} ảnh trong content")
        else:
            self.logger.warning("Không tìm thấy ảnh nào trong content container")
        
        # Nếu không có content, return None
        if not content_parts:
            return None
        
        # Kết hợp content parts
        content_text = "\n\n".join(content_parts)
        
        # Làm sạch content: loại bỏ các dòng trống liên tiếp
        if content_text:
            # Loại bỏ các khoảng trắng thừa trong mỗi dòng
            lines = content_text.split('\n')
            cleaned_lines = []
            prev_empty = False
            for line in lines:
                cleaned_line = re.sub(r'\s+', ' ', line.strip()) if line.strip() else ''
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
                    prev_empty = False
                elif not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            
            content_text = '\n\n'.join(cleaned_lines)
            
            # Loại bỏ các dòng trống thừa (3+ dòng trống liên tiếp)
            content_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', content_text)
        
        if not content_text or len(content_text) < 50:
            return None
        
        # Trả về tuple (content, images)
        return (content_text, images if images else None)
    
    def _extract_authors(self, response):
        """Extract danh sách tác giả"""
        authors = []
        
        # Strategy 1: Tìm authors từ các selector phổ biến của TechCrunch
        author_selectors = [
            "a[class*='author']::text",
            "span[class*='author']::text",
            "div[class*='author']::text",
            ".article__byline a::text",
            ".byline a::text",
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
        
        # Strategy 3: Tìm link có /author/ trong URL
        if not authors:
            author_links = response.css("a[href*='/author/']::text").getall()
            if author_links:
                authors = [a.strip() for a in author_links if a.strip()]
        
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
        
        # Strategy 4: Tìm meta datePublished trong structured data
        date = response.css("meta[itemprop='datePublished']::attr(content)").get()
        if date:
            date = date.strip()
            if len(date) > 0:
                return date
        
        # Strategy 5: Tìm trong các class có chứa date/publish
        date_selectors = [
            "span[class*='date']::text",
            "div[class*='date']::text",
            "time[class*='date']::text",
            ".article__date::text",
            ".published-date::text",
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
        
        # Strategy 1: Tìm tags từ các selector phổ biến của TechCrunch
        tag_selectors = [
            "a[class*='tag']::text",
            "span[class*='tag']::text",
            "div[class*='tag']::text",
            ".article__tags a::text",
            ".tags a::text",
            "meta[property='article:tag']::attr(content)",
        ]
        
        for selector in tag_selectors:
            tag_elements = response.css(selector).getall()
            if tag_elements:
                tags = [t.strip() for t in tag_elements if t.strip()]
                break
        
        # Strategy 2: Tìm categories
        if not tags:
            category_elements = response.css("a[class*='category']::text, span[class*='category']::text, .article__categories a::text").getall()
            if category_elements:
                tags = [c.strip() for c in category_elements if c.strip()]
        
        # Strategy 3: Tìm links có /tag/ hoặc /category/ trong URL
        if not tags:
            tag_links = response.css("a[href*='/tag/']::text, a[href*='/category/']::text").getall()
            if tag_links:
                tags = [t.strip() for t in tag_links if t.strip()]
        
        return tags if tags else None
    

