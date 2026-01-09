# coding: utf-8
"""管理员后台 - 独立的 Streamlit 前端"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.api_client import api_client
import pandas as pd
from streamlit_echarts import st_echarts

# 页面配置
st.set_page_config(
    page_title="法律AI助手 - 管理后台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={}
)

# 暗色主题
st.markdown("""
<style>
/* 隐藏默认元素 */
#MainMenu, footer, header, [data-testid="stHeader"], 
[data-testid="stToolbar"], .stDeployButton {display: none !important;}

/* 全局背景 */
.stApp {background-color: #212121; color: #ececec;}
.main .block-container {background: #212121; padding: 2rem;}

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
    background: #10a37f !important; 
    color: white !important;
    border: none !important; 
    border-radius: 8px !important;
    padding: 0.5rem 2rem !important;
}
.stButton button:hover {background: #0e8c6d !important;}

/* 卡片 */
div[data-testid="metric-container"] {
    background: #2a2a2a;
    border: 1px solid #3f3f3f;
    border-radius: 12px;
    padding: 1rem;
}

/* 表单 */
[data-testid="stForm"] {background: transparent !important; border: none !important;}

/* 滚动条 */
::-webkit-scrollbar {width: 6px;}
::-webkit-scrollbar-track {background: #212121;}
::-webkit-scrollbar-thumb {background: #424242; border-radius: 3px;}
</style>
""", unsafe_allow_html=True)


def init_admin_session():
    """初始化管理员 Session State"""
    if "admin_token" not in st.session_state:
        st.session_state.admin_token = None
    if "admin_user" not in st.session_state:
        st.session_state.admin_user = None


def is_admin_logged_in() -> bool:
    """检查管理员是否已登录"""
    return st.session_state.admin_token is not None


def render_admin_login():
    """管理员登录页面"""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding-top: 100px; margin-bottom: 60px;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📊</div>
            <h1 style="color: #ececec; font-size: 2.2rem; font-weight: 600;">管理员后台</h1>
            <p style="color: #8e8e8e; font-size: 1rem; margin-top: 8px;">法律AI助手 - 数据统计与分析</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("admin_login_form"):
            username = st.text_input("管理员账号", placeholder="请输入管理员用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            
            # 居中提交按钮
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submit = st.form_submit_button("登 录", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("请填写所有字段")
                else:
                    # 调用登录 API
                    result = api_client.login(username, password)
                    if "error" not in result:
                        # 验证是否为管理员
                        api_client.set_token(result["access_token"])
                        user_info = api_client.get_current_user()
                        
                        if "error" not in user_info and user_info.get("is_admin", False):
                            st.session_state.admin_token = result["access_token"]
                            st.session_state.admin_user = user_info
                            st.rerun()
                        else:
                            st.error("该账号不是管理员")
                            api_client.clear_token()
                    else:
                        st.error(result["error"])


def render_admin_dashboard():
    """管理员后台主界面"""
    # 顶部导航栏
    col1, col2, col3 = st.columns([2, 4, 1])
    with col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 2rem;">📊</span>
            <span style="font-size: 1.3rem; font-weight: 600;">管理后台</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("退出登录", key="logout_btn"):
            st.session_state.admin_token = None
            st.session_state.admin_user = None
            api_client.clear_token()
            st.rerun()
    
    st.markdown("<hr style='border-color: #2f2f2f; margin: 20px 0 30px 0;'>", unsafe_allow_html=True)
    
    # 获取统计数据
    result = api_client.get_admin_stats()
    if "error" in result:
        st.error(f"获取数据失败: {result['error']}")
        return
    
    # ========== 基础统计卡片 ==========
    st.markdown("<h3 style='color: #ececec; margin-bottom: 16px;'>📈 系统概览</h3>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 用户总数", result["total_users"])
    with col2:
        st.metric("💬 对话总数", result["total_conversations"])
    with col3:
        st.metric("📝 消息总数", result["total_messages"])
    with col4:
        # 计算今日新增用户
        user_growth = result.get("user_growth", [])
        today_growth = 0
        if len(user_growth) >= 2:
            today_growth = user_growth[-1]["count"] - user_growth[-2]["count"]
        st.metric("🆕 今日新增", today_growth)
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # ========== 用户增长趋势图 ==========
    st.markdown("<h3 style='color: #ececec; margin-bottom: 16px;'>📊 用户增长趋势（近30天）</h3>", unsafe_allow_html=True)
    user_growth = result.get("user_growth", [])
    if user_growth:
        df = pd.DataFrame(user_growth)
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%m-%d')
        
        # ECharts 折线图配置
        line_option = {
            "backgroundColor": "#212121",
            "tooltip": {
                "trigger": "axis",
                "backgroundColor": "rgba(50,50,50,0.9)",
                "borderColor": "#10a37f",
                "borderWidth": 1,
                "textStyle": {"color": "#ececec"}
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "top": "10%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "data": df['date'].tolist(),
                "axisLine": {"lineStyle": {"color": "#424242"}},
                "axisLabel": {"color": "#8e8e8e", "fontSize": 11}
            },
            "yAxis": {
                "type": "value",
                "axisLine": {"lineStyle": {"color": "#424242"}},
                "axisLabel": {"color": "#8e8e8e"},
                "splitLine": {"lineStyle": {"color": "#2f2f2f", "type": "dashed"}}
            },
            "series": [{
                "name": "用户数",
                "type": "line",
                "smooth": True,
                "data": df['count'].tolist(),
                "lineStyle": {"color": "#10a37f", "width": 3},
                "itemStyle": {"color": "#10a37f"},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(16,163,127,0.3)"},
                            {"offset": 1, "color": "rgba(16,163,127,0.05)"}
                        ]
                    }
                }
            }]
        }
        st_echarts(options=line_option, height="400px")
    else:
        st.info("暂无数据")
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # ========== 问题数量增长趋势图 ==========
    st.markdown("<h3 style='color: #ececec; margin-bottom: 16px;'>💬 问题数量增长趋势（近30天）</h3>", unsafe_allow_html=True)
    message_growth = result.get("message_growth", [])
    if message_growth:
        df_msg = pd.DataFrame(message_growth)
        df_msg['date'] = pd.to_datetime(df_msg['date']).dt.strftime('%m-%d')
        
        # ECharts 折线图配置（使用不同颜色）
        line_option_msg = {
            "backgroundColor": "#212121",
            "tooltip": {
                "trigger": "axis",
                "backgroundColor": "rgba(50,50,50,0.9)",
                "borderColor": "#1e90ff",
                "borderWidth": 1,
                "textStyle": {"color": "#ececec"}
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "top": "10%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
                "data": df_msg['date'].tolist(),
                "axisLine": {"lineStyle": {"color": "#424242"}},
                "axisLabel": {"color": "#8e8e8e", "fontSize": 11}
            },
            "yAxis": {
                "type": "value",
                "axisLine": {"lineStyle": {"color": "#424242"}},
                "axisLabel": {"color": "#8e8e8e"},
                "splitLine": {"lineStyle": {"color": "#2f2f2f", "type": "dashed"}}
            },
            "series": [{
                "name": "问题数",
                "type": "line",
                "smooth": True,
                "data": df_msg['count'].tolist(),
                "lineStyle": {"color": "#1e90ff", "width": 3},
                "itemStyle": {"color": "#1e90ff"},
                "areaStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(30,144,255,0.3)"},
                            {"offset": 1, "color": "rgba(30,144,255,0.05)"}
                        ]
                    }
                }
            }]
        }
        st_echarts(options=line_option_msg, height="400px")
    else:
        st.info("暂无数据")
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    # ========== 两列布局 ==========
    col_left, col_right = st.columns(2)
    
    # 左侧：高频问题 Top 10
    with col_left:
        st.markdown("<h3 style='color: #ececec; margin-bottom: 16px;'>🔥 高频问题 Top 10</h3>", unsafe_allow_html=True)
        top_questions = result.get("top_questions", [])
        
        if top_questions:
            # ECharts 横向柱状图配置
            questions = [item['question'][:30] + ('...' if len(item['question']) > 30 else '') for item in top_questions]
            counts = [item['count'] for item in top_questions]
            
            bar_option = {
                "backgroundColor": "#212121",
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {"type": "shadow"},
                    "backgroundColor": "rgba(50,50,50,0.9)",
                    "borderColor": "#10a37f",
                    "borderWidth": 1,
                    "textStyle": {"color": "#ececec"}
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "3%",
                    "top": "3%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "value",
                    "axisLine": {"lineStyle": {"color": "#424242"}},
                    "axisLabel": {"color": "#8e8e8e"},
                    "splitLine": {"lineStyle": {"color": "#2f2f2f", "type": "dashed"}}
                },
                "yAxis": {
                    "type": "category",
                    "data": questions[::-1],  # 反转顺序，让最热门的在顶部
                    "axisLine": {"lineStyle": {"color": "#424242"}},
                    "axisLabel": {"color": "#ececec", "fontSize": 11}
                },
                "series": [{
                    "name": "提问次数",
                    "type": "bar",
                    "data": counts[::-1],
                    "itemStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 1, "y2": 0,
                            "colorStops": [
                                {"offset": 0, "color": "#10a37f"},
                                {"offset": 1, "color": "#0e8c6d"}
                            ]
                        },
                        "borderRadius": [0, 5, 5, 0]
                    },
                    "label": {
                        "show": True,
                        "position": "right",
                        "formatter": "{c} 次",
                        "color": "#ececec",
                        "fontSize": 11
                    },
                    "barMaxWidth": 30
                }]
            }
            st_echarts(options=bar_option, height="420px")
        else:
            st.info("暂无数据")
    
    # 右侧：知识库分类统计
    with col_right:
        st.markdown("<h3 style='color: #ececec; margin-bottom: 16px;'>📚 问题分类统计</h3>", unsafe_allow_html=True)
        category_stats = result.get("category_stats", [])
        
        if category_stats:
            # ECharts 饼图配置
            pie_data = [{"value": item["count"], "name": item["category"]} for item in category_stats]
            
            pie_option = {
                "backgroundColor": "#212121",
                "tooltip": {
                    "trigger": "item",
                    "formatter": "{b}: {c} ({d}%)",
                    "backgroundColor": "rgba(50,50,50,0.9)",
                    "borderColor": "#10a37f",
                    "borderWidth": 1,
                    "textStyle": {"color": "#ececec"}
                },
                "legend": {
                    "orient": "vertical",
                    "right": "10",
                    "top": "center",
                    "textStyle": {"color": "#ececec", "fontSize": 12}
                },
                "series": [{
                    "name": "问题分类",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "center": ["35%", "50%"],
                    "avoidLabelOverlap": False,
                    "itemStyle": {
                        "borderRadius": 10,
                        "borderColor": "#212121",
                        "borderWidth": 2
                    },
                    "label": {
                        "show": True,
                        "position": "outside",
                        "formatter": "{b}\n{d}%",
                        "color": "#ececec",
                        "fontSize": 11
                    },
                    "emphasis": {
                        "label": {"show": True, "fontSize": 14, "fontWeight": "bold"}
                    },
                    "labelLine": {"show": True, "lineStyle": {"color": "#424242"}},
                    "data": pie_data,
                    "color": ["#10a37f", "#1e90ff", "#ff6b6b", "#ffd93d", "#a29bfe", "#fd79a8"]
                }]
            }
            st_echarts(options=pie_option, height="380px")
            
            # 详细数据
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            for item in category_stats:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 8px 0; 
                            border-bottom: 1px solid #2f2f2f;">
                    <span style="color: #ececec;">{item['category']}</span>
                    <span style="color: #8e8e8e;">{item['count']} 条 ({item['percentage']}%)</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂无数据")


def main():
    init_admin_session()
    
    # 设置 Token
    if st.session_state.admin_token:
        api_client.set_token(st.session_state.admin_token)
    
    if not is_admin_logged_in():
        render_admin_login()
    else:
        render_admin_dashboard()


if __name__ == "__main__":
    main()
