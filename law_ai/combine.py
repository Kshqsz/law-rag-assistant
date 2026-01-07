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
            law_books[metadata["book"]].append(doc)

    law_str = ""
    for book, docs in law_books.items():
        law_str += f"相关法律：《{book}》\n"
        law_str += "\n".join([doc.page_content.strip("\n") for doc in docs])
        law_str += "\n"

    return law_str


def combine_web_docs(docs: List[Document]) -> str:
    web_str = ""
    for doc in docs:
        web_str += f"相关网页：{doc.metadata['title']}\n"
        web_str += f"网页地址：{doc.metadata['link']}\n"
        web_str += doc.page_content.strip("\n") + "\n"
        web_str += "\n"

    return web_str
