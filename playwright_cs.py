import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    url = "https://steamdt.com/cs2/AK-47%20%7C%20Hydroponic%20(Factory%20New)"
    target_api = "/user/steam/type-trend/v2/item/details"
    buff_history = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def handle_response(response):
            print("接口：", response.url)
            if target_api in response.url:
                try:
                    data = await response.json()
                    print("捕获到 BUFF 历史数据接口：", response.url)
                    buff_history["data"] = data
                except Exception as e:
                    print("解析失败:", e)

        page.on("response", handle_response)
        await page.goto(url)
        await page.wait_for_timeout(10000)  # 等待接口加载

        # 保存数据
        if "data" in buff_history:
            with open("buff_history.json", "w", encoding="utf-8") as f:
                json.dump(buff_history["data"], f, ensure_ascii=False, indent=2)
            print("BUFF 历史数据已保存到 buff_history.json")
        else:
            print("未捕获到 BUFF 历史数据接口响应")

        await browser.close()

asyncio.run(main())