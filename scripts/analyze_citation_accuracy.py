# coding: utf-8
"""
法律引用准确率分析脚本

功能：
1. 从数据库读取所有对话
2. 提取答案中的法律条文引用（《法律名》、第XX条等）
3. 验证这些引用是否存在于对应的law_context中
4. 生成详细的准确率报告

使用方法：
    python scripts/analyze_citation_accuracy.py [options]
    
选项：
    --limit 10          只分析最近10条对话（用于测试）
    --output-dir results 输出目录（默认为evaluation_results）
    --user-id 1         只分析特定用户的对话
"""

import sys
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, Message, Conversation, User


class CitationExtractor:
    """从答案中提取法律引用"""
    
    # 法律名称的规范化字典（处理简称和全称）
    # 支持：全称、简称、带《》的各种形式
    LAW_ALIASES = {
        '刑法': {
            '刑法', '《刑法》', '《中华人民共和国刑法》',
        },
        '民法': {
            '民法', '民法典', '《民法》', '《民法典》', 
            '《中华人民共和国民法典》', '《中华人民共和国民法》'
        },
        '劳动法': {
            '劳动法', '《劳动法》', '《中华人民共和国劳动法》'
        },
        '合同法': {
            '合同法', '《合同法》', '《中华人民共和国合同法》'
        },
        '婚姻法': {
            '婚姻法', '《婚姻法》', '《中华人民共和国婚姻法》'
        },
        '继承法': {
            '继承法', '《继承法》', '《中华人民共和国继承法》'
        },
        '侵权责任法': {
            '侵权责任法', '《侵权责任法》', '《中华人民共和国侵权责任法》'
        },
        '行政法': {
            '行政法', '《行政法》'
        },
        '税法': {
            '税法', '《税法》'
        },
        '商法': {
            '商法', '《商法》'
        },
        '宪法': {
            '宪法', '《宪法》', '《中华人民共和国宪法》'
        },
        '诉讼法': {
            '诉讼法', '《诉讼法》'
        },
        '民事诉讼法': {
            '民事诉讼法', '民诉法', '《民事诉讼法》', '《民诉法》',
            '《中华人民共和国民事诉讼法》'
        },
        '刑事诉讼法': {
            '刑事诉讼法', '刑诉法', '《刑事诉讼法》', '《刑诉法》',
            '《中华人民共和国刑事诉讼法》'
        },
        '行政诉讼法': {
            '行政诉讼法', '行诉法', '《行政诉讼法》', '《行诉法》',
            '《中华人民共和国行政诉讼法》'
        },
        '道路交通安全法': {
            '道路交通安全法', '道交法', '《道路交通安全法》', '《道交法》',
            '《中华人民共和国道路交通安全法》', '交通法'
        },
        '公路法': {
            '公路法', '《公路法》', '《中华人民共和国公路法》'
        },
        '铁路法': {
            '铁路法', '《铁路法》', '《中华人民共和国铁路法》'
        },
        '民用航空法': {
            '民用航空法', '航空法', '《民用航空法》', '《航空法》',
            '《中华人民共和国民用航空法》'
        },
        '海商法': {
            '海商法', '《海商法》', '《中华人民共和国海商法》'
        },
        '破产法': {
            '破产法', '《破产法》', '《中华人民共和国破产法》'
        },
        '公司法': {
            '公司法', '《公司法》', '《中华人民共和国公司法》'
        },
        '证券法': {
            '证券法', '《证券法》', '《中华人民共和国证券法》'
        },
        '保险法': {
            '保险法', '《保险法》', '《中华人民共和国保险法》'
        },
        '票据法': {
            '票据法', '《票据法》', '《中华人民共和国票据法》'
        },
        '反不正当竞争法': {
            '反不正当竞争法', '《反不正当竞争法》'
        },
        '商标法': {
            '商标法', '《商标法》', '《中华人民共和国商标法》'
        },
        '著作权法': {
            '著作权法', '《著作权法》', '《中华人民共和国著作权法》'
        },
        '专利法': {
            '专利法', '《专利法》', '《中华人民共和国专利法》'
        },
        '环境保护法': {
            '环境保护法', '环保法', '《环境保护法》', '《环保法》',
            '《中华人民共和国环境保护法》'
        },
        '土地管理法': {
            '土地管理法', '《土地管理法》', '《中华人民共和国土地管理法》'
        },
        '城市房地产管理法': {
            '城市房地产管理法', '房地产法', '《城市房地产管理法》',
            '《中华人民共和国城市房地产管理法》'
        },
        '物权法': {
            '物权法', '《物权法》', '《中华人民共和国物权法》'
        },
    }
    
    def extract_citations(self, text: str) -> List[Dict]:
        """
        从文本中提取法律引用
        
        支持的格式：
        1. 《刑法》第233条
        2. 刑法第233条
        3. 故意杀人（刑法第232条）- 全角括号内的法律+条号
        4. 故意杀人(刑法第232条) - 半角括号内的法律+条号
        5. （刑法第232条） - 单独的全角括号
        6. (刑法第232条) - 单独的半角括号
        7. 道交法（道路交通安全法的简称）
        8. 仅《法律名》
        
        返回列表，每个元素为：
        {
            "law_name": "刑法",  # 标准化后的法律名称
            "article_num": "233",  # 条号（如果有）
            "matched_text": "《刑法》第233条",  # 原始匹配文本
            "position": 42  # 在文本中的位置
        }
        """
        citations = []
        used_positions = set()  # 跟踪已使用的位置，避免重复匹配
        
        # 模式0a: 全角括号内的法律+条号（刑法第232条）
        # 支持：（刑法第232条）或 xxx（刑法第232条）这样的格式
        # 关键：支持括号内有逗号的情况，如：（涉嫌妨害作证罪，刑法第307条）
        pattern0a = r'[（(]([^）)]*?法(?:典)?)\s*第\s*(\d+)\s*条[）)]'
        for match in re.finditer(pattern0a, text):
            law_full = match.group(1).strip()
            article_num = match.group(2)
            
            # 跳过如果这个位置已经被匹配过
            if match.start() in used_positions:
                continue
            
            # 关键修复：如果括号内有逗号，需要清理法律名
            # 例如："涉嫌妨害作证罪，刑法" -> "刑法"
            if '，' in law_full:
                # 从最后一个"，"之后开始
                parts = law_full.split('，')
                law_full = parts[-1].strip()
            elif ',' in law_full:
                parts = law_full.split(',')
                law_full = parts[-1].strip()
            
            law_name = self._normalize_law_name(law_full)
            
            citations.append({
                "law_name": law_name,
                "law_full": law_full,
                "article_num": article_num,
                "matched_text": match.group(0),
                "position": match.start(),
                "citation_type": "article"
            })
            used_positions.add(match.start())
        
        # 模式1: 《法律名》第XX条
        pattern1 = r'《([^》]+)》\s*第\s*(\d+)\s*条'
        for match in re.finditer(pattern1, text):
            if match.start() in used_positions:
                continue
            
            law_full = match.group(1)
            article_num = match.group(2)
            law_name = self._normalize_law_name(law_full)
            
            # 避免重复
            if not any(c['article_num'] == article_num and c.get('law_name') == law_name for c in citations):
                citations.append({
                    "law_name": law_name,
                    "law_full": law_full,
                    "article_num": article_num,
                    "matched_text": match.group(0),
                    "position": match.start(),
                    "citation_type": "article"
                })
                used_positions.add(match.start())
        
        # 模式2: 法律名第XX条（不要求《》符号，包括简称）
        # 匹配：刑法第233条、道交法第50条、民事诉讼法第123条 等
        # 重要：排除已经在括号中被匹配过的，且排除各种分隔符和括号
        pattern2 = r'(?:《)?([^》\s（(，,；;、・\.\-~]+?法(?:典)?)\s*第\s*(\d+(?:\.\d+)?)\s*条'
        for match in re.finditer(pattern2, text):
            if match.start() in used_positions:
                continue
            
            law_full = match.group(1)
            article_num = match.group(2).split('.')[0]  # 取第一个数字部分
            
            # 额外的清理：如果仍包含某些奇怪字符，只取最后一部分
            for sep in ['，', ',', '；', ';', '、', '・', '-', '~']:
                if sep in law_full:
                    law_full = law_full.split(sep)[-1].strip()
            
            law_name = self._normalize_law_name(law_full)
            
            # 避免重复（检查是否与已有的冲突）
            if not any(c['article_num'] == article_num and c.get('law_name') == law_name for c in citations):
                citations.append({
                    "law_name": law_name,
                    "law_full": law_full,
                    "article_num": article_num,
                    "matched_text": match.group(0),
                    "position": match.start(),
                    "citation_type": "article"
                })
                used_positions.add(match.start())
        
        # 模式3: 仅《法律名》（不带条号）
        pattern3 = r'《([^》]+法(?:典)?)》'
        for match in re.finditer(pattern3, text):
            if match.start() in used_positions:
                continue
            
            law_full = match.group(1)
            law_name = self._normalize_law_name(law_full)
            
            # 仅当没有对应的条文引用时才添加
            if not any(c.get('law_name') == law_name and c['citation_type'] == 'article' for c in citations):
                citations.append({
                    "law_name": law_name,
                    "law_full": law_full,
                    "article_num": None,
                    "matched_text": match.group(0),
                    "position": match.start(),
                    "citation_type": "law"
                })
                used_positions.add(match.start())
        
        return citations
    
    def _normalize_law_name(self, law_full: str) -> str:
        """规范化法律名称（将简称和全称统一为简称）"""
        law_full = law_full.strip('《》').strip()
        
        # 直接精确匹配
        for standard_name, aliases in self.LAW_ALIASES.items():
            if law_full in aliases:
                return standard_name
        
        # 如果不在预定义字典中，尝试智能匹配
        # 策略1: 检查是否是某个别名的子字符串或父字符串
        law_full_lower = law_full.lower()
        for standard_name, aliases in self.LAW_ALIASES.items():
            for alias in aliases:
                alias_lower = alias.lower()
                # 如果law_full包含alias的关键部分，或alias包含law_full的关键部分
                # 例如："道交法" 包含于 "《道路交通安全法》"
                if (law_full_lower in alias_lower or 
                    alias_lower in law_full_lower or
                    law_full_lower.replace('《', '').replace('》', '') == alias_lower.replace('《', '').replace('》', '')):
                    return standard_name
        
        # 策略2: 基于关键字匹配（对于未来可能出现的新法律）
        # 例如："某某法" 可以通过"法"字来识别
        for standard_name, aliases in self.LAW_ALIASES.items():
            # 提取标准名的关键字（去掉"法"、"典"、"规定"等）
            key_part = standard_name.replace('法', '').replace('典', '').replace('规定', '')
            if key_part and key_part in law_full:
                return standard_name
        
        # 如果还是无法匹配，返回原始值
        return law_full


class CitationValidator:
    """验证引用是否存在于law_context中"""
    
    @staticmethod
    def _format_article_numbers(article_num: str) -> List[str]:
        """
        将阿拉伯数字条号转换为多种可能的形式
        
        例如：232 -> ["232", "二百三十二", "第232条", "第二百三十二条", ...]
        """
        formats = [
            article_num,  # 原始形式
            f"第{article_num}条",  # 带第和条
            f"第{article_num}",  # 仅带第
            f"{article_num}条"  # 仅带条
        ]
        
        # 尝试转换为汉字形式
        try:
            chinese_num = CitationValidator._num_to_chinese(int(article_num))
            if chinese_num:
                formats.extend([
                    chinese_num,
                    f"第{chinese_num}条",
                    f"第{chinese_num}",
                    f"{chinese_num}条"
                ])
        except:
            pass
        
        return formats
    
    @staticmethod
    def _num_to_chinese(num: int) -> str:
        """将阿拉伯数字转换为汉字形式"""
        if num <= 0 or num > 9999:
            return ""
        
        chars = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
        units = ['', '十', '百', '千']
        
        def convert_group(n):
            """转换0-999的数字"""
            if n == 0:
                return ''
            if n < 10:
                return chars[n]
            if n < 100:
                tens = n // 10
                ones = n % 10
                result = chars[tens] + units[1]
                if ones > 0:
                    result += chars[ones]
                return result
            else:
                hundreds = n // 100
                remainder = n % 100
                result = chars[hundreds] + units[2]
                if remainder == 0:
                    return result
                if remainder < 10:
                    result += '○' if remainder == 0 else chars[remainder]
                else:
                    tens = remainder // 10
                    ones = remainder % 10
                    result += chars[tens] + units[1]
                    if ones > 0:
                        result += chars[ones]
                return result
        
        if num < 10:
            return chars[num]
        elif num < 100:
            tens = num // 10
            ones = num % 10
            result = chars[tens] + units[1]
            if ones > 0:
                result += chars[ones]
            return result
        elif num < 1000:
            hundreds = num // 100
            remainder = num % 100
            result = chars[hundreds] + units[2]
            if remainder == 0:
                return result.replace('零零', '零')
            if remainder < 10:
                result += '零' + chars[remainder]
            else:
                tens = remainder // 10
                ones = remainder % 10
                result += chars[tens] + units[1]
                if ones > 0:
                    result += chars[ones]
            return result.replace('零零', '零')
        else:
            thousands = num // 1000
            remainder = num % 1000
            result = chars[thousands] + units[3]
            hundreds = remainder // 100
            if hundreds > 0:
                result += chars[hundreds] + units[2]
                remainder = remainder % 100
                if remainder == 0:
                    return result
                if remainder < 10:
                    result += '零' + chars[remainder]
                else:
                    tens = remainder // 10
                    ones = remainder % 10
                    result += chars[tens] + units[1]
                    if ones > 0:
                        result += chars[ones]
            else:
                result += '零'
                ten_remainder = remainder % 100
                if ten_remainder > 0:
                    if ten_remainder < 10:
                        result += '零' + chars[ten_remainder]
                    else:
                        tens = ten_remainder // 10
                        ones = ten_remainder % 10
                        result += chars[tens] + units[1]
                        if ones > 0:
                            result += chars[ones]
            return result.replace('零零', '零').rstrip('零')
    
    def verify_citations(
        self,
        citations: List[Dict],
        law_context: str
    ) -> Dict:
        """
        验证引用列表
        
        返回：
        {
            "verified": [...],  # 已验证的引用
            "unverified": [...],  # 未验证的引用（可能是虚构）
            "accuracy_score": 0.85,
            "details": [...]
        }
        """
        verified = []
        unverified = []
        
        for citation in citations:
            law_name = citation['law_name']
            article_num = citation['article_num']
            
            # 在law_context中搜索
            is_found = False
            found_context = ""
            
            if article_num:
                # 搜索条号出现
                # 支持多种格式: "第233条"、"233条"、"第二百三十三条"等
                formats = self._format_article_numbers(article_num)
                
                for fmt in formats:
                    # 转义数字以避免正则表达式错误
                    pattern = re.escape(fmt)
                    if re.search(pattern, law_context):
                        is_found = True
                        # 提取上下文（前后各50个字符）
                        match = re.search(pattern, law_context)
                        start = max(0, match.start() - 50)
                        end = min(len(law_context), match.end() + 50)
                        found_context = law_context[start:end]
                        break
            else:
                # 仅验证法律名是否出现
                if law_name in law_context or f"《{law_name}》" in law_context:
                    is_found = True
            
            result = {
                "citation": citation,
                "is_verified": is_found,
                "found_context": found_context[:100] if found_context else "",
                "status": "✓ 已验证" if is_found else "✗ 未验证"
            }
            
            if is_found:
                verified.append(result)
            else:
                unverified.append(result)
        
        # 计算准确率
        total = len(citations) if citations else 1
        accuracy = len(verified) / total if citations else 1.0
        
        return {
            "verified": verified,
            "unverified": unverified,
            "accuracy_score": accuracy,
            "verified_count": len(verified),
            "unverified_count": len(unverified),
            "total_citations": len(citations)
        }


class AccuracyReportGenerator:
    """生成准确率报告"""
    
    def __init__(self, output_dir: str = "evaluation_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(
        self,
        results: List[Dict],
        report_name: str = None
    ) -> str:
        """
        生成报告并保存
        
        返回：报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = report_name or f"citation_accuracy_{timestamp}"
        
        # 计算统计数据
        total_messages = len(results)
        total_citations = sum(r['total_citations'] for r in results)
        total_verified = sum(r['verified_count'] for r in results)
        total_unverified = sum(r['unverified_count'] for r in results)
        
        # 平均准确率
        avg_accuracy = sum(r['accuracy_score'] for r in results) / total_messages if results else 0
        
        # 按对话统计
        conversation_stats = defaultdict(lambda: {"verified": 0, "unverified": 0, "accuracy": 0})
        for r in results:
            conv_id = r['conversation_id']
            conversation_stats[conv_id]['verified'] += r['verified_count']
            conversation_stats[conv_id]['unverified'] += r['unverified_count']
            conversation_stats[conv_id]['accuracy'] = r['accuracy_score']
        
        # 问题分类统计
        by_category = defaultdict(lambda: {"count": 0, "accuracy": 0})
        for r in results:
            category = r.get('category', '其他')
            by_category[category]['count'] += 1
            by_category[category]['accuracy'] += r['accuracy_score']
        
        for category in by_category:
            by_category[category]['accuracy'] /= by_category[category]['count']
        
        # 生成JSON报告
        summary = {
            "report_name": report_name,
            "generated_at": datetime.now().isoformat(),
            "analysis_summary": {
                "total_ai_messages": total_messages,
                "total_citations": total_citations,
                "verified_citations": total_verified,
                "unverified_citations": total_unverified,
                "overall_accuracy": round(avg_accuracy, 4),
                "accuracy_percentage": f"{avg_accuracy * 100:.1f}%"
            },
            "conversation_level": {
                "count": len(conversation_stats),
                "stats": {
                    conv_id: {
                        "verified": stats['verified'],
                        "unverified": stats['unverified'],
                        "accuracy": round(stats['accuracy'], 4)
                    }
                    for conv_id, stats in conversation_stats.items()
                }
            },
            "detailed_results": [
                {
                    "conversation_id": r['conversation_id'],
                    "user_id": r['user_id'],
                    "question": r['question'][:100],
                    "answer_length": len(r['answer']),
                    "total_citations": r['total_citations'],
                    "verified_count": r['verified_count'],
                    "unverified_count": r['unverified_count'],
                    "accuracy_score": round(r['accuracy_score'], 4),
                    "unverified_citations": [
                        {
                            "matched_text": u['citation']['matched_text'],
                            "law_name": u['citation']['law_name'],
                            "article_num": u['citation'].get('article_num')
                        }
                        for u in r['unverified'][:3]  # 仅保存前3个
                    ]
                }
                for r in results[:50]  # 详细结果仅保存前50条
            ]
        }
        
        # 保存JSON报告
        json_path = os.path.join(self.output_dir, f"{report_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 生成可读的文本报告
        text_report = self._generate_text_report(summary)
        text_path = os.path.join(self.output_dir, f"{report_name}.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        
        # 生成CSV详细报告
        csv_path = self._generate_csv_report(results, report_name)
        
        return {
            "json_path": json_path,
            "text_path": text_path,
            "csv_path": csv_path
        }
    
    def _generate_text_report(self, summary: Dict) -> str:
        """生成可读的文本报告"""
        
        report = f"""
{'='*70}
                    法律引用准确率分析报告
{'='*70}

生成时间: {summary['generated_at']}
报告名称: {summary['report_name']}

【核心指标】
───────────────────────────────────────────────────────────────────
✓ 已验证引用数:    {summary['analysis_summary']['verified_citations']}
✗ 未验证引用数:    {summary['analysis_summary']['unverified_citations']}
──────────────────────────────────────────────────────────────────
✓ 总引用数:        {summary['analysis_summary']['total_citations']}
✓ 分析的对话数:    {summary['analysis_summary']['total_ai_messages']}

【准确率评估】
───────────────────────────────────────────────────────────────────
📊 总体准确率:     {summary['analysis_summary']['accuracy_percentage']}
   （{summary['analysis_summary']['verified_citations']} / {summary['analysis_summary']['total_citations']}）

【质量评分】
───────────────────────────────────────────────────────────────────
"""
        
        accuracy = summary['analysis_summary']['overall_accuracy']
        if accuracy >= 0.95:
            quality = "🌟 excellent (优秀)"
        elif accuracy >= 0.85:
            quality = "⭐ good (良好)"
        elif accuracy >= 0.70:
            quality = "👍 fair (一般)"
        else:
            quality = "⚠️  needs improvement (需改进)"
        
        report += f"评级：{quality}\n"
        report += f"\n【建议】\n"
        
        if accuracy < 0.70:
            report += "⚠️  准确率较低，当前存在 {:.0f}% 的虚构风险\n".format((1 - accuracy) * 100)
            report += "    建议：\n"
            report += "    1. 检查提示词，强调必须基于检索结果\n"
            report += "    2. 检查检索是否正常（相似度分数）\n"
            report += "    3. 增加拒答机制\n"
        elif accuracy < 0.85:
            report += "⚠️  还有一些虚构内容，建议继续改进\n"
        else:
            report += "✅ 引用准确率良好\n"
        
        report += "\n" + "="*70 + "\n"
        
        return report
    
    def _generate_csv_report(self, results: List[Dict], report_name: str) -> str:
        """生成CSV详细报告"""
        import csv
        
        csv_path = os.path.join(self.output_dir, f"{report_name}_detail.csv")
        
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                '对话ID', '用户ID', '问题', '答案长度',
                '总引用数', '已验证', '未验证', '准确率',
                '未验证的引用1', '未验证的引用2', '未验证的引用3'
            ])
            
            for r in results:
                unverified_texts = [
                    u['citation']['matched_text']
                    for u in r['unverified'][:3]
                ]
                unverified_texts.extend([''] * (3 - len(unverified_texts)))
                
                writer.writerow([
                    r['conversation_id'],
                    r['user_id'],
                    r['question'][:50],
                    len(r['answer']),
                    r['total_citations'],
                    r['verified_count'],
                    r['unverified_count'],
                    f"{r['accuracy_score']*100:.1f}%",
                    *unverified_texts
                ])
        
        return csv_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="分析法律引用准确率")
    parser.add_argument('--limit', type=int, default=0, help='限制分析的对话数（0表示全部）')
    parser.add_argument('--output-dir', type=str, default='evaluation_results', help='输出目录')
    parser.add_argument('--user-id', type=int, default=None, help='仅分析特定用户')
    
    args = parser.parse_args()
    
    # 初始化
    extractor = CitationExtractor()
    validator = CitationValidator()
    report_gen = AccuracyReportGenerator(args.output_dir)
    
    # 从数据库加载数据
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("📊 法律引用准确率分析")
        print("="*70)
        print(f"⏳ 加载数据库...")
        
        # 查询所有包含law_context的对话
        query = db.query(
            Message.id,
            Message.content,
            Message.law_context,
            Message.conversation_id,
            Conversation.user_id,
            Message.created_at
        ).join(
            Conversation, Message.conversation_id == Conversation.id
        ).filter(
            Message.role == "assistant",
            Message.law_context != None,
            Message.law_context != ""
        )
        
        if args.user_id:
            query = query.filter(Conversation.user_id == args.user_id)
        
        messages = query.order_by(Message.created_at.desc())
        
        if args.limit > 0:
            messages = messages.limit(args.limit)
        
        messages = messages.all()
        
        print(f"✓ 加载了 {len(messages)} 条AI回答\n")
        
        if not messages:
            print("❌ 没有找到有law_context的对话")
            return
        
        # 分析每条对话
        results = []
        
        for idx, msg in enumerate(messages, 1):
            message_id, answer, law_context, conv_id, user_id, created_at = msg
            
            # 提取引用
            citations = extractor.extract_citations(answer)
            
            # 验证引用
            validation = validator.verify_citations(citations, law_context)
            
            # 获取问题
            question_msg = db.query(Message).filter(
                Message.conversation_id == conv_id,
                Message.role == "user"
            ).first()
            question = question_msg.content if question_msg else "未找到问题"
            
            result = {
                "message_id": message_id,
                "conversation_id": conv_id,
                "user_id": user_id,
                "question": question,
                "answer": answer,
                "created_at": created_at.isoformat() if created_at else "",
                "citations": citations,
                "verified": validation['verified'],
                "unverified": validation['unverified'],
                "verified_count": validation['verified_count'],
                "unverified_count": validation['unverified_count'],
                "total_citations": validation['total_citations'],
                "accuracy_score": validation['accuracy_score']
            }
            
            results.append(result)
            
            # 实时进度
            if idx % 10 == 0 or idx == len(messages):
                avg_acc = sum(r['accuracy_score'] for r in results) / len(results)
                print(f"  [{idx}/{len(messages)}] 平均准确率: {avg_acc*100:.1f}%")
        
        print(f"\n✓ 分析完成！\n")
        
        # 生成报告
        print("📝 生成报告...")
        report_paths = report_gen.generate_report(results)
        
        print(f"✓ 报告已保存到:")
        print(f"   - JSON: {report_paths['json_path']}")
        print(f"   - 文本: {report_paths['text_path']}")
        print(f"   - CSV:  {report_paths['csv_path']}")
        
        # 打印摘要
        total_citations = sum(r['total_citations'] for r in results)
        total_verified = sum(r['verified_count'] for r in results)
        avg_accuracy = sum(r['accuracy_score'] for r in results) / len(results) if results else 0
        
        print("\n" + "="*70)
        print("【统计摘要】")
        print("="*70)
        print(f"分析的AI回答:     {len(results)} 条")
        print(f"总引用数:         {total_citations} 条")
        print(f"✓ 已验证:        {total_verified} 条")
        print(f"✗ 未验证:        {total_citations - total_verified} 条")
        print(f"──────────────────────────────────────────────────")
        print(f"📊 总体准确率:    {avg_accuracy*100:.1f}%")
        print("="*70 + "\n")
        
        # 列出准确率最低的5条对话
        if results:
            print("【准确率最低的对话】:")
            sorted_results = sorted(results, key=lambda x: x['accuracy_score'])
            for r in sorted_results[:5]:
                print(f"  - 对话{r['conversation_id']}: {r['question'][:30]}... → {r['accuracy_score']*100:.0f}%")
                if r['unverified']:
                    for u in r['unverified'][:2]:
                        print(f"    ✗ {u['citation']['matched_text']}")
            print()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
