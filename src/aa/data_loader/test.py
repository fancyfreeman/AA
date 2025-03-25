import pandas as pd

# 创建示例 DataFrame
data = {"name": ["AA", "B", "C", "AAA", "BB"], "value": [10, 20, 30, 40, 50]}
df = pd.DataFrame(data)

# 按 name 列排序，先按字符个数，再按字母顺序
df_sorted = df.sort_values(by="name", key=lambda x: (x.str.len(), x))

print("排序前的 DataFrame:")
print(df)
print("\n排序后的 DataFrame:")
print(df_sorted)
