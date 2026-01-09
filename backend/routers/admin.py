# coding: utf-8
"""管理员 API 路由"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter, defaultdict
import re

from ..database import get_db, User, Conversation, Message, QuestionLog
from ..schemas import AdminStatsResponse, SuccessResponse
from ..auth import get_current_user

router = APIRouter(prefix="/admin", tags=["管理员"])


def require_admin(current_user: User = Depends(get_current_user)):
    """验证管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


# 法律分类关键词（基于Law-Book文件夹结构）
LAW_CATEGORIES = {
    "宪法": ["宪法", "宪政", "国家制度", "基本权利", "国家机构"],
    "宪法相关法": ["国旗", "国徽", "国歌", "国籍", "选举", "代表", "国防", "军人", "戒严", "反恐", "国家安全", 
                "监察", "法官", "检察官", "人民法院", "人民检察院", "立法", "民族区域自治"],
    "民法典": ["民法典", "人格权", "婚姻", "继承", "侵权责任"],
    "民法商法": ["合同", "债务", "借款", "担保", "物权", "买卖", "租赁", "公司", "企业", "破产", 
              "证券", "保险", "票据", "信托", "商标", "专利", "著作权", "股权", "法人"],
    "行政法": ["行政", "处罚", "许可", "强制", "复议", "公务员", "政府", "城市管理", 
            "土地管理", "环境保护", "食品安全", "药品管理"],
    "经济法": ["反垄断", "反不正当竞争", "消费者权益", "产品质量", "价格", "税收", 
            "银行", "金融", "审计", "统计", "预算"],
    "社会法": ["劳动", "工资", "辞退", "解雇", "工伤", "社保", "工会", "就业", "职业病",
            "教育", "科学技术", "医疗", "社会保险", "社会救助", "慈善"],
    "刑法": ["杀人", "盗窃", "抢劫", "诈骗", "故意伤害", "强奸", "绑架", "犯罪", "刑事", 
          "判刑", "死刑", "无期徒刑", "有期徒刑", "拘役", "罚金", "贪污", "贿赂"],
    "诉讼与非诉讼程序法": ["诉讼", "起诉", "上诉", "审判", "执行", "证据", "仲裁", "调解", 
                      "民事诉讼", "刑事诉讼", "行政诉讼", "公证", "律师", "法律援助"],
}

# 法律主题关键词（核心主题作为key，所有变体作为value列表）
LAW_THEME_KEYWORDS = {
    # 刑法类
    "故意杀人罪": ["杀人罪", "杀人", "故意杀人", "谋杀", "杀害"],
    "过失致人死亡罪": ["过失杀人", "过失致人死亡", "过失致死", "误杀"],
    "故意伤害罪": ["伤害罪", "伤害", "故意伤害", "打伤", "致伤"],
    "过失致人重伤罪": ["过失伤害", "过失致人重伤", "误伤"],
    "盗窃罪": ["盗窃", "偷窃", "偷盗", "窃取", "偷东西"],
    "抢劫罪": ["抢劫", "抢夺", "持械抢劫"],
    "诈骗罪": ["诈骗", "骗钱", "电信诈骗", "网络诈骗", "欺诈"],
    "强奸罪": ["强奸", "性侵"],
    "绑架罪": ["绑架", "劫持"],
    "交通肇事罪": ["交通肇事", "肇事", "车祸", "交通事故", "撞人", "撞车"],
    
    # 民事类
    "合同纠纷": ["合同", "违约", "合同违约", "合同纠纷", "毁约", "解除合同"],
    "债务纠纷": ["债务", "借款", "欠款", "借钱", "还钱", "欠债", "债权"],
    "离婚": ["离婚", "离异", "分居", "离婚诉讼", "离婚财产", "离婚协议"],
    "抚养权": ["抚养", "抚养权", "抚养费", "孩子抚养", "子女抚养"],
    "赡养费": ["赡养", "赡养费", "赡养义务", "养老"],
    "遗产继承": ["继承", "遗产", "遗产继承", "遗嘱", "财产继承"],
    "房屋买卖": ["买房", "卖房", "房屋买卖", "购房", "房产交易"],
    "租赁纠纷": ["租赁", "租房", "房租", "租金"],
    "侵权责任": ["侵权", "侵害", "名誉侵权", "肖像权"],
    
    # 劳动类
    "劳动合同": ["劳动合同", "劳动纠纷", "劳动争议"],
    "工伤赔偿": ["工伤", "工伤赔偿", "工作受伤"],
    "辞退": ["辞退", "解雇", "开除", "被辞退", "被开除", "裁员"],
    "加班费": ["加班", "加班费", "加班工资"],
    "工资": ["工资", "薪资", "薪水", "拖欠工资", "欠薪"],
    "社保": ["社保", "社会保险", "五险一金", "养老保险"],
    
    # 其他
    "行政处罚": ["行政处罚", "罚款", "行政拘留"],
    "行政诉讼": ["行政诉讼", "行政复议", "告政府"],
    "民事诉讼": ["起诉", "诉讼", "打官司", "上诉"],
}


def extract_question_theme(question: str) -> tuple:
    """提取问题的核心主题（基于关键词匹配+主题归一化）
    返回: (主题名称, 是否匹配到关键词)
    """
    # 保存原始问题用于兜底处理
    original = question
    
    # 清洗问题：转小写、去除标点和空格
    cleaned = re.sub(r'[？?！!，,。.、\s]+', '', question.lower())
    
    # 遍历所有主题，找到最匹配的
    best_match = None
    best_match_len = 0
    
    for theme, keywords in LAW_THEME_KEYWORDS.items():
        for keyword in keywords:
            keyword_cleaned = keyword.replace(" ", "").lower()
            if keyword_cleaned in cleaned:
                # 优先选择匹配长度最长的
                if len(keyword_cleaned) > best_match_len:
                    best_match = theme
                    best_match_len = len(keyword_cleaned)
    
    if best_match:
        return (best_match, True)  # 匹配到关键词
    
    # 兜底逻辑：如果没有匹配到任何关键词，提取问题核心词
    # 去除常见疑问词和无意义词
    for word in ["什么", "怎么", "如何", "怎样", "为什么", "是否", "可以", "能否", 
                 "多少", "几年", "几个月", "几天", "吗", "呢", "啊", "呀", "的", "了", "吗"]:
        cleaned = cleaned.replace(word, "")
    
    # 返回提取的主题（10-25个字符，避免太短或太长）
    if len(cleaned) > 25:
        return (cleaned[:25], False)
    elif len(cleaned) >= 4:  # 至少4个字符才有意义
        return (cleaned, False)
    else:
        # 如果清洗后太短，返回原始问题的前20个字符
        theme = original[:20] if len(original) > 20 else original
        return (theme, False)


def classify_question(question: str) -> str:
    """对问题进行法律分类（按优先级匹配，避免误分类）"""
    # 按顺序检查，优先匹配特征明显的类别
    # 1. 宪法（最优先，避免被其他类别误匹配）
    for keyword in LAW_CATEGORIES["宪法"]:
        if keyword in question:
            return "宪法"
    
    # 2. 刑法（特征明显）
    for keyword in LAW_CATEGORIES["刑法"]:
        if keyword in question:
            return "刑法"
    
    # 3. 诉讼与非诉讼程序法
    for keyword in LAW_CATEGORIES["诉讼与非诉讼程序法"]:
        if keyword in question:
            return "诉讼与非诉讼程序法"
    
    # 4. 民法典（包含婚姻继承等）
    for keyword in LAW_CATEGORIES["民法典"]:
        if keyword in question:
            return "民法典"
    
    # 5. 社会法（包含劳动、社保等）
    for keyword in LAW_CATEGORIES["社会法"]:
        if keyword in question:
            return "社会法"
    
    # 6. 民法商法（公司、合同等）
    for keyword in LAW_CATEGORIES["民法商法"]:
        if keyword in question:
            return "民法商法"
    
    # 7. 经济法
    for keyword in LAW_CATEGORIES["经济法"]:
        if keyword in question:
            return "经济法"
    
    # 8. 行政法
    for keyword in LAW_CATEGORIES["行政法"]:
        if keyword in question:
            return "行政法"
    
    # 9. 宪法相关法
    for keyword in LAW_CATEGORIES["宪法相关法"]:
        if keyword in question:
            return "宪法相关法"
    
    # 默认分类到民法商法（因为最常见）
    return "民法商法"


@router.get("/stats", response_model=AdminStatsResponse, summary="获取统计数据")
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """获取管理员统计数据"""
    
    # 基础统计
    total_users = db.query(User).count()
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    
    # 用户增长趋势（最近30天）
    user_growth = []
    for i in range(30, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        count = db.query(User).filter(
            func.date(User.created_at) <= date_str
        ).count()
        user_growth.append({"date": date_str, "count": count})
    
    # 问题数量增长趋势（最近30天，统计用户消息数）
    message_growth = []
    for i in range(30, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        count = db.query(Message).filter(
            Message.role == "user",
            func.date(Message.created_at) <= date_str
        ).count()
        message_growth.append({"date": date_str, "count": count})
    
    # 高频问题 Top 10（基于主题聚合，优化统计逻辑）
    user_messages = db.query(Message).filter(
        Message.role == "user"
    ).order_by(Message.created_at.desc()).limit(2000).all()  # 增加样本量到2000
    
    # 使用主题聚合相似问题，区分关键词匹配和兜底提取
    keyword_themes = defaultdict(lambda: {"count": 0, "examples": [], "category": ""})  # 关键词匹配的主题
    other_themes = defaultdict(lambda: {"count": 0, "examples": [], "category": ""})    # 兜底提取的主题
    
    for msg in user_messages:
        theme, is_keyword_match = extract_question_theme(msg.content)
        
        # 根据是否匹配关键词，放入不同的字典
        target_dict = keyword_themes if is_keyword_match else other_themes
        
        target_dict[theme]["count"] += 1
        # 保存示例问题（最多保存3个）
        if len(target_dict[theme]["examples"]) < 3:
            target_dict[theme]["examples"].append(msg.content)
        # 记录分类（只记录一次）
        if not target_dict[theme]["category"]:
            target_dict[theme]["category"] = classify_question(msg.content)
    
    # 优先展示关键词匹配的主题，按频率排序
    keyword_sorted = sorted(keyword_themes.items(), key=lambda x: x[1]["count"], reverse=True)
    
    # 如果关键词匹配的主题不足10个，用其他主题补充（但要求至少出现5次）
    if len(keyword_sorted) < 10:
        other_sorted = sorted(
            [(theme, data) for theme, data in other_themes.items() if data["count"] >= 5],
            key=lambda x: x[1]["count"], 
            reverse=True
        )
        # 补充到10个
        sorted_themes = keyword_sorted + other_sorted[:10 - len(keyword_sorted)]
    else:
        sorted_themes = keyword_sorted[:10]
    
    top_questions = []
    for theme, data in sorted_themes:
        # 显示格式：主题名 + 分类标签
        category_tag = f"[{data['category']}]" if data['category'] else ""
        display_text = f"{theme} {category_tag}"
        
        top_questions.append({
            "question": display_text,
            "count": data["count"]
        })
    
    # 知识库覆盖领域统计
    category_counter = Counter()
    for msg in user_messages:
        cat = classify_question(msg.content)
        category_counter[cat] += 1
    
    total_categorized = sum(category_counter.values()) or 1
    category_stats = [
        {
            "category": cat,
            "count": count,
            "percentage": round(count / total_categorized * 100, 1)
        }
        for cat, count in category_counter.most_common()
    ]
    
    return {
        "total_users": total_users,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "user_growth": user_growth,
        "message_growth": message_growth,
        "top_questions": top_questions,
        "category_stats": category_stats
    }


@router.post("/create-admin", response_model=SuccessResponse, summary="创建管理员账号")
async def create_admin_user(
    username: str = "admin",
    password: str = "admin123",
    db: Session = Depends(get_db)
):
    """创建管理员账号（仅用于初始化）"""
    from ..auth import get_password_hash, get_user_by_username
    
    existing = get_user_by_username(db, username)
    if existing:
        # 更新为管理员
        existing.is_admin = True
        db.commit()
        return {"success": True, "message": f"用户 {username} 已设置为管理员"}
    
    # 创建新管理员
    admin = User(
        username=username,
        hashed_password=get_password_hash(password),
        is_admin=True
    )
    db.add(admin)
    db.commit()
    return {"success": True, "message": f"管理员 {username} 创建成功"}
