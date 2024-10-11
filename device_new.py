# url='https://phonedb.net/index.php?m=device&s=list&filter=29'
import logging
import queue
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import chardet
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

logger = logging.getLogger(__name__)

# 添加控制台输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')
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


def detect_encoding(file_path: str):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']


# def insert_csv(value, results, file_path='device_new.csv'):
#     # 检测文件编码
#     encoding = detect_encoding(file_path)
#
#     # 读取 CSV 文件
#     with open(file_path, mode='r', newline='', encoding=encoding) as csvfile:
#         reader = csv.DictReader(csvfile)
#         rows = list(reader)
#
#     # 更新符合条件的行
#     for row in rows:
#         if row['tt.term_mdl_code'] == value:
#             row['name'] = results
#
#     # 将更新后的数据写回 CSV 文件
#     with open(file_path, mode='w', newline='', encoding=encoding) as csvfile:
#         fieldnames = rows[0].keys()
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(rows)


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
    jump_to_page_links = soup.find_all(
        'a', {'title': lambda x: 'Jump to page' in x if x else False})

    full_page_hrefs = [
        urllib.parse.urljoin(
            base_url,
            link.get('href')) for link in jump_to_page_links]

    return full_page_hrefs


# 获取name值
def search_and_scrape(value) -> list:
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


# def worker(task_queue, loop, executor, results):
#    while True:
#        term_mdl_code = await task_queue.get()
#        result = await loop.run_in_executor(executor, search_and_scrape, term_mdl_code)
#        results.extend(result)
#        task_queue.task_done()
# 异步读取csv文件
def read_csv(file_path):
    df = pd.read_csv(file_path, encoding='GBK')
    return df


# name列表
def worker(task_queue, results_dict):
    while True:
        term_mdl_code = task_queue.get()
        if term_mdl_code is None:
            break
        result = search_and_scrape(term_mdl_code)
        results_dict[term_mdl_code] = result
        task_queue.task_done()


def process_data(file_path, output_file_path):
    # 读取 CSV 文件
    df = read_csv(file_path)
    term_mdl_codes = df['tt.term_mdl_code'].tolist()
    task_queue = queue.Queue()
    for term_mdl_code in term_mdl_codes:
        task_queue.put(term_mdl_code)
    # 创建结果字典
    results_dict = {}
    # 创建线程池
    num_workers = 10
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # 创建工作者任务
        workers = [
            executor.submit(
                worker,
                task_queue,
                results_dict) for _ in range(num_workers)]
        # 显示进度条
        with tqdm(total=len(term_mdl_codes), desc="Processing") as pbar:
            # 等待所有任务完成
            task_queue.join()
            for _ in range(num_workers):
                task_queue.put(None)
            # 等待所有工作者任务完成
            for worker_task in workers:
                worker_task.result()
            # 将字典转换为 DataFrame 列
    df['name'] = df['tt.term_mdl_code'].map(results_dict).fillna('')
    write_csv(df, output_file_path)


# 写入结果
def write_csv(df, output_file_path):
    df.to_csv(output_file_path, index=False, encoding='gbk')
    logger.info(f"Results written to {output_file_path}")


#
# async def main():
#     # 并发执行 process_data
#     try:
#         await process_date()
#     except Exception as e:
#         logger.error(f"An error occurred: {e}", exc_info=True)
if __name__ == '__main__':
    # search_values = ['SM-N9760', 'PHA120', 'OPPO A207']
    file_path = 'device_test.csv'
    output_file_path = 'device_test_output.csv'
    process_data(file_path, output_file_path)
