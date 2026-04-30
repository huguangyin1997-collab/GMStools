import json
from .BCompare_Feature import FeatureComparator

# 示例用法
def usage_example():
    # 创建对比器
    comparator = FeatureComparator()
    
    # 读取JSON数据
    with open('mr_feature.json', 'r', encoding='utf-8') as f:
        mr_data = json.load(f)
    
    with open('smr_feature.json', 'r', encoding='utf-8') as f:
        smr_data = json.load(f)
    
    # 进行比较
    result = comparator.compare(mr_data, smr_data)
    print(result)
    
    # 或者分别使用不同功能
    # 1. 仅严格对比
    # strict_result = comparator.strict_compare_only(mr_data, smr_data)
    # print(strict_result)
    
    # 2. 仅智能对比（返回结果对象）
    # smart_result = comparator.smart_compare_only(mr_data, smr_data)
    # print(f"状态: {smart_result.status}")
    # print(f"相同: {smart_result.summary['same']}")
    # print(f"移动: {smart_result.summary['moved']}")
    
    # 3. 智能对比并生成HTML
    # smart_result, html = comparator.smart_compare_only(
    #     mr_data, 
    #     smr_data, 
    #     output_path='smart_comparison.html'
    # )
