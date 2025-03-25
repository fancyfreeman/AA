# Automated Analysis (AA)

## 项目概述
商业银行业务指标自动化分析系统，通过配置文件驱动实现：
- 数据自动加载
- 指标自动化分析
- 分析结果自动生成

## 功能特性
- 📁 配置驱动：通过YAML配置文件定义数据源、分析规则和输出格式
- 🧩 模块化设计：支持扩展多种数据加载器、分析器和报告生成器
- 📊 灵活分析：支持自定义业务指标和计算规则
- 📈 多格式输出：生成HTML、PDF等多种格式分析报告

## 目录结构
```
.
├── config/               # 配置文件
│   └── config.yaml       # 主配置文件
├── data/                 # 数据文件存储
├── docs/                 # 项目文档
├── examples/             # 示例配置和数据
├── src/                  # 源代码
│   └── aa/               # 主包
│       ├── core/         # 核心流程控制
│       ├── data_loader/  # 数据加载模块
│       ├── analyzers/    # 数据分析模块
│       ├── report_generators/ # 报告生成模块
│       └── utils/        # 工具函数
├── tests/                # 单元测试
├── venv/                 # Python虚拟环境
├── requirements.txt      # 依赖清单
└── README.md             # 项目文档
```

## 快速开始

### 前置要求
- Python 3.9+
- pip

### 安装依赖
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 配置说明
编辑 `config/config.yaml`:
```yaml
data_source:
  type: csv
  path: data/input.csv

analysis:
  metrics:
    - loan_balance
    - deposit_growth_rate
  timeframe: monthly

output:
  format: html
  path: reports/
```

### 运行流程
```python
from aa.core import AnalysisPipeline

pipeline = AnalysisPipeline()
pipeline.run()
```

## 开发指南
1. 扩展数据加载器：继承 `BaseDataLoader`
2. 实现分析规则：继承 `BaseAnalyzer`
3. 添加报告生成器：继承 `BaseReportGenerator`

## 许可证
MIT License
