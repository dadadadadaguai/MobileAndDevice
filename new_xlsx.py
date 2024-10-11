import pandas as pd

def merge_and_update():
    # 读取两个 CSV 文件
    df_a = pd.read_csv('final_device_output_new.csv', encoding='gbk')
    df_b = pd.read_csv('device.csv', encoding='gbk')

    # 根据 tt.term_mdl_code 合并 A 和 B 表
    merged_df = pd.merge(df_b, df_a[['tt.term_mdl_code', 'name']], on='tt.term_mdl_code', how='left', suffixes=('_b', '_a'))

    # 更新 B 表中的 name 列
    merged_df['name'] = merged_df.get('name_a', merged_df['name_b'])
    merged_df.drop(columns=['name_b', 'name_a'], inplace=True)
    merged_df.rename(columns={'name': 'name_updated'}, inplace=True)

    # 将更新后的 B 表写入新的 CSV 文件
    merged_df.to_csv('updated_B.csv', index=False, encoding='gbk')

# 调用函数
if __name__ == '__main__':
    merge_and_update()