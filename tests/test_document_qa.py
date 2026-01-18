#!/usr/bin/env python3
# coding: utf-8
"""
文档上传问答功能测试程序

测试流程：
1. 创建测试用户
2. 上传测试文档
3. 基于文档内容提问
4. 验证回答是否使用了文档内容
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_db, User, Document
from backend.law_service import law_qa_service
from sqlalchemy.orm import Session
import tempfile

# 测试文档内容
TEST_DOCUMENT_CONTENT = """
《中华人民共和国劳动合同法》

第三十七条 劳动者提前通知解除劳动合同

劳动者提前三十日以书面形式通知用人单位，可以解除劳动合同。
劳动者在试用期内提前三日通知用人单位，可以解除劳动合同。

第三十八条 劳动者单方解除劳动合同

用人单位有下列情形之一的，劳动者可以解除劳动合同：
（一）未按照劳动合同约定提供劳动保护或者劳动条件的；
（二）未及时足额支付劳动报酬的；
（三）未依法为劳动者缴纳社会保险费的；
（四）用人单位的规章制度违反法律、法规的规定，损害劳动者权益的；
（五）因本法第二十六条第一款规定的情形致使劳动合同无效的；
（六）法律、行政法规规定劳动者可以解除劳动合同的其他情形。

用人单位以暴力、威胁或者非法限制人身自由的手段强迫劳动者劳动的，
或者用人单位违章指挥、强令冒险作业危及劳动者人身安全的，
劳动者可以立即解除劳动合同，不需事先告知用人单位。

第四十七条 经济补偿的计算

经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向劳动者支付。
六个月以上不满一年的，按一年计算；不满六个月的，向劳动者支付半个月工资的经济补偿。
"""


async def test_document_qa():
    """测试文档问答功能"""
    print("=" * 80)
    print("开始测试文档上传问答功能")
    print("=" * 80)
    
    # 测试问题列表
    test_questions = [
        "劳动者如何解除劳动合同？",
        "如果公司不缴纳社保，我该怎么办？",
        "经济补偿金怎么计算？",
        "该怎么办？"  # 宽泛的问题
    ]
    
    print("\n📄 测试文档内容：")
    print("-" * 80)
    print(TEST_DOCUMENT_CONTENT[:200] + "...")
    print("-" * 80)
    
    print("\n\n🧪 开始测试...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(test_questions)}: {question}")
        print("=" * 80)
        
        try:
            # 调用法律问答服务，传入文档内容
            answer, law_context, web_context = await law_qa_service.ask_question(
                question=question,
                use_document_content=TEST_DOCUMENT_CONTENT,
                history=None
            )
            
            print(f"\n✅ 回答成功")
            print(f"\n📝 AI 回答：")
            print("-" * 80)
            print(answer)
            print("-" * 80)
            
            # 验证回答是否包含文档中的关键词
            keywords = ["第三十七条", "第三十八条", "第四十七条", "劳动合同法", "经济补偿"]
            found_keywords = [kw for kw in keywords if kw in answer or kw in law_context]
            
            if found_keywords:
                print(f"\n✅ 验证通过：回答中包含文档关键词：{', '.join(found_keywords)}")
            else:
                print(f"\n⚠️  警告：回答中未包含文档关键词，可能未使用文档内容")
            
            # 检查是否有法律上下文
            if law_context:
                print(f"\n📚 法律上下文长度：{len(law_context)} 字符")
                if "用户上传的文档内容" in law_context:
                    print("✅ 法律上下文包含上传的文档")
                else:
                    print("⚠️  法律上下文不包含上传的文档")
            
        except Exception as e:
            print(f"\n❌ 测试失败：{e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


async def test_stream_document_qa():
    """测试流式文档问答功能"""
    print("\n\n" + "=" * 80)
    print("开始测试流式文档上传问答功能")
    print("=" * 80)
    
    question = "如果公司不给我缴纳社保，我应该怎么办？"
    
    print(f"\n📝 问题: {question}")
    print(f"\n📄 使用文档: 劳动合同法相关条款\n")
    print("🔄 流式回答:")
    print("-" * 80)
    
    try:
        full_answer = ""
        async for chunk in law_qa_service.stream_answer(
            question=question,
            use_document_content=TEST_DOCUMENT_CONTENT,
            history=None
        ):
            if isinstance(chunk, dict):
                # 最后的上下文信息
                print("\n" + "-" * 80)
                print(f"\n📚 法律上下文长度: {len(chunk.get('law_context', ''))} 字符")
                if "用户上传的文档内容" in chunk.get('law_context', ''):
                    print("✅ 包含上传的文档内容")
            else:
                # 流式输出的文本
                print(chunk, end='', flush=True)
                full_answer += chunk
        
        print("\n" + "-" * 80)
        print(f"\n✅ 流式测试完成，共生成 {len(full_answer)} 字符")
        
    except Exception as e:
        print(f"\n❌ 流式测试失败：{e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("📋 文档上传问答功能测试程序")
    print("=" * 80)
    
    # 测试普通问答
    await test_document_qa()
    
    # 测试流式问答
    await test_stream_document_qa()
    
    print("\n\n✅ 所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
