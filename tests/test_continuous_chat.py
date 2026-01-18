# coding: utf-8
"""
连续对话功能测试脚本

测试场景：
1. 第一轮：询问具体法律问题
2. 第二轮：使用代词追问（测试上下文理解）
3. 第三轮：相关问题追问
"""
import asyncio
import sys
from backend.law_service import law_qa_service


async def test_continuous_conversation():
    """测试连续对话功能"""
    
    print("=" * 80)
    print("🧪 连续对话功能测试")
    print("=" * 80)
    
    # 初始化历史记录
    history = []
    
    # ==================== 第一轮对话 ====================
    print("\n" + "=" * 80)
    print("【第一轮对话】独立问题 - 无历史上下文")
    print("=" * 80)
    
    question1 = "故意杀人罪会判几年？"
    print(f"\n👤 用户: {question1}")
    
    answer1, law_ctx1, web_ctx1 = await law_qa_service.ask_question(
        question1,
        history=None
    )
    
    print(f"\n⚖️  律师: {answer1[:200]}...")
    print(f"\n📚 法律依据: {len(law_ctx1)} 字符")
    print(f"🌐 网络来源: {len(web_ctx1)} 字符")
    
    # 将第一轮对话加入历史
    history.append({"role": "user", "content": question1})
    history.append({"role": "assistant", "content": answer1})
    
    # ==================== 第二轮对话 ====================
    print("\n" + "=" * 80)
    print("【第二轮对话】使用代词追问 - 测试上下文理解")
    print("=" * 80)
    print(f"📝 当前历史: {len(history)} 条消息")
    
    question2 = "那如果是过失致人死亡呢？"  # 使用了"那"这个代词
    print(f"\n👤 用户: {question2}")
    
    answer2, law_ctx2, web_ctx2 = await law_qa_service.ask_question(
        question2,
        history=history
    )
    
    print(f"\n⚖️  律师: {answer2[:200]}...")
    print(f"\n📚 法律依据: {len(law_ctx2)} 字符")
    print(f"🌐 网络来源: {len(web_ctx2)} 字符")
    
    # 将第二轮对话加入历史
    history.append({"role": "user", "content": question2})
    history.append({"role": "assistant", "content": answer2})
    
    # ==================== 第三轮对话 ====================
    print("\n" + "=" * 80)
    print("【第三轮对话】继续深入追问 - 测试多轮对话")
    print("=" * 80)
    print(f"📝 当前历史: {len(history)} 条消息")
    
    question3 = "这两种情况的主要区别是什么？"  # 使用了"这两种"指代
    print(f"\n👤 用户: {question3}")
    
    answer3, law_ctx3, web_ctx3 = await law_qa_service.ask_question(
        question3,
        history=history
    )
    
    print(f"\n⚖️  律师: {answer3[:200]}...")
    print(f"\n📚 法律依据: {len(law_ctx3)} 字符")
    print(f"🌐 网络来源: {len(web_ctx3)} 字符")
    
    # ==================== 第四轮对话 ====================
    print("\n" + "=" * 80)
    print("【第四轮对话】全新问题 - 测试是否能切换话题")
    print("=" * 80)
    
    question4 = "合同违约需要承担什么责任？"  # 全新的话题
    print(f"\n👤 用户: {question4}")
    
    answer4, law_ctx4, web_ctx4 = await law_qa_service.ask_question(
        question4,
        history=history
    )
    
    print(f"\n⚖️  律师: {answer4[:200]}...")
    print(f"\n📚 法律依据: {len(law_ctx4)} 字符")
    print(f"🌐 网络来源: {len(web_ctx4)} 字符")
    
    # ==================== 测试总结 ====================
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    print("\n📊 测试结果:")
    print(f"  - 总共进行了 4 轮对话")
    print(f"  - 历史消息数量: {len(history)} 条")
    print(f"  - 第2轮成功理解上下文（代词'那'）: {'✓' if '过失' in answer2 else '✗'}")
    print(f"  - 第3轮成功理解多轮对话（'这两种'）: {'✓' if ('故意' in answer3 or '过失' in answer3) else '✗'}")
    print(f"  - 第4轮能够切换新话题: {'✓' if '合同' in answer4 else '✗'}")
    
    print("\n💡 测试建议:")
    print("  1. 检查第2轮回答是否包含'过失致人死亡'相关内容")
    print("  2. 检查第3轮回答是否对比了'故意'和'过失'的区别")
    print("  3. 检查第4轮回答是否正确切换到合同话题")
    print("  4. 启动前端界面进行实际对话测试")
    
    return True


async def test_without_history():
    """对比测试：不使用历史记录"""
    
    print("\n\n" + "=" * 80)
    print("🧪 对比测试：不使用历史记录")
    print("=" * 80)
    
    question = "那如果是过失致人死亡呢？"  # 这个问题在没有上下文时应该无法理解
    print(f"\n👤 用户: {question}")
    print("📝 历史记录: 无")
    
    answer, law_ctx, web_ctx = await law_qa_service.ask_question(
        question,
        history=None
    )
    
    print(f"\n⚖️  律师: {answer[:300]}...")
    
    print("\n💡 预期结果：")
    print("  由于没有历史上下文，AI可能会:")
    print("  - 要求澄清问题")
    print("  - 给出通用的过失致人死亡答案")
    print("  - 无法理解'那'字指代的内容")
    
    return True


def main():
    """主函数"""
    try:
        # 运行连续对话测试
        asyncio.run(test_continuous_conversation())
        
        # 运行对比测试
        asyncio.run(test_without_history())
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
