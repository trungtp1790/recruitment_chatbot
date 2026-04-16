import scrapy


class LinkedInSpider(scrapy.Spider):
    name = "linkedin"
    allowed_domains = ["linkedin.com"]
    start_urls = ["https://www.linkedin.com/jobs/"]

    custom_settings = {"ROBOTSTXT_OBEY": True}

    def parse(self, response: scrapy.http.Response):
        # Skeleton only. Respect terms and legal constraints before real crawling.
        for card in response.css("li.jobs-search-results__list-item"):
            yield {
                "source": "linkedin",
                "source_id": card.css("::attr(data-entity-urn)").get(),
                "title": card.css("h3::text").get(),
                "company": card.css("h4 a::text").get(),
                "location": card.css("span.job-search-card__location::text").get(),
                "apply_url": response.urljoin(card.css("a::attr(href)").get() or ""),
            }
