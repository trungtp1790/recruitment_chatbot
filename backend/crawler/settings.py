BOT_NAME = "recruitment_crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1

FEEDS = {
    "output/%(name)s_%(time)s.json": {
        "format": "json",
        "encoding": "utf-8",
        "indent": 2,
    }
}
