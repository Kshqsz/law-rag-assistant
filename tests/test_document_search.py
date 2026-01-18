#!/usr/bin/env python3
# coding: utf-8
"""
测试文档上传后的法律检索增强功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.law_service import LawQAService

def test_document_enhanced_search():
    """测试文档增强检索"""
    service = LawQAService()
    
    # 模拟上传的文档内容
    document_content = """
    甲方与乙方于2023年1月1日签订了一份房屋租赁合同，约定租期为一年，
    月租金5000元。合同签订后，乙方按时支付了前三个月的租金，但从第四个月开始，
    乙方以各种理由拖欠租金。现在已经拖欠了三个月共计15000元。
    甲方多次催促，乙方仍然不支付。
    """
    
    question = "我该怎么办？"
    
    print("\n" + "="*60)
    print("测试: 文档增强检索")
    print("="*60)
    print(f"\n📄 文档内容（节选）:\n{document_content.strip()[:100]}...\n")
    print(f"❓ 用户问题: {question}\n")
    
    # 注意：这里只是模拟，实际的检索增强在 chain.py 中的 enhance_search_with_document 函数
    # 真实的测试需要启动后端服务并上传文档
    
    print("🔍 预期效果:")
    print("   1. 检索问题会结合文档内容: '我该怎么办？ 涉及内容：甲方与乙方于2023年1月1日签订...'")
    print("   2. 检索到的法律文献应该与'租赁合同'、'拖欠租金'相关")
    print("   3. 而不是检索到无关的法律条文")
    print("\n✅ 检索增强逻辑已实现在 law_ai/chain.py 的 enhance_search_with_document 函数中")
    print("   - 会提取文档前300字符")
    print("   - 将其与问题结合形成增强检索问题")
    print("   - 用于向量库和网页检索")

if __name__ == "__main__":
    test_document_enhanced_search()
