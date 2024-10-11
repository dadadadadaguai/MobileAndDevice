import json
import logging
import urllib.parse
import csv
import queue
from io import StringIO
import aiofiles
import chardet
import pandas as pd
import requests
from bs4 import BeautifulSoup
import asyncio


# url='https://phonedb.net/index.php?m=device&s=list&filter=29'
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

# 创建一个 logger 实例
logger = logging.getLogger(__name__)

# 添加控制台输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


def search_url(url):
    soup_all = []
    for u in url:
        response = requests.get(u)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            soup_all.append(soup)
    return soup_all


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def insert_csv(value, results, file_path='device.csv'):
    # 检测文件编码
    encoding = detect_encoding(file_path)

    # 读取 CSV 文件
    with open(file_path, mode='r', newline='', encoding=encoding) as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    # 更新符合条件的行
    for row in rows:
        if row['tt.term_mdl_code'] == value:
            row['name'] = results

    # 将更新后的数据写回 CSV 文件
    with open(file_path, mode='w', newline='', encoding=encoding) as csvfile:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
# 解析搜索结果
def parse_search_results(soup):
    # 示搜索结果在 <div class="search-result"> <a title=***>中
    search_results = []
    for result_div in soup.find_all('div', class_='content_block_title'):
        title = result_div.find('a').text.strip()
        search_results.append(title)
    return search_results

# 读取页码
def get_page_url(soup):
    base_url = 'https://phonedb.net/'
    # 筛选出 title 属性包含 "Jump to page" 的 a 标签
    jump_to_page_links = soup.find_all('a', {'title': lambda x: 'Jump to page' in x if x else False})

    full_page_hrefs = [urllib.parse.urljoin(base_url, link.get('href')) for link in jump_to_page_links]

    return full_page_hrefs

#获取name值
async def search_and_scrape(value) -> list:
    base_url = "https://phonedb.net/index.php?m=device&s=list"
    # 构造请求参数
    payload = {
        'search_exp': value,
        'search_header': '',
        'filter': ''
    }
    # 发送POST请求
    response = requests.post(base_url, data=payload)
    results = []
    if response.status_code == 200:
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        # 获取分页数据URL
        full_page_hrefs = get_page_url(soup)
        logger.info("Full page hrefs: %s", full_page_hrefs)
        # 解析分页数据
        soup_all = search_url(full_page_hrefs)
        # 爬取搜索结果
        for soup in soup_all:
            result = parse_search_results(soup)
            results.extend(result)
        logger.info("Results for: %s", results)
    else:
        logger.info("Failed to retrieve results for %s", value)
    return results

#异步读取csv文件
async def read_csv(file_path):
    async with aiofiles.open(file_path, mode='r') as f:
        content = await f.read()
        df = pd.read_csv(StringIO(content))
    return df
#name列表
async def process_date():
    file_path = 'device.csv'
    # 异步读取 CSV 文件
    df = await read_csv(file_path)
    term_mdl_codes = df['tt.term_mdl_code'].tolist()
    # 并发执行 search_and_scrape
    tasks = [search_and_scrape(term_mdl_code) for term_mdl_code in term_mdl_codes]
    # 执行任务
    results = await asyncio.gather(*tasks)
    results_json = json.dumps(results, ensure_ascii=False)
    df['name'] = results
    await write_csv(results, df, output_file_path='device_output.csv')
#写入结果
async def write_csv(results, df, output_file_path):
    df['name'] = results
    df['name'] = df['name'].apply(lambda x: x if x is not None else '')
    # 输出到 CSV 文件
    df.to_csv(output_file_path, index=False, encoding='GBk')
    logger.info(f"Results written to {output_file_path}")

async def main():
    # 并发执行 process_data
    await process_date()
if __name__ == '__main__':
    # search_values = ['SM-N9760', 'PHA120', 'OPPO A207']
    asyncio.run(main())