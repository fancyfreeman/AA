from aa.report_generators import ReportGenerator

if __name__ == "__main__":
    generator = ReportGenerator()
    report = generator.generate(
        analysis_results={},
        config_path="config/report_config.yaml"
    )
    
    with open("reports/demo_report.md", "w") as f:
        f.write(report)
    
    print("报告生成成功！保存至 reports/demo_report.md")