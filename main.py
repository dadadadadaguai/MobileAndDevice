import json
import os

import pandas as pd
import requests

file_path = 'city.csv'
# 获取csv文件
df = pd.read_csv(file_path)
def getCityId():
    cityId_rows=df[df['TYPE']=='CITY']
    state_abbrev=df[df['TYPE']=='STATE_ABBREV']
    state_abbrev_ids=state_abbrev['CODE']
    city_ids=cityId_rows['CODE']
    # print(city_ids)
    # number =city_ids.count()
    # print(number)
    return  city_ids,state_abbrev_ids

def downJson(file_path,city_ids):
    #city前缀地址
    Url_head='https://geo.datav.aliyun.com/areas_v3/bound/geojson?code='
    for city_id in city_ids:
        #将city_id和_full拼接
        city_id_url=Url_head+f"{city_id}_full"
        # print(city_id_url)
        response=requests.get(city_id_url)
        if response.status_code == 200:
            data = response.json()
            filename = os.path.join(file_path, f'{city_id}.json')
            print(filename)
            with open(filename, 'w',encoding='utf-8') as file:
                json.dump(data, file,ensure_ascii=False, indent=4)
        else:
            errors_row=df[df['CODE']==city_id]
            error_name=errors_row['VAL']
            print(f"Failed to retrieve data for {city_id},{error_name}")


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    city_ids,state_abbrev_ids=getCityId()
    number =city_ids.count()
    output_dir=r'D:\work\others\all'
    output_dir_other=r'D:\work\others\all\other'
    other_path=r'D:\work\others\other_city'
    #state_abbrev只有市的
    state_abbrev_ids_city=['110000','120000','150000','310000','450000','500000','540000','640000','650000','810000','820000']
    state_abbrev_ids_ohter=['540600','710000']
    downJson(other_path,state_abbrev_ids_ohter)

