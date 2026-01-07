# coding: utf-8
"""
法律文本分割模块

功能说明：
- LawSplitter: 自定义的文本分割器（继承 RecursiveCharacterTextSplitter）
  专用于分割法律文本（Markdown 格式）
  首先按 Markdown 标题（#, ##, ###, ####）进行结构化分割
  然后按"第XXX条"的法律条文格式进行二级分割
  保留文档的 Markdown 结构信息和原始元数据

使用示例：
    from langchain.docstore.document import Document
    from law_ai.splitter import LawSplitter
    
    # 创建示例法律文档
    doc = Document(
        page_content=\"\"\"# 中华人民共和国刑法
        
## 第二编 罪名

### 第一章 危害公共安全罪

第一百一十四条 放火、决水、爆炸、投放毒物或者以其他危险方法致人重伤、死亡或者使公私财产遭受重大损失的，处十年以上有期徒刑、无期徒刑或者死刑。

过失犯前款罪的，处三年以上七年以下有期徒刑；情节较轻的，处三年以下有期徒刑或者拘役。
\"\"\",
        metadata={"source": "law.md"}
    )
    
    # 创建分割器
    splitter = LawSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    
    # 分割文档
    split_docs = splitter.split_documents([doc])
    
    print(f"分割后共 {len(split_docs)} 个块：")
    for i, chunk in enumerate(split_docs, 1):
        print(f"\\n块 {i}:")
        print(f"  内容: {chunk.page_content[:100]}...")
        print(f"  元数据: {chunk.metadata}")
    
    # 输出示例:
    # 分割后共 2 个块：
    #
    # 块 1:
    #   内容: # 中华人民共和国刑法
    #
    # ## 第二编 罪名
    #
    # ### 第一章 危害公共安全罪...
    #   元数据: {'source': 'law.md', 'header1': '中华人民共和国刑法', 
    #           'header2': '第二编 罪名', 'header3': '第一章 危害公共安全罪',
    #           'book': '中华人民共和国刑法'}
    #
    # 块 2:
    #   内容: 第一百一十四条 放火、决水、爆炸...
    #   元数据: {'source': 'law.md', 'header1': '中华人民共和国刑法',
    #           'book': '中华人民共和国刑法'}
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.docstore.document import Document
from typing import Any, Iterable, List

class LawSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, **kwargs: Any) -> None:
        """Initialize a LawSplitter."""
        separators = [r"第\S*条 "]
        is_separator_regex = True

        headers_to_split_on = [
            ("#", "header1"),
            ("##", "header2"),
            ("###", "header3"),
            ("####", "header4"),
        ]

        self.md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        super().__init__(separators=separators, is_separator_regex=is_separator_regex, **kwargs)

    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        """Split documents."""
        texts, metadatas = [], []
        for doc in documents:
            md_docs = self.md_splitter.split_text(doc.page_content)
            for md_doc in md_docs:
                texts.append(md_doc.page_content)

                metadatas.append(
                    md_doc.metadata | doc.metadata | {"book": md_doc.metadata.get("header1")})

        return self.create_documents(texts, metadatas=metadatas)
