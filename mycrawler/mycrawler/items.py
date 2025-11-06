# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MycrawlerItem(scrapy.Item):
    # Basic information
    title = scrapy.Field()
    link = scrapy.Field()
    description = scrapy.Field()
    
    # Content
    content = scrapy.Field()
    content_length = scrapy.Field()
    
    # Metadata
    authors = scrapy.Field()  # List of authors
    date = scrapy.Field()
    tags = scrapy.Field()  # List of tags/categories
    
    # Media
    images = scrapy.Field()  # List of image URLs
