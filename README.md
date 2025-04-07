# 自动化商业数据分析工具（Automated business data Analysis tool 简称AA）

## 项目简介
自动化商业数据分析工具（Automated business data Analysis tool 简称AA）是一款通用的商业数据分析报告生成工具，适合用于对企业总部或者分支机构各项业务指标的变动进行监测分析，工具支持：
- 支持灵活接入业务指标数据，灵活适配手工报表或者标准数据表；
- 支持灵活配置业务分析报告模板，通过多种指标监测算子，对指标变动进行监测；
- 支持分析报告生成；
- 应用扩展：用户可以将生成报告提交给Deepseek，让其对分析报告进行总结提炼，总结亮点不足，形成报告解读。

AA工具具有灵活、自动化的特点，结合AI更可以实现报告的智能解读，将大大提高商业数据分析的效率，具体体现在：
- **数据处理自动化**，提高数据抽取、清洗、整合的效率；
- **指标解读自动化**，提高对指标变动、解读的效率，释放人力；
- **分析结果智能化**，与AI结合后，提高业务分析的质量和效率；

## 工具使用流程
1. 数据预处理
   1. 数据预处理配置
   2. 数据预处理
2. 生成指标监测报告
   1. 指标监测报告模板配置
   2. 指标监测报告生成
3. 指标监测报告解读（可选）
   1. 将指标监测报告提交给AI，通过提示词，让AI解读分析报告，提炼分析结论

## 快速开始
### 安装 (提供windows macOS 两个平台的安装指引 )
```Shell
# 1.从github下载AA
git clone https://github.com/fancyfreeman/AA.git

# 2.安装python，检查python，要求使用 python 3.10+ 以上版本
python -V
Python 3.13.2

# 3.创建python虚拟环境
cd AA                     # 进入工具目录
python -m venv .venv      # 创建虚拟环境 .venv
source .venv/bin/activate # 激活虚拟环境 如需取消激活虚拟环境 执行 deactivate

# 4.安装依赖包
cd AA
pip install -r requirements.txt

# 


```
### 运行（以使用样例数据为例进行说明）
```Shell
cd AA                     # 进入工具目录
python ./src/main.py -T 1
```

## 使用说明
### 目录结构
```
.
├── config/                               # 配置文件
│   └── data_extraction_config.xlsx       # 数据预处理配置文件
│   └── report_config.yaml                # 分析报告模板模板文件
├── data/                                 # 数据文件夹
│   └── raw/                              # 原始数据文件夹
│   └── processed/                        # 预处理数据文件夹
├── reports/                              # 分析报告文件夹
├── src/                                  # 源代码
│   └── aa/                               # 主包
│   └── main.py                           # 主程序入口
├── requirements.txt                      # 依赖清单
└── README.md                             # 项目文档
```
数据命名规范（建议）
config/ 该目录存放数据抽取配置文件和分析报告模板模板文件
data/raw 该目录存放原始excel数据
如 data_extraction_config_X公司样例_零售业.xlsx


### 数据预处理
#### 数据预处理配置
（介绍配置文件内容）


### 生成指标监测报告

### 指标监测报告解读（需要AI支持，如DeepSeek-R1）


## 许可证
MIT License
