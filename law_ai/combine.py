# coding: utf-8
"""
文档合并与格式化模块

功能说明：
- combine_law_docs(docs): 将来自向量库的法律文档按书籍分组，格式化为字符串
  按照"相关法律：《书名》"的格式组织法律条文，便于传递给 LLM
  
- combine_web_docs(docs): 将来自网页的文档格式化为字符串
  按照"相关网页：网页标题"、"网页地址：URL"的格式组织网页内容

使用示例：
    from langchain.docstore.document import Document
    from law_ai.combine import combine_law_docs, combine_web_docs
    
    # 创建示例法律文档
    law_docs = [
        Document(
            page_content="第二百三十二条 故意杀人的，处死刑。",
            metadata={"book": "中华人民共和国刑法"}
        ),
        Document(
            page_content="第二百三十三条 过失致人死亡的，处三年以上七年以下有期徒刑",
            metadata={"book": "中华人民共和国刑法"}
        )
    ]
    
    # 合并法律文档
    law_text = combine_law_docs(law_docs)
    print(law_text)
    # 输出:
    # 相关法律：《中华人民共和国刑法》
    # 第二百三十二条 故意杀人的，处死刑。
    # 第二百三十三条 过失致人死亡的，处三年以上七年以下有期徒刑
    
    # 创建示例网页文档
    web_docs = [
        Document(
            page_content="根据最新法律规定，故意杀人需要承担刑事责任。",
            metadata={"title": "刑法解释", "link": "https://example.com/law"}
        )
    ]
    
    # 合并网页文档
    web_text = combine_web_docs(web_docs)
    print(web_text)
    # 输出:
    # 相关网页：刑法解释
    # 网页地址：https://example.com/law
    # 根据最新法律规定，故意杀人需要承担刑事责任。
"""
from typing import List
from collections import defaultdict

from langchain.docstore.document import Document

# example:
#   相关法律：《中华人民共和国刑法》
#   第二百三十二条 故意杀人的，处死刑。
#   第二百三十三条 过失致人死亡的，处三年以上七年以下有期徒刑
def combine_law_docs(docs: List[Document]) -> str:
    law_books = defaultdict(list)
    for doc in docs:
        metadata = doc.metadata
        if 'book' in metadata:
            content = doc.page_content.strip()
            # 只过滤空内容和纯标题（如"第一节 一般规定"这种没有实际条文的）
            # 纯标题特征：以"第"开头，且不包含"条"字
            is_empty_title = (content.startswith('第') and 
                             '条' not in content and 
                             len(content) < 30)
            
            # 保留所有非空且非纯标题的文档（包括用户上传的短文档）
            if content and not is_empty_title:
                law_books[metadata["book"]].append(doc)

    law_str = ""
    for book, docs in law_books.items():
        if docs:  # 确保有有效文档
            law_str += f"相关法律：《{book}》\n"
            law_str += "\n".join([doc.page_content.strip("\n") for doc in docs])
            law_str += "\n"

    return law_str


def combine_web_docs(docs: List[Document]) -> str:
    # 法律相关关键词
    law_keywords = ['法', '刑', '条', '规定', '法律', '条例', '刑法', '民法', 
                     '诉讼', '权利', '责任', '判', '罚', '赔偿', '刑期',
                     '犯罪', '违法', '诉讼', '仲裁', '法院', '检察',
                     '律师', '公安', '司法', '法制', '宪法']
    
    web_str = ""
    for doc in docs:
        title = doc.metadata.get('title', '')
        content = doc.page_content.strip("\n")
        
        # 检查标题或内容是否包含法律关键词
        is_law_related = any(keyword in title or keyword in content for keyword in law_keywords)
        
        # 过滤明显不相关的关键词
        irrelevant_keywords = ['Python', 'CSDN', '编程', '代码', '网络信息安全', '课后习题', 
                               '百度文库', 'Word文档', '批量读取', '数据库', 'API']
        is_irrelevant = any(keyword in title or keyword in content[:200] for keyword in irrelevant_keywords)
        
        if is_law_related and not is_irrelevant:
            web_str += f"相关网页：{title}\n"
            web_str += f"网页地址：{doc.metadata.get('link', '')}\n"
            web_str += content + "\n"
            web_str += "\n"

    return web_str
