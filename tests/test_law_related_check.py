#!/usr/bin/env python3
# coding: utf-8
"""
测试法律相关性判断逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.law_service import LawQAService

def test_law_related_check():
    """测试法律相关性判断"""
    service = LawQAService()
    
    print("\n" + "="*60)
    print("测试 1: 无上下文，宽泛问题 - 应该返回 False")
    print("="*60)
    question = "那这两者有什么关系"
    history = []
    result = service.is_law_related(question, history)
    print(f"问题: {question}")
    print(f"历史: {history}")
    print(f"结果: {result}")
    print(f"预期: False")
    print(f"✅ 通过" if not result else "❌ 失败")
    
    print("\n" + "="*60)
    print("测试 2: 有法律概念上下文，宽泛问题 - 应该返回 True")
    print("="*60)
    question = "那这两者有什么区别"
    history = [
        {"role": "user", "content": "什么是故意杀人"},
        {"role": "assistant", "content": "故意杀人是指..."},
        {"role": "user", "content": "什么是过失杀人"},
        {"role": "assistant", "content": "过失杀人是指..."}
    ]
    result = service.is_law_related(question, history)
    print(f"问题: {question}")
    print(f"历史: 包含故意杀人、过失杀人的讨论")
    print(f"结果: {result}")
    print(f"预期: True")
    print(f"✅ 通过" if result else "❌ 失败")
    
    print("\n" + "="*60)
    print("测试 3: 直接的法律问题 - 应该返回 True")
    print("="*60)
    question = "合同纠纷怎么处理"
    history = []
    result = service.is_law_related(question, history)
    print(f"问题: {question}")
    print(f"历史: {history}")
    print(f"结果: {result}")
    print(f"预期: True")
    print(f"✅ 通过" if result else "❌ 失败")
    
    print("\n" + "="*60)
    print("测试 4: 日常问题 - 应该返回 False")
    print("="*60)
    question = "今天天气怎么样"
    history = []
    result = service.is_law_related(question, history)
    print(f"问题: {question}")
    print(f"历史: {history}")
    print(f"结果: {result}")
    print(f"预期: False")
    print(f"✅ 通过" if not result else "❌ 失败")

if __name__ == "__main__":
    test_law_related_check()
