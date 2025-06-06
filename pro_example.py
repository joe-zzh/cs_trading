import asyncio
import pandas as pd
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    # 可选：自定义浏览器配置
    browser_config = BrowserConfig(
        headless=True,  # 无头模式
        verbose=True    # 输出详细日志
    )

    # 可选：自定义爬取参数
    crawl_config = CrawlerRunConfig(
        table_score_threshold=8,  # 严格表格检测
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 执行爬取
        results = await crawler.arun(
            url="https://coinmarketcap.com/?page=1",
            config=crawl_config
        )

        # 处理结果，提取表格
        raw_df = pd.DataFrame()
        if results.success and results.media["tables"]:
            raw_df = pd.DataFrame(
                results.media["tables"][0]["rows"],
                columns=results.media["tables"][0]["headers"],
            )
            print(raw_df.head())
        else:
            print("未检测到表格或爬取失败")

if __name__ == "__main__":
    asyncio.run(main())