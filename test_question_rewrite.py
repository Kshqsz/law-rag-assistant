#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试问题重写功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.law_service import LawQAService

def test_question_rewrite():
    """测试问题重写"""
    print("=" * 80)
    print("🧪 测试问题重写功能")
    print("=" * 80)
    
    service = LawQAService()
    
    # 模拟历史对话
    history = [
        {"role": "user", "content": "故意杀人罪会判几年？"},
        {"role": "assistant", "content": "根据《中华人民共和国刑法》第232条，故意杀人的，处死刑、无期徒刑或者十年以上有期徒刑；情节较轻的，处三年以上十年以下有期徒刑。"},
        {"role": "user", "content": "那如果是过失致人死亡呢？"},
        {"role": "assistant", "content": "过失致人死亡罪根据《刑法》第233条，处三年以上七年以下有期徒刑；情节较轻的，处三年以下有期徒刑。"}
    ]
    
    # 测试包含代词的问题
    test_questions = [
        "这两种情况的主要区别是什么？",
        "那个刑期更长？",
        "它们在主观方面有何不同？",
        "合同违约怎么处理？"  # 不包含代词
    ]
    
    for question in test_questions:
        print(f"\n原问题: {question}")
        
        # 检查是否包含代词
        has_pronoun = service._contains_pronoun(question)
        print(f"包含代词: {has_pronoun}")
        
        if has_pronoun:
            # 重写问题
            rewritten = service._rewrite_question_with_history(question, history)
            print(f"重写后: {rewritten}")
        else:
            print("无需重写")
        
        print("-" * 60)

if __name__ == "__main__":
    test_question_rewrite()
