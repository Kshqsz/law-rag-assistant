# coding: utf-8
"""
Streamlit 前端 - API 客户端封装
"""
import requests
from typing import Optional, List, Dict, Any
import streamlit as st

# API 基础 URL
API_BASE_URL = "http://localhost:8000/api"


class APIClient:
    """API 客户端"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    def set_token(self, token: str):
        """设置认证 Token"""
        self.token = token
    
    def clear_token(self):
        """清除 Token"""
        self.token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            if files:
                # 文件上传不需要 Content-Type
                headers.pop("Content-Type", None)
                response = requests.request(
                    method, url, headers=headers, files=files, timeout=120
                )
            else:
                response = requests.request(
                    method, url, headers=headers, json=data, timeout=120
                )
            
            if response.status_code == 401:
                return {"error": "认证失效，请重新登录", "status_code": 401}
            
            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", "请求失败")
                except:
                    error_detail = response.text or "请求失败"
                return {"error": error_detail, "status_code": response.status_code}
            
            return response.json()
            
        except requests.exceptions.ConnectionError:
            return {"error": "无法连接到服务器，请确保后端服务已启动"}
        except requests.exceptions.Timeout:
            return {"error": "请求超时，请稍后重试"}
        except Exception as e:
            return {"error": f"请求错误: {str(e)}"}
    
    # ==================== 认证相关 ====================
    
    def register(self, username: str, password: str) -> Dict:
        """用户注册"""
        return self._request("POST", "/auth/register", {
            "username": username,
            "password": password
        })
    
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        return self._request("POST", "/auth/login/json", {
            "username": username,
            "password": password
        })
    
    def get_current_user(self) -> Dict:
        """获取当前用户信息"""
        return self._request("GET", "/auth/me")
    
    # ==================== 对话相关 ====================
    
    def list_conversations(self) -> Dict:
        """获取对话列表"""
        return self._request("GET", "/conversations")
    
    def create_conversation(self, title: str = "新对话") -> Dict:
        """创建新对话"""
        return self._request("POST", "/conversations", {"title": title})
    
    def get_conversation(self, conversation_id: int) -> Dict:
        """获取对话详情"""
        return self._request("GET", f"/conversations/{conversation_id}")
    
    def update_conversation(self, conversation_id: int, title: str) -> Dict:
        """更新对话标题"""
        return self._request("PUT", f"/conversations/{conversation_id}", {"title": title})
    
    def delete_conversation(self, conversation_id: int) -> Dict:
        """删除对话"""
        return self._request("DELETE", f"/conversations/{conversation_id}")
    
    def list_messages(self, conversation_id: int) -> Dict:
        """获取对话消息列表"""
        return self._request("GET", f"/conversations/{conversation_id}/messages")
    
    def clear_messages(self, conversation_id: int) -> Dict:
        """清空对话消息"""
        return self._request("DELETE", f"/conversations/{conversation_id}/messages")
    
    # ==================== 聊天相关 ====================
    
    def chat(
        self, 
        message: str, 
        conversation_id: Optional[int] = None,
        use_document: Optional[int] = None
    ) -> Dict:
        """发送消息"""
        data = {"message": message}
        if conversation_id:
            data["conversation_id"] = conversation_id
        if use_document:
            data["use_document"] = use_document
        
        return self._request("POST", "/chat", data)
    
    def chat_stream(
        self, 
        message: str, 
        conversation_id: Optional[int] = None,
        use_document: Optional[int] = None
    ):
        """流式发送消息并获取回答"""
        import requests
        import json
        
        data = {"message": message}
        if conversation_id:
            data["conversation_id"] = conversation_id
        if use_document:
            data["use_document"] = use_document
        
        url = f"{self.base_url}/chat/stream"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(url, json=data, headers=headers, stream=True)
        
        if response.status_code != 200:
            yield {"error": f"请求失败: {response.status_code}"}
            return
        
        # 解析 SSE 流
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]  # 移除 "data: " 前缀
                    try:
                        chunk = json.loads(data_str)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
    
    def check_law_related(self, question: str) -> Dict:
        """检查问题是否与法律相关"""
        return self._request("GET", f"/chat/check-law?question={question}")
    
    # ==================== 文档相关 ====================
    
    def upload_document(self, file) -> Dict:
        """上传文档"""
        files = {"file": (file.name, file, file.type)}
        return self._request("POST", "/documents/upload", files=files)
    
    def list_documents(self) -> Dict:
        """获取文档列表"""
        return self._request("GET", "/documents")
    
    def get_document(self, document_id: int) -> Dict:
        """获取文档详情"""
        return self._request("GET", f"/documents/{document_id}")
    
    def get_document_content(self, document_id: int) -> Dict:
        """获取文档内容"""
        return self._request("GET", f"/documents/{document_id}/content")
    
    def delete_document(self, document_id: int) -> Dict:
        """删除文档"""
        return self._request("DELETE", f"/documents/{document_id}")
    
    # ==================== 收藏夹相关 ====================
    
    def add_favorite(self, message_id: int, question: str, answer: str) -> Dict:
        """添加收藏"""
        return self._request("POST", "/favorites", {
            "message_id": message_id,
            "question": question,
            "answer": answer
        })
    
    def list_favorites(self) -> Dict:
        """获取收藏列表"""
        return self._request("GET", "/favorites")
    
    def delete_favorite(self, favorite_id: int) -> Dict:
        """删除收藏"""
        return self._request("DELETE", f"/favorites/{favorite_id}")
    
    # ==================== 管理员相关 ====================
    
    def get_admin_stats(self) -> Dict:
        """获取管理员统计数据"""
        return self._request("GET", "/admin/stats")
    
    def create_admin_user(self, username: str = "admin", password: str = "admin123") -> Dict:
        """创建管理员账号"""
        return self._request("POST", f"/admin/create-admin?username={username}&password={password}")


# 创建全局客户端实例
api_client = APIClient()


def init_session_state():
    """初始化 Streamlit Session State"""
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None
    if "page" not in st.session_state:
        st.session_state.page = "chat"


def is_logged_in() -> bool:
    """检查是否已登录"""
    return st.session_state.token is not None


def set_login(token: str, user: Dict):
    """设置登录状态"""
    st.session_state.token = token
    st.session_state.user = user
    api_client.set_token(token)


def logout():
    """登出"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.current_conversation_id = None
    st.session_state.messages = []
    st.session_state.selected_document = None
    api_client.clear_token()
