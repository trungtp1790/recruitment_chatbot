import scrapy


class ItViecSpider(scrapy.Spider):
    name = "itviec"
    allowed_domains = ["itviec.com"]
    start_urls = ["https://itviec.com/it-jobs"]

    custom_settings = {"ROBOTSTXT_OBEY": True}

    def parse(self, response: scrapy.http.Response):
        # Skeleton only: selectors need to be adjusted by real page structure.
        for card in response.css("div.job"):
            yield {
                "source": "itviec",
                "source_id": card.css("::attr(data-id)").get(),
                "title": card.css("h3::text").get(),
                "company": card.css(".company-name::text").get(),
                "location": ", ".join(card.css(".address::text").getall()).strip(),
                "salary_text": card.css(".salary-text::text").get(),
                "apply_url": response.urljoin(card.css("a::attr(href)").get() or ""),
            }
