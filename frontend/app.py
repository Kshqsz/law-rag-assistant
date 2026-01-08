# coding: utf-8
"""法律AI助手 - Streamlit 前端"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.api_client import api_client, init_session_state, is_logged_in
from frontend.components import (
    render_login_page, render_sidebar, render_chat_area, 
    render_favorites_page
)

# 页面配置
st.set_page_config(
    page_title="法律AI助手",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ChatGPT 黑白风格
st.markdown("""
<style>
/* 隐藏默认元素 */
#MainMenu, footer, header, [data-testid="stHeader"], 
[data-testid="stToolbar"], .stDeployButton {display: none !important;}

/* 全局背景 */
.stApp {background-color: #212121; color: #ececec;}
.main .block-container {background: #212121; max-width: 900px; padding: 1rem;}

/* 侧边栏 */
[data-testid="stSidebar"] {background: #171717; border-right: 1px solid #2f2f2f;}
[data-testid="stSidebar"] > div:first-child {background: #171717;}

/* 输入框 */
.stTextInput input {
    background: #2f2f2f !important; 
    border: 1px solid #424242 !important;
    border-radius: 8px !important; 
    color: #ececec !important;
}
.stTextInput input:focus {border-color: #10a37f !important;}

/* 按钮 */
.stButton button {
    background: #2f2f2f !important; 
    color: #ececec !important;
    border: 1px solid #424242 !important; 
    border-radius: 8px !important;
}
.stButton button:hover {background: #3f3f3f !important;}
.stButton button[kind="primary"], 
.stButton button[data-testid="baseButton-primary"] {
    background: #10a37f !important; 
    border: none !important; 
    color: white !important;
}

/* 聊天 */
[data-testid="stChatInput"] {
    background: #2f2f2f !important;
    border: 1px solid #424242 !important;
    border-radius: 24px !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #ececec !important;
}

/* Tab */
.stTabs [data-baseweb="tab-list"] {gap: 8px; background: transparent;}
.stTabs [data-baseweb="tab"] {background: #2f2f2f; border-radius: 8px; color: #ececec !important;}
.stTabs [aria-selected="true"] {background: #10a37f !important;}

/* 表单 */
[data-testid="stForm"] {background: transparent !important; border: none !important;}

/* 展开器 */
.streamlit-expanderHeader {background: #2f2f2f !important; border-radius: 8px !important;}
.streamlit-expanderContent {background: #1a1a1a !important; border: 1px solid #2f2f2f !important;}

/* 文件上传 */
[data-testid="stFileUploader"] {background: #2f2f2f !important; border: 1px dashed #424242 !important; border-radius: 8px !important;}

/* 提示 */
.stAlert {background: #2f2f2f !important; border: 1px solid #424242 !important; border-radius: 8px !important;}

/* 滚动条 */
::-webkit-scrollbar {width: 6px;}
::-webkit-scrollbar-track {background: #212121;}
::-webkit-scrollbar-thumb {background: #424242; border-radius: 3px;}
</style>
""", unsafe_allow_html=True)

def main():
    init_session_state()
    
    if st.session_state.token:
        api_client.set_token(st.session_state.token)
    
    if not is_logged_in():
        render_login_page()
    else:
        render_sidebar()
        
        # 根据页面状态渲染不同内容
        page = st.session_state.get("page", "chat")
        if page == "favorites":
            render_favorites_page()
        else:
            render_chat_area()

if __name__ == "__main__":
    main()
