crawler = AsyncWebCrawler(config=browser_config)
await crawler.start()

try:
      # Set up scraping parameters
      crawl_config = CrawlerRunConfig(
          table_score_threshold=8,  # Strict table detection
      )

      # Execute market data extraction
      results: List[CrawlResult] = await crawler.arun(
          url="https://coinmarketcap.com/?page=1", config=crawl_config
      )

      # Process results
      raw_df = pd.DataFrame()
      for result in results:
          if result.success and result.media["tables"]:
              raw_df = pd.DataFrame(
                  result.media["tables"][0]["rows"],
                  columns=result.media["tables"][0]["headers"],
              )
              break
      print(raw_df.head())

  finally:
      await crawler.stop()