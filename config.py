# coding: utf-8


class Config:
    LAW_BOOK_PATH = "./Law-Book"
    LAW_BOOK_CHUNK_SIZE = 100 # 每块切分的最大长度为100字符
    LAW_BOOK_CHUNK_OVERLAP = 20 # 每块切分时，前后块重叠20字符以防止语义割裂
    LAW_VS_COLLECTION_NAME = "law" # 法律向量数据库集合名称
    LAW_VS_SEARCH_K = 2 # 检索后最多返回2条相关内容

    WEB_VS_COLLECTION_NAME = "web" # 网络数据向量数据库集合名称(注意此处未使用网络向量数据库)
    WEB_VS_SEARCH_K = 2 # 检索后最多返回2条相关内容(实际上这边是直接调用DuckDuckGo搜索, 未存入ChromaDB)
    
    # 代理配置 (用于 DuckDuckGo 网页搜索，设置为 None 则不使用代理)
    WEB_PROXY = "http://127.0.0.1:7890"

    WEB_HOST = "0.0.0.0" # Gradio Web 服务监听所有网络接口（可被局域网访问）
    WEB_PORT = 7860 # Web UI 使用 7860 端口（Gradio 默认端口）
    WEB_USERNAME = "username"
    WEB_PASSWORD = "password"


config = Config() # 方便被其他模块导入使用 

#  导入示例: from config import config
#           print(config.LAW_BOOK_PATH)
