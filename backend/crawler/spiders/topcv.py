import scrapy


class TopCVSpider(scrapy.Spider):
    name = "topcv"
    allowed_domains = ["topcv.vn"]
    start_urls = ["https://www.topcv.vn/tim-viec-lam-moi-nhat"]

    custom_settings = {"ROBOTSTXT_OBEY": True}

    def parse(self, response: scrapy.http.Response):
        # Skeleton only: selectors need to be adjusted by real page structure.
        for card in response.css("div.job-item"):
            yield {
                "source": "topcv",
                "source_id": card.css("::attr(data-job-id)").get(),
                "title": card.css("h3.title a::text").get(),
                "company": card.css(".company-name a::text").get(),
                "location": ", ".join(card.css(".city-text::text").getall()).strip(),
                "salary_text": card.css(".salary::text").get(),
                "apply_url": response.urljoin(card.css("h3.title a::attr(href)").get() or ""),
            }
