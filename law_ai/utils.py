# coding: utf-8
"""
工具模块：模型、向量库和数据处理

功能说明：
- DashScopeEmbeddings: 自定义的文本向量化模型（继承 Embeddings）
  使用阿里云 DashScope 的 text-embedding-v2 模型
  支持批量文本向量化（最多 25 条/批）
  支持单条文本向量化
  
- get_embedding_model(): 获取 Embedding 模型实例
  
- get_cached_embedder(): 获取带缓存的 Embedding 模型
  缓存存储在 .cache/embeddings 目录
  
- get_record_manager(namespace): 获取向量库记录管理器
  基于 SQLite 数据库存储记录
  
- get_vectorstore(collection_name): 获取 Chroma 向量库实例
  默认持久化存储在 ./chroma_db
  
- clear_vectorstore(collection_name): 清空指定集合的所有数据
  
- get_model(model, streaming, callbacks): 获取 LLM 模型（ChatOpenAI）
  默认使用 qwen-plus 模型
  通过 DashScope OpenAI 兼容接口调用
  
- law_index(docs, show_progress): 将文档导入向量库
  自动处理重复和更新

使用示例：
    from law_ai.utils import (
        get_embedding_model, 
        get_vectorstore, 
        get_model,
        law_index
    )
    from law_ai.loader import LawLoader
    from law_ai.splitter import LawSplitter
    
    # 示例 1: 获取模型
    embedding_model = get_embedding_model()
    vectors = embedding_model.embed_documents(["民法典", "刑法"])
    print(f"向量维度: {len(vectors[0])}")  # 输出: 向量维度: 1536
    
    # 示例 2: 获取向量库
    vectorstore = get_vectorstore("law")
    # vectorstore 可用于相似度搜索
    
    # 示例 3: 初始化法律数据库（完整流程）
    # 1. 加载文档
    loader = LawLoader("./Law-Book")
    documents = loader.load()
    print(f"加载了 {len(documents)} 个文档")
    
    # 2. 分割文档
    splitter = LawSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = splitter.split_documents(documents)
    print(f"分割后共 {len(split_docs)} 个文本块")
    
    # 3. 导入向量库
    result = law_index(split_docs, show_progress=True)
    print(f"导入结果: {result}")
    
    # 示例 4: 获取 LLM 模型
    from langchain.callbacks import StreamingStdOutCallbackHandler
    
    llm = get_model(
        model="qwen-max",
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()]
    )
    
    # 使用 LLM
    response = llm.invoke("什么是民法典？")
    print(response.content)
"""
import os
from typing import List, Dict
from collections import defaultdict
import dashscope

from langchain.docstore.document import Document
from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings
from langchain_core.embeddings import Embeddings
from langchain.indexes import SQLRecordManager, index
from langchain.vectorstores import Chroma
from langchain.indexes._api import _batch
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.manager import Callbacks

class DashScopeEmbeddings(Embeddings):
    """阿里云 DashScope Embedding 模型"""
    
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-v2")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化"""
        # DashScope 单次最多支持 25 条，需要分批处理
        all_embeddings = []
        batch_size = 25

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            response = dashscope.TextEmbedding.call(
                model = self.model,
                input = batch_texts,
                api_key = self.api_key
            )
            if response.status_code == 200:
                batch_embeddings = [item["embedding"] for item in response.output["embeddings"]]
                all_embeddings.extend(batch_embeddings)
            else:
                raise Exception(f"DashScope Embedding 调用失败: {response.code} - {response.message}")
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """单条文本向量化"""
        return self.embed_documents([text])[0]


def get_embedding_model() -> DashScopeEmbeddings:
    """获取 Embedding 模型，使用 DashScope 原生 API"""
    return DashScopeEmbeddings()

def get_cached_embedder() -> CacheBackedEmbeddings:
    fs = LocalFileStore("./.cache/embeddings")
    underlying_embeddings = get_embedding_model()

    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings, fs, namespace=underlying_embeddings.model
    )
    return cached_embedder

def get_record_manager(namespace: str = "law") -> SQLRecordManager:
    return SQLRecordManager(
        f"chroma/{namespace}", db_url="sqlite:///law_record_manager_cache.sql"
    )

def get_vectorstore(collection_name: str = "law") -> Chroma:
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=get_cached_embedder(),
        collection_name=collection_name
    )
    return vectorstore

def clear_vectorstore(collection_name: str = "law") -> None:
    record_manager = get_record_manager(collection_name)
    vectorstore = get_vectorstore(collection_name)

    index([], record_manager, vectorstore, cleanup="full", source_id_key="source")

def get_model(
        model: str = None,
        streaming: bool = True,
        callbacks: Callbacks = None) -> ChatOpenAI:
    """获取 LLM 模型，支持 DashScope API"""
    model_name = model or os.getenv("MODEL_NAME", "qwen-plus")
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    
    return ChatOpenAI(
        model=model_name,
        streaming=streaming,
        callbacks=callbacks,
        openai_api_key=api_key,
        openai_api_base=base_url
    )


def law_index(docs: List[Document], show_progress: bool = True) -> Dict:
    info = defaultdict(int)

    record_manager = get_record_manager("law")
    vectorstore = get_vectorstore("law")

    pbar = None
    if (show_progress):
        from tqdm import tqdm
        pbar = tqdm(total=len(docs))
    
    for batch in _batch(100, docs):
        result = index(
            batch,
            record_manager,
            vectorstore,
            cleanup=None,
            # cleanup="full"
            source_id_key="source"
        )
        for k, v in result.items():
            info[k] += v
        if pbar:
            pbar.update(len(batch))
    if pbar:
        pbar.close()
    return dict(info)