# coding: utf-8
"""
Streamlit 前端 - ChatGPT 风格组件
"""
import streamlit as st
from .api_client import api_client, set_login, logout
from datetime import datetime
from io import BytesIO
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def export_conversation_to_pdf(messages):
    """导出对话为PDF"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    import re
    
    def clean_markdown(text):
        """清理markdown格式，转换为纯文本"""
        # 移除代码块标记
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 移除粗体和斜体标记
        text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'___([^_]+)___', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # 移除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 移除链接标记 [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # 移除图片标记
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
        
        # 转换列表标记
        text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 移除引用标记
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        
        # 移除分隔线
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
        
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # 尝试注册中文字体
    try:
        # macOS 系统字体
        pdfmetrics.registerFont(TTFont('SimSun', '/System/Library/Fonts/STHeiti Light.ttc'))
        font_name = 'SimSun'
    except:
        try:
            # 尝试其他macOS中文字体
            pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
            font_name = 'PingFang'
        except:
            font_name = 'Helvetica'
    
    # 创建样式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor='#10a37f'
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        spaceAfter=10,
        leftIndent=10,
        textColor='#000000'
    )
    
    answer_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        spaceAfter=20,
        leftIndent=10,
        textColor='#333333'
    )
    
    time_style = ParagraphStyle(
        'Time',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        alignment=TA_CENTER,
        textColor='#666666',
        spaceAfter=20
    )
    
    # 添加标题
    story.append(Paragraph("法律AI对话记录", title_style))
    story.append(Paragraph(f"导出时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}", time_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 添加对话内容
    qa_count = 0
    for idx, msg in enumerate(messages):
        if msg["role"] == "user":
            qa_count += 1
            # 清理markdown格式
            content = clean_markdown(msg["content"])
            # 转义XML特殊字符
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            story.append(Paragraph(f"<b>【问题 {qa_count}】</b>", question_style))
            story.append(Paragraph(content, question_style))
            story.append(Spacer(1, 0.15*inch))
        else:
            # 清理markdown格式
            content = clean_markdown(msg["content"])
            # 转义XML特殊字符
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # 处理换行
            content = content.replace('\n', '<br/>')
            
            story.append(Paragraph(f"<b>【回答 {qa_count}】</b>", answer_style))
            story.append(Paragraph(content, answer_style))
            story.append(Spacer(1, 0.25*inch))
    
    # 生成PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def render_login_page():
    """登录/注册页面"""
    # 检查并显示退出登录消息
    if st.session_state.get('show_logout_success'):
        st.toast("✅ 已退出登录", icon="👋")
        del st.session_state.show_logout_success
    
    # 居中样式
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding-top: 60px;
    }
    .login-header {
        text-align: center;
        margin-bottom: 40px;
    }
    .login-logo {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    .login-title {
        color: #ececec;
        font-size: 2rem;
        font-weight: 600;
    }
    .login-subtitle {
        color: #8e8e8e;
        font-size: 1rem;
    }
    /* 输入框全宽显示 */
    .stTextInput {
        width: 100% !important;
    }
    .stTextInput > div {
        width: 100% !important;
    }
    .stTextInput input {
        width: 100% !important;
    }
    /* 移除tabs内部的额外padding */
    [data-testid="stTabs"] [data-testid="stVerticalBlock"] {
        padding: 0 !important;
    }
    /* 强制按钮居中 - 更强的选择器 */
    div[data-testid="stForm"] button[kind="primary"] {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    /* 确保按钮容器也居中 */
    div[data-testid="stForm"] div[data-testid="column"] {
        display: flex !important;
        justify-content: center !important;
    }
    /* 让 tabs 居中显示 */
    [data-testid="stTabs"] {
        display: flex !important;
        justify-content: center !important;
    }
    [data-testid="stTabs"] > div {
        max-width: 100% !important;
        justify-content: center !important;
    }
    [data-testid="stTabs"] [role="tablist"] {
        justify-content: center !important;
    }
    /* 增大 tab 按钮的字体和尺寸 */
    [data-testid="stTabs"] button[role="tab"] {
        font-size: 1.2rem !important;
        padding: 12px 32px !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("""
        <div class="login-header">
            <div class="login-logo">⚖️</div>
            <h1 class="login-title">法律AI助手</h1>
            <p class="login-subtitle">基于 RAG 技术的智能法律问答系统</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("用户名", placeholder="请输入用户名")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    login_btn = st.form_submit_button("登 录", use_container_width=True, type="primary")
                
                if login_btn:
                    if username and password:
                        result = api_client.login(username, password)
                        if "error" not in result:
                            api_client.set_token(result["access_token"])
                            user_info = api_client.get_current_user()
                            if "error" not in user_info:
                                set_login(result["access_token"], user_info)
                                # 设置标志在rerun后显示toast
                                st.session_state.show_login_success = user_info.get('username', '用户')
                                st.rerun()
                        else:
                            st.error(result["error"])
                    else:
                        st.error("请填写用户名和密码")
        
        with tab2:
            with st.form("register_form"):
                reg_username = st.text_input("用户名", placeholder="3-50个字符", key="reg_u")
                reg_password = st.text_input("密码", type="password", placeholder="至少6位", key="reg_p")
                reg_password2 = st.text_input("确认密码", type="password", placeholder="再次输入", key="reg_p2")
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    reg_btn = st.form_submit_button("注 册", use_container_width=True, type="primary")
                
                if reg_btn:
                    if not all([reg_username, reg_password, reg_password2]):
                        st.error("请填写所有字段")
                    elif reg_password != reg_password2:
                        st.error("两次密码不一致")
                    elif len(reg_password) < 6:
                        st.error("密码至少6位")
                    else:
                        result = api_client.register(reg_username, reg_password)
                        if "error" not in result:
                            st.success("✅ 注册成功！请切换到登录标签页登录")
                        else:
                            st.error(result["error"])


def render_sidebar():
    """侧边栏"""
    # 检查并显示登录成功消息
    if st.session_state.get('show_login_success'):
        username = st.session_state.show_login_success
        st.toast(f"✅ 欢迎回来，{username}！", icon="👋")
        del st.session_state.show_login_success
    
    with st.sidebar:
        # 顶部 Logo
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; padding: 16px 0; border-bottom: 1px solid #2f2f2f;">
            <span style="font-size: 1.5rem;">⚖️</span>
            <span style="font-size: 1.1rem; font-weight: 600;">法律AI助手</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 新建对话
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
        if st.button("➕ 新建对话", use_container_width=True, type="primary"):
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
            st.session_state.uploaded_file_content = None
            st.session_state.uploaded_file_name = None
            st.session_state.uploaded_document_id = None
            st.session_state.page = "chat"
            st.rerun()
        
        # 导航菜单
        st.markdown("<p style='color: #6e6e6e; font-size: 0.75rem; margin: 16px 0 8px 0;'>功能</p>", unsafe_allow_html=True)
        
        if st.button("💬 对话", key="nav_chat", use_container_width=True,
                    type="primary" if st.session_state.get("page", "chat") == "chat" else "secondary"):
            st.session_state.page = "chat"
            st.rerun()
        
        if st.button("⭐ 收藏夹", key="nav_fav", use_container_width=True,
                    type="primary" if st.session_state.get("page") == "favorites" else "secondary"):
            st.session_state.page = "favorites"
            st.rerun()
        
        # 历史对话
        st.markdown("<p style='color: #6e6e6e; font-size: 0.75rem; margin: 16px 0 8px 0;'>历史对话</p>", unsafe_allow_html=True)
        
        result = api_client.list_conversations()
        if "error" not in result:
            conversations = result.get("conversations", [])
            if not conversations:
                st.markdown("<p style='color: #4e4e4e; font-size: 0.85rem;'>暂无对话</p>", unsafe_allow_html=True)
            else:
                # 删除确认弹窗
                @st.dialog("确认删除", width="small")
                def show_delete_confirm(conv_id):
                    st.markdown("""
                    <div style="color: #ff6666; margin-bottom: 20px; text-align: center;">
                        <div style="font-size: 3rem; margin-bottom: 10px;">⚠️</div>
                        <p style="font-size: 1.1rem;">确认删除此对话？</p>
                        <p style="color: #999; font-size: 0.9rem;">此操作无法撤销</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ 确认删除", key="confirm_del_dialog", use_container_width=True, type="primary"):
                            api_client.delete_conversation(conv_id)
                            if st.session_state.current_conversation_id == conv_id:
                                st.session_state.current_conversation_id = None
                                st.session_state.messages = []
                            st.session_state.show_delete_success = True
                            st.rerun()
                    with col2:
                        if st.button("✕ 取消", key="cancel_del_dialog", use_container_width=True):
                            st.rerun()
                
                for conv in conversations[:10]:  # 限制显示10条
                    is_current = st.session_state.current_conversation_id == conv["id"]
                    title = conv['title'][:14] + "..." if len(conv['title']) > 14 else conv['title']
                    
                    cols = st.columns([5, 1])
                    with cols[0]:
                        if st.button(title, key=f"c_{conv['id']}", use_container_width=True,
                                    type="primary" if is_current else "secondary"):
                            st.session_state.current_conversation_id = conv["id"]
                            st.session_state.page = "chat"
                            _load_messages(conv["id"])
                            st.rerun()
                    with cols[1]:
                        # 使用popover在右侧弹出菜单
                        with st.popover("⋮", use_container_width=True):
                            # 导出PDF按钮
                            temp_messages = _load_messages_for_export(conv["id"])
                            if temp_messages:
                                pdf_buffer = export_conversation_to_pdf(temp_messages)
                                if pdf_buffer:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    st.download_button(
                                        label="📄 导出PDF",
                                        data=pdf_buffer,
                                        file_name=f"法律对话_{conv['title'][:10]}_{timestamp}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_pdf_{conv['id']}",
                                        use_container_width=True
                                    )
                            
                            # 删除按钮
                            if st.button("🗑️ 删除对话", key=f"del_{conv['id']}", use_container_width=True):
                                show_delete_confirm(conv["id"])
        
        # ========== 底部用户区域 ==========
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] > div:first-child {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        .user-area {
            margin-top: auto !important;
            padding-top: 20px;
            border-top: 1px solid #2f2f2f;
        }
        /* 隐藏popover的箭头 */
        [data-testid="stPopover"] > div > div:first-child::before,
        [data-testid="stPopover"] > div > div:first-child::after {
            display: none !important;
        }
        /* 调整popover位置，使其更靠右 */
        [data-testid="stPopover"] {
            position: relative !important;
        }
        [data-testid="stPopover"] > div {
            left: auto !important;
            right: 0 !important;
        }
        /* popover内容样式优化 */
        [data-testid="stPopover"] [data-testid="stVerticalBlock"] {
            padding: 4px !important;
            gap: 4px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 填充空间
        st.markdown("<div style='flex-grow: 1; min-height: 50px;'></div>", unsafe_allow_html=True)
        
        # 用户区域
        st.markdown("<div class='user-area'></div>", unsafe_allow_html=True)
        
        # 初始化菜单状态
        if "user_menu_open" not in st.session_state:
            st.session_state.user_menu_open = False
        if "logout_confirm" not in st.session_state:
            st.session_state.logout_confirm = False
        if "delete_confirm_conv_id" not in st.session_state:
            st.session_state.delete_confirm_conv_id = None
        
        # 展开的菜单（在用户按钮上方）
        if st.session_state.user_menu_open:
            # 检查是否显示退出确认
            if st.session_state.get("logout_confirm", False):
                st.markdown("""
                <div style="background: #2a2a2a; border: 1px solid #ff4444; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <p style="color: #ff6666; font-size: 0.9rem; margin: 0;">⚠️ 确认退出登录？</p>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ 确认", key="confirm_logout", use_container_width=True, type="primary"):
                        st.session_state.show_logout_success = True
                        logout()
                        st.session_state.user_menu_open = False
                        st.session_state.logout_confirm = False
                        st.rerun()
                with col2:
                    if st.button("✕ 取消", key="cancel_logout", use_container_width=True):
                        st.session_state.logout_confirm = False
                        st.rerun()
            else:
                st.markdown("""
                <div style="background: #2a2a2a; border-radius: 8px; padding: 4px; margin-bottom: 8px;">
                </div>
                """, unsafe_allow_html=True)
                if st.button("↪️ 退出登录", key="logout_btn", use_container_width=True):
                    st.session_state.logout_confirm = True
                    st.rerun()
        
        # 用户按钮
        username = st.session_state.user.get('username', '用户')
        if st.button(f"👤 {username}", key="user_btn", use_container_width=True):
            st.session_state.user_menu_open = not st.session_state.user_menu_open
            st.rerun()


def _load_messages(conversation_id: int):
    """加载对话消息"""
    result = api_client.list_messages(conversation_id)
    if "error" not in result:
        st.session_state.messages = [
            {"role": m["role"], "content": m["content"], "id": m.get("id"),
             "law_context": m.get("law_context"), "web_context": m.get("web_context")}
            for m in result.get("messages", [])
        ]


def _load_messages_for_export(conversation_id: int):
    """加载对话消息用于导出（不修改session_state）"""
    result = api_client.list_messages(conversation_id)
    if "error" not in result:
        return [
            {"role": m["role"], "content": m["content"], "id": m.get("id"),
             "law_context": m.get("law_context"), "web_context": m.get("web_context")}
            for m in result.get("messages", [])
        ]
    return None


def _send_question(prompt: str):
    """发送问题并获取回答（流式输出）"""
    # 构建显示消息和实际问题
    display_msg = prompt
    actual_question = prompt
    use_document_id = None
    
    # 如果有上传的文档，将文档内容和问题组合
    if st.session_state.get("uploaded_file_content"):
        display_msg = f"📎 [{st.session_state.uploaded_file_name}]\n\n{prompt}"
        use_document_id = st.session_state.get("uploaded_document_id")
        # 将文档内容和问题组合，让检索和生成都能看到
        doc_content = st.session_state.uploaded_file_content[:3000]
        actual_question = f"""基于以下文档内容回答问题：

【文档内容】
{doc_content}

【问题】
{prompt}

请综合文档内容、法律条文和网络信息给出专业建议。"""
    
    # 添加用户消息到列表
    st.session_state.messages.append({"role": "user", "content": display_msg})
    
    # 显示用户消息
    with st.chat_message("user", avatar="👤"):
        st.markdown(display_msg)
    
    # 调用 API 获取回答（流式）
    with st.chat_message("assistant", avatar="⚖️"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 调用流式 API
            result = api_client.chat_stream(
                message=actual_question,
                conversation_id=st.session_state.current_conversation_id,
                use_document=use_document_id
            )
            
            # 流式显示回答
            for chunk in result:
                if "error" in chunk:
                    st.error(chunk["error"])
                    return False
                
                if "token" in chunk:
                    full_response += chunk["token"]
                    message_placeholder.markdown(full_response + "▌")
                
                if "done" in chunk and chunk["done"]:
                    # 完成流式输出
                    message_placeholder.markdown(full_response)
                    
                    # 获取最终数据
                    conv_id = chunk.get("conversation_id")
                    msg_id = chunk.get("message_id")
                    law_ctx = chunk.get("law_context", "")
                    web_ctx = chunk.get("web_context", "")
                    
                    # 显示法律依据和网络来源
                    if law_ctx:
                        with st.expander("📚 法律依据"):
                            st.markdown(law_ctx)
                    if web_ctx:
                        with st.expander("🌐 网络来源"):
                            st.markdown(web_ctx)
                    
                    # 保存到 session
                    st.session_state.current_conversation_id = conv_id
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "id": msg_id,
                        "law_context": law_ctx,
                        "web_context": web_ctx
                    })
                    return True
        
        except Exception as e:
            st.error(f"请求失败: {str(e)}")
            return False
    
    return False


def _read_file_content(uploaded_file) -> tuple:
    """读取上传的文件内容，支持多种编码和PDF"""
    filename = uploaded_file.name
    file_bytes = uploaded_file.read()
    
    # 尝试PDF
    if filename.lower().endswith('.pdf'):
        try:
            import PyPDF2
            from io import BytesIO
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts), None
        except Exception as e:
            return None, f"PDF 读取失败: {str(e)}"
    
    # 文本文件 - 尝试多种编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
    for enc in encodings:
        try:
            return file_bytes.decode(enc), None
        except:
            continue
    
    return None, "无法识别文件编码，请使用 UTF-8 或 GBK 编码的文本文件"


def render_chat_area():
    """聊天区域"""
    # 检查并显示文件上传和删除成功消息
    if st.session_state.get('show_upload_success'):
        filename = st.session_state.show_upload_success
        st.toast(f"✅ 文件已上传: {filename}", icon="📎")
        del st.session_state.show_upload_success
    
    if st.session_state.get('show_delete_success'):
        st.toast("✅ 对话已删除", icon="🗑️")
        del st.session_state.show_delete_success
    
    # 初始化
    if "uploaded_file_content" not in st.session_state:
        st.session_state.uploaded_file_content = None
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None
    
    # 欢迎界面或消息列表
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; padding: 100px 20px;">
            <div style="font-size: 3rem; margin-bottom: 20px;">⚖️</div>
            <h2 style="color: #ececec; font-weight: 500;">有什么法律问题可以帮您？</h2>
            <p style="color: #8e8e8e;">您可以直接提问，或点击下方示例开始</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 示例问题 - 单列显示
        examples = [("故意杀人罪会判几年？", "🔍"), ("合同违约如何处理？", "📝"),
                   ("离婚财产如何分割？", "👨‍👩‍👧"), ("被公司辞退怎么赔偿？", "💼")]
        cols = st.columns([1, 2, 1])  # 左边距-内容-右边距
        with cols[1]:
            for i, (q, icon) in enumerate(examples):
                if st.button(f"{icon} {q}", key=f"ex_{i}", use_container_width=True):
                    # 使用辅助函数发送问题
                    _send_question(q)
                    st.rerun()
    else:
        # 显示消息
        for idx, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
                st.markdown(msg["content"])
                
                if msg["role"] == "assistant":
                    # 显示法律依据和网络来源
                    if msg.get("law_context"):
                        with st.expander("📚 法律依据"):
                            st.markdown(msg["law_context"])
                    if msg.get("web_context"):
                        with st.expander("🌐 网络来源"):
                            st.markdown(msg["web_context"])
                    
                    # 收藏按钮
                    if idx > 0:  # 确保有对应的用户问题
                        user_msg = st.session_state.messages[idx - 1]
                        if user_msg["role"] == "user":
                            cols = st.columns([8, 1])
                            with cols[1]:
                                if st.button("⭐", key=f"fav_{idx}", help="收藏"):
                                    result = api_client.add_favorite(
                                        message_id=msg.get("id", 0),
                                        question=user_msg["content"],
                                        answer=msg["content"]
                                    )
                                    if "error" not in result:
                                        st.toast("✅ 已添加到收藏夹！", icon="⭐")
                                        st.rerun()  # 刷新页面
                                    else:
                                        st.toast(result.get("error", "收藏失败"), icon="❌")
    
    # ========== 输入区域：+ 按钮集成在输入框内 ==========
    st.markdown("""
    <style>
    /* 将文件上传按钮嵌入到 chat input 左侧 */
    [data-testid="stChatInput"] {
        position: relative;
    }
    [data-testid="stChatInput"] > div {
        position: relative;
        display: flex;
        align-items: center;
    }
    /* 上传按钮样式 */
    .upload-btn-wrapper {
        position: absolute;
        left: 8px;
        z-index: 100;
        display: flex;
        align-items: center;
    }
    .upload-btn-wrapper button {
        background: transparent !important;
        border: none !important;
        padding: 4px 8px !important;
        font-size: 1.2rem;
        cursor: pointer;
        color: #8e8e8e !important;
        min-width: 32px !important;
        height: 32px !important;
    }
    .upload-btn-wrapper button:hover {
        color: #ececec !important;
        background: #3f3f3f !important;
        border-radius: 6px !important;
    }
    /* 调整输入框内边距以留出按钮空间 */
    [data-testid="stChatInput"] textarea {
        padding-left: 48px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 显示已上传文件
    if st.session_state.uploaded_file_content:
        col1, col2 = st.columns([8, 1])
        with col1:
            st.info(f"📎 已上传: {st.session_state.uploaded_file_name}")
        with col2:
            if st.button("✕", key="rm_file", help="移除文件"):
                st.session_state.uploaded_file_content = None
                st.session_state.uploaded_file_name = None
                st.session_state.uploaded_document_id = None
                st.rerun()
    
    # 上传按钮（使用 container 和 columns 定位到输入框左侧）
    col1, col2 = st.columns([1, 20])
    with col1:
        if st.button("➕", key="upload_btn", help="上传文件"):
            st.session_state.show_upload_dialog = not st.session_state.get("show_upload_dialog", False)
            st.rerun()
    
    # 文件上传对话框
    if st.session_state.get("show_upload_dialog", False):
        uploaded = st.file_uploader(
            "选择文件", 
            type=["txt", "md", "pdf"],
            label_visibility="collapsed",
            key="file_uploader"
        )
        if uploaded:
            content, error = _read_file_content(uploaded)
            if error:
                st.error(error)
            else:
                # 上传文件到后端
                with st.spinner("正在上传文件..."):
                    result = api_client.upload_document(uploaded)
                    if "error" in result:
                        st.error(f"文件上传失败: {result['error']}")
                    else:
                        # API直接返回 document 对象
                        st.session_state.uploaded_file_content = content
                        st.session_state.uploaded_file_name = uploaded.name
                        st.session_state.uploaded_document_id = result.get("id")
                        st.session_state.show_upload_dialog = False
                        st.session_state.show_upload_success = uploaded.name
                        st.rerun()
    
    # 聊天输入
    if prompt := st.chat_input("询问法律问题..."):
        # 使用辅助函数发送问题
        _send_question(prompt)
        
        # 清除上传的文件
        st.session_state.uploaded_file_content = None
        st.session_state.uploaded_file_name = None
        st.session_state.uploaded_document_id = None
        st.rerun()


def render_favorites_page():
    """收藏夹页面"""
    st.markdown("""
    <h2 style="color: #ececec; margin-bottom: 20px;">⭐ 我的收藏</h2>
    """, unsafe_allow_html=True)
    
    result = api_client.list_favorites()
    if "error" in result:
        st.error(result["error"])
        return
    
    favorites = result.get("favorites", [])
    if not favorites:
        st.markdown("""
        <div style="text-align: center; padding: 60px; color: #8e8e8e;">
            <div style="font-size: 3rem; margin-bottom: 16px;">⭐</div>
            <p>暂无收藏内容</p>
            <p style="font-size: 0.85rem;">在对话中点击 ⭐ 按钮收藏问答</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 弹窗显示收藏详情
    @st.dialog("收藏详情", width="large")
    def show_favorite_detail(fav):
        st.markdown(f"""
        <div style="color: #10a37f; font-size: 0.9rem; margin-bottom: 16px;">
            📅 {fav['created_at'][:19].replace('T', ' ')}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 问题")
        st.markdown(f"""
        <div style="background: #2a2a2a; border-radius: 8px; padding: 16px; margin-bottom: 20px; color: #ececec;">
            {fav['question']}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 回答")
        st.markdown(f"""
        <div style="background: #2a2a2a; border-radius: 8px; padding: 16px; color: #b0b0b0; white-space: pre-wrap; max-height: 500px; overflow-y: auto;">
            {fav['answer']}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("关闭", use_container_width=True):
            st.rerun()
    
    # 显示收藏列表
    for fav in favorites:
        with st.container():
            st.markdown(f"""
            <div style="background: #2a2a2a; border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                <div style="color: #10a37f; font-size: 0.85rem; margin-bottom: 8px;">
                    📅 {fav['created_at'][:10]}
                </div>
                <div style="color: #ececec; font-weight: 500; margin-bottom: 12px;">
                    Q: {fav['question'][:100]}{'...' if len(fav['question']) > 100 else ''}
                </div>
                <div style="color: #b0b0b0; font-size: 0.9rem;">
                    A: {fav['answer'][:200]}{'...' if len(fav['answer']) > 200 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 按钮行
            col1, col2, col3 = st.columns([7, 1, 1])
            with col2:
                if st.button("👁️", key=f"view_fav_{fav['id']}", help="查看详情"):
                    show_favorite_detail(fav)
            with col3:
                if st.button("🗑️", key=f"del_fav_{fav['id']}", help="删除收藏"):
                    result = api_client.delete_favorite(fav['id'])
                    if "error" not in result:
                        st.toast("✅ 已从收藏夹移除", icon="🗑️")
                    st.rerun()


def render_welcome():
    """兼容接口"""
    pass
