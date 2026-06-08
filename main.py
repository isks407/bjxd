# ============================================================
#  驼灵智能体大赛 - 「智投未来」金融投资赛道
#  A股智能风控投顾智能体
#  代码文件：main.py
#  开发工具：Gradio + Python
# ============================================================

import os

# 必须在 import gradio 之前清除代理（否则 gradio 内 requests 会走代理导致 share 隧道失败）
for _proxy_var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(_proxy_var, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# 强制无缓冲输出，确保启动日志实时可见
os.environ["PYTHONUNBUFFERED"] = "1"

import gradio as gr
import re
import json
from datetime import datetime

# ============================================================
#  全局配置
# ============================================================

# 数据存储目录
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 历史记录文件路径
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# ============================================================
#  自定义Gradio主题配色（答辩投屏优化）
# ============================================================

CUSTOM_THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Noto Sans SC"),
).set(
    # 全局背景
    body_background_fill="linear-gradient(180deg, #eef2ff 0%, #f8fafc 55%, #e8edf7 100%)",
    body_background_fill_dark="linear-gradient(180deg, #1e1b4b 0%, #0f172a 55%, #1e1b4b 100%)",
    # 卡片/区块背景
    block_background_fill="#ffffff",
    block_background_fill_dark="#1e293b",
    block_border_width="1px",
    block_border_color="#e2e8f0",
    block_border_color_dark="#334155",
    block_shadow="0 4px 24px rgba(79, 70, 229, 0.08)",
    # 标题
    block_title_text_color="#1e293b",
    block_title_text_color_dark="#e2e8f0",
    # 按钮 - 主按钮
    button_primary_background_fill="linear-gradient(135deg, #4f46e5, #7c3aed)",
    button_primary_background_fill_hover="linear-gradient(135deg, #4338ca, #6d28d9)",
    button_primary_text_color="#ffffff",
    button_primary_border_color="transparent",
    button_primary_shadow="0 4px 14px rgba(79, 70, 229, 0.35)",
    # 按钮 - 次要按钮
    button_secondary_background_fill="#ffffff",
    button_secondary_border_color="#e2e8f0",
    # 按钮 - 圆角尺寸
    button_large_radius="12px",
    button_medium_radius="10px",
    button_small_radius="8px",
    # 输入框
    input_background_fill="#f8fafc",
    input_border_color="#e2e8f0",
    input_shadow="0 1px 3px rgba(0,0,0,0.04)",
    input_radius="10px",
    # 区块圆角
    block_radius="16px",
    container_radius="16px",
    # 间距
    block_padding="24px",
    # 字体
    body_text_color="#334155",
    body_text_color_dark="#cbd5e1",
    body_text_size="16px",
    # 表格
    table_border_color="#e2e8f0",
    table_even_background_fill="#f8fafc",
)

# ============================================================
#  全局自定义CSS样式（答辩投屏优化）
# ============================================================

CUSTOM_CSS = """
/* ===== 全局排版 ===== */
.module-container {
    margin-bottom: 12px;
}

/* ===== 大标题样式 ===== */
.main-title {
    text-align: center;
    padding: 20px 0 8px;
}
.main-title h1 {
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.03em;
}
.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 1rem;
    margin-bottom: 16px;
}

/* ===== 输入框增强 ===== */
.input-textbox textarea {
    font-size: 16px !important;
    line-height: 1.8 !important;
    border: 2px solid #e2e8f0 !important;
    transition: border-color 0.3s ease !important;
}
.input-textbox textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
}

/* ===== 解析按钮 ===== */
.parse-button button {
    font-size: 18px !important;
    font-weight: 600 !important;
    padding: 12px 32px !important;
    letter-spacing: 0.05em;
    transition: all 0.3s ease !important;
}
.parse-button button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4) !important;
}

/* ===== 警告信息 ===== */
.warning-markdown {
    border: 2px solid #f59e0b !important;
    border-radius: 14px !important;
    padding: 16px !important;
    background: linear-gradient(135deg, #fffbeb, #fef3c7) !important;
}

/* ===== 结果卡片 ===== */
.result-card {
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 18px;
    background: #ffffff;
}

/* ===== Gradio默认元素微调 ===== */
footer { visibility: hidden; }

/* ===== 模块2 仪表盘卡片增强 ===== */
.dashboard-row {
    gap: 14px;
}
.dashboard-row .svelte-1f3543o {
    border-radius: 14px;
    padding: 14px;
    border: 1px solid #e2e8f0;
}

/* ===== 模块3 报告排版增强 ===== */
.report-markdown {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 8px 32px rgba(79, 70, 229, 0.06);
    font-size: 15px;
    line-height: 1.9;
}
.report-markdown h1 {
    font-size: 1.6rem !important;
    color: #1e293b !important;
    text-align: center;
    border-bottom: 2px solid #4f46e5;
    padding-bottom: 14px;
    margin-bottom: 18px;
}
.report-markdown h2 {
    font-size: 1.2rem !important;
    color: #334155 !important;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 8px;
    margin-top: 24px;
}
.report-markdown table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 14px;
}
.report-markdown th {
    background: #f1f5f9;
    color: #1e293b;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
}
.report-markdown td {
    padding: 10px 14px;
    border-bottom: 1px solid #f1f5f9;
}
.report-markdown blockquote {
    border-left: 4px solid #4f46e5;
    background: #eef2ff;
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 14px 0;
}
.report-markdown hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
    margin: 20px 0;
}

/* ===== 模块4 侧边知识库增强 ===== */
.knowledge-markdown {
    font-size: 13px;
    line-height: 1.7;
}
.knowledge-markdown h2 {
    font-size: 1rem !important;
    color: #4f46e5 !important;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 6px;
    margin-top: 14px;
}
.knowledge-markdown h3 {
    font-size: 0.9rem !important;
    color: #334155 !important;
    margin-top: 10px;
}
.knowledge-markdown p {
    margin: 4px 0;
    color: #64748b;
}
"""


# ============================================================
#  模块1：自然语言解析模块
#  功能：从用户口语化输入中提取本金、个股名称/代码、
#        持仓比例、风险偏好；信息不全时弹窗提醒补全
# ============================================================

# --- 股票名称与代码映射表（常见A股标的，可扩展） ---
STOCK_NAME_MAP = {
    # 白酒消费
    "贵州茅台": "600519", "茅台": "600519",
    "五粮液": "000858",
    "泸州老窖": "000568", "老窖": "000568",
    "山西汾酒": "600809", "汾酒": "600809",
    # 新能源
    "宁德时代": "300750", "宁德": "300750",
    "比亚迪": "002594",
    "隆基绿能": "601012", "隆基": "601012",
    "阳光电源": "300274", "阳光": "300274",
    # 金融
    "中国平安": "601318", "平安": "601318",
    "招商银行": "600036", "招行": "600036",
    "中信证券": "600030", "中信": "600030",
    "东方财富": "300059",
    # 医药
    "药明康德": "603259", "药明": "603259",
    "恒瑞医药": "600276", "恒瑞": "600276",
    "迈瑞医疗": "300760", "迈瑞": "300760",
    "片仔癀": "600436",
    # 科技
    "海康威视": "002415", "海康": "002415",
    "中芯国际": "688981", "中芯": "688981",
    "立讯精密": "002475", "立讯": "002475",
    "科大讯飞": "002230",
    # 家电
    "美的集团": "000333", "美的": "000333",
    "格力电器": "000651", "格力": "000651",
    # 其他
    "长江电力": "600900",
    "中国神华": "601088", "神华": "601088",
    "中国中免": "601888", "中免": "601888",
    "紫金矿业": "601899", "紫金": "601899",
    "万科A": "000002", "万科": "000002",
}

# --- 风险偏好关键词映射 ---
RISK_KEYWORDS = {
    "保守": ["保守", "稳健偏保守", "低风险", "谨慎", "保本", "稳健型", "保守型"],
    "稳健": ["稳健", "平衡", "中等风险", "适中", "平衡型", "中风险"],
    "进取": ["进取", "激进", "高风险", "积极", "成长", "进取型", "激进型", "成长型"],
}


def extract_principal(text: str):
    """
    从自然语言文本中提取本金金额
    支持格式：10万/10万元/100000元/10w/本金10万 等
    返回：float 金额（元），未匹配返回 None
    """
    if not text:
        return None

    # 模式1：X万 / X万元 / X万块
    m = re.search(r'(\d+\.?\d*)\s*万(?:元|块|块钱)?', text)
    if m:
        return float(m.group(1)) * 10000

    # 模式2：Xw / XW（如 10w、50W）
    m = re.search(r'(\d+\.?\d*)\s*[wW](?!\w)', text)
    if m:
        return float(m.group(1)) * 10000

    # 模式3：本金:XX / 资金XX元
    m = re.search(r'(?:本金|资金|投入|总资金)[:：]?\s*(\d+\.?\d*)\s*(?:万|元|块)?', text)
    if m:
        val = float(m.group(1))
        if val < 10000 and ('万' not in m.group(0)):
            # 可能是以万为单位的小数，检查上下文
            pass
        return val if val >= 10000 else val * 10000 if '万' in m.group(0) else val

    # 模式4：纯数字（≥4位整数，视为金额）
    m = re.search(r'(?<!\d)(\d{4,9})(?!\d)', text)
    if m:
        return float(m.group(1))

    return None


def extract_stock(text: str):
    """
    从自然语言文本中提取股票名称或代码
    优先匹配6位数字代码，其次匹配名称关键词
    返回：dict {"name": str, "code": str} 或 None
    """
    if not text:
        return None

    # 优先匹配6位数字代码（A股代码格式）
    m = re.search(r'(?<!\d)(\d{6})(?!\d)', text)
    if m:
        code = m.group(1)
        # 反向查找名称
        for name, c in STOCK_NAME_MAP.items():
            if c == code:
                return {"name": name, "code": code}
        return {"name": f"股票({code})", "code": code}

    # 按名称关键词匹配（优先长名称，避免"平安"误匹配"中国平安"）
    matched = []
    for name, code in STOCK_NAME_MAP.items():
        if name in text:
            matched.append((len(name), name, code))
    if matched:
        # 取最长匹配（最精确）
        matched.sort(key=lambda x: x[0], reverse=True)
        _, name, code = matched[0]
        return {"name": name, "code": code}

    return None


def extract_position_ratio(text: str):
    """
    从自然语言文本中提取持仓比例
    支持格式：30%、三成、半仓、满仓、一半 等
    返回：float 比例（0.0~1.0），未匹配返回 None
    """
    if not text:
        return None

    # 模式1：百分比数字（如30%、50.5%）
    m = re.search(r'(\d+\.?\d*)\s*%', text)
    if m:
        ratio = float(m.group(1)) / 100
        return min(ratio, 1.0)

    # 模式2：中文量词
    CHINESE_RATIO = {
        "满仓": 1.0, "全仓": 1.0, "全部": 1.0, "全仓买入": 1.0,
        "九成": 0.9, "九成仓": 0.9,
        "八成": 0.8, "八成仓": 0.8,
        "七成": 0.7, "七成仓": 0.7,
        "六成": 0.6, "六成仓": 0.6,
        "一半": 0.5, "五成": 0.5, "半仓": 0.5, "五成仓": 0.5,
        "四成": 0.4, "四成仓": 0.4,
        "三成": 0.3, "三成仓": 0.3,
        "两成": 0.2, "二成": 0.2, "两成仓": 0.2,
        "一成": 0.1, "一成仓": 0.1,
    }
    for kw, ratio in CHINESE_RATIO.items():
        if kw in text:
            return ratio

    # 模式3：分数表述（如 1/3、三分之 等）
    m = re.search(r'(\d+)\s*分\s*之\s*(\d+)', text)
    if m:
        return float(m.group(1)) / float(m.group(2))

    return None


def extract_risk_preference(text: str):
    """
    从自然语言文本中提取风险偏好
    返回：str "保守" / "稳健" / "进取"，未匹配返回 None
    """
    if not text:
        return None

    # 按关键词匹配
    for preference, keywords in RISK_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return preference

    return None


def parse_natural_language(text: str):
    """
    核心解析函数：从自然语言输入中提取四项关键投资参数
    输入：str 用户口语化描述
    输出：tuple (principal, stock_dict, position_ratio, risk_pref, missing_list)
      - principal: float or None
      - stock_dict: dict {"name", "code"} or None
      - position_ratio: float or None
      - risk_pref: str or None
      - missing_list: list[str] 缺失信息的中文提示
    """
    if not text or not text.strip():
        return None, None, None, None, [
            "💰 请输入本金金额（如：10万元、50000元）",
            "📈 请输入个股名称或代码（如：茅台、600519）",
            "📊 请输入持仓比例（如：六成仓、30%）",
            "⚖️ 请选择风险偏好（保守 / 稳健 / 进取）",
        ]

    # 逐项提取
    principal = extract_principal(text)
    stock = extract_stock(text)
    position = extract_position_ratio(text)
    risk = extract_risk_preference(text)

    # 收集缺失信息
    missing = []
    if principal is None:
        missing.append('💰 本金金额未识别（请说明：如「10万元」、「50000元」）')
    if stock is None:
        missing.append('📈 个股名称或代码未识别（请说明：如「茅台」、「600519」）')
    if position is None:
        missing.append('📊 持仓比例未识别（请说明：如「六成仓」、「30%」、「半仓」）')
    if risk is None:
        missing.append("⚖️ 风险偏好未识别（请选择：保守 / 稳健 / 进取）")

    return principal, stock, position, risk, missing


# --- 模块1 UI 组件构建函数 ---

def create_module1_ui():
    """
    创建模块1的Gradio UI组件
    返回：包含输入文本框和解析按钮的UI组件字典
    """
    with gr.Column(elem_classes=["module-container"]):
        # 模块标题
        gr.Markdown(
            """
            ## 🔍 模块一：自然语言解析
            > 请用日常口语描述您的投资需求，系统将智能提取关键参数
            """
        )

        # 示例提示
        with gr.Accordion("💡 输入示例（点击展开）", open=False):
            gr.Markdown(
                """
                - *"我本金10万元，买了茅台，现在六成仓，风险偏好比较保守"*
                - *"投了5万块在宁德时代，持仓30%，我想稳健一点"*
                - *"资金20万元，600519半仓，我是进取型投资者"*
                - *"50万全仓比亚迪，风险偏好激进"*
                """
            )

        # 输入区域
        with gr.Row():
            nl_input = gr.Textbox(
                label="📝 请描述您的投资情况",
                placeholder="例如：我本金10万元，买了茅台，现在六成仓，风险偏好偏保守...",
                lines=4,
                scale=5,
                elem_classes=["input-textbox"],
            )

        # 解析按钮
        with gr.Row():
            parse_btn = gr.Button(
                "🔎 智能解析",
                variant="primary",
                size="lg",
                scale=1,
                elem_classes=["parse-button"],
            )

        # 解析结果展示区域（信息完整时显示）
        with gr.Row(visible=False) as result_row:
            with gr.Column():
                gr.Markdown("### ✅ 解析结果")
                with gr.Row():
                    principal_display = gr.Textbox(
                        label="💰 本金",
                        interactive=False,
                        scale=1,
                    )
                    stock_display = gr.Textbox(
                        label="📈 个股",
                        interactive=False,
                        scale=1,
                    )
                    position_display = gr.Textbox(
                        label="📊 持仓比例",
                        interactive=False,
                        scale=1,
                    )
                    risk_display = gr.Textbox(
                        label="⚖️ 风险偏好",
                        interactive=False,
                        scale=1,
                    )

        # 缺失信息提醒区域（信息不全时显示）
        with gr.Row(visible=False) as warning_row:
            missing_display = gr.Markdown(
                value="",
                elem_classes=["warning-markdown"],
            )

        # 隐藏的状态组件（用于跨模块传递数据）
        parsed_state = gr.State(value=None)

    return {
        "nl_input": nl_input,
        "parse_btn": parse_btn,
        "result_row": result_row,
        "principal_display": principal_display,
        "stock_display": stock_display,
        "position_display": position_display,
        "risk_display": risk_display,
        "warning_row": warning_row,
        "missing_display": missing_display,
        "parsed_state": parsed_state,
    }


def on_parse_click(text: str):
    """
    解析按钮回调：执行自然语言解析并返回UI更新
    """
    principal, stock, position, risk, missing = parse_natural_language(text)

    if principal is not None and stock is not None and position is not None and risk is not None:
        # 信息完整 → 显示解析结果
        parsed_data = {
            "principal": principal,
            "stock_name": stock["name"],
            "stock_code": stock["code"],
            "position_ratio": position,
            "risk_preference": risk,
            "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return (
            gr.update(visible=True),                          # result_row
            f"¥{principal:,.0f} 元",                          # principal_display
            f"{stock['name']}（{stock['code']}）",            # stock_display
            f"{position*100:.0f}%（{position*100:.1f}%）",     # position_display
            risk,                                              # risk_display
            gr.update(visible=False),                          # warning_row
            "",                                                # missing_display
            parsed_data,                                       # parsed_state
        )
    else:
        # 信息不全 → 显示提醒
        missing_items = "\n".join([f"- {m}" for m in missing])
        warning_html = (
            "### ⚠️ 信息不完整，请补充以下内容：\n\n"
            + missing_items
            + "\n\n> 💡 请在上方文本框中补充缺失信息后，重新点击「智能解析」"
        )
        return (
            gr.update(visible=False),     # result_row
            "", "", "", "",               # displays (hidden)
            gr.update(visible=True),      # warning_row
            warning_html,                 # missing_display
            None,                         # parsed_state
        )


# ============================================================
#  模块2：智能风控测算模块
#  功能：核算持仓市值与闲置资金；依据风控阈值（保守25%/
#        稳健35%/进取50%）给出仓位三档提醒（正常/轻度超配/
#        重仓预警）；计算止损参考价与最大可承受亏损
# ============================================================

# --- 风控阈值配置表 ---
RISK_CONTROL_CONFIG = {
    "保守": {
        "max_position_pct": 0.25,      # 仓位上限 25%
        "stop_loss_pct": -0.08,         # 止损线 -8%
        "color": "#10b981",             # 绿色系
        "icon": "🛡️",
        "description": "以本金安全为首要目标，严控仓位与回撤",
    },
    "稳健": {
        "max_position_pct": 0.35,      # 仓位上限 35%
        "stop_loss_pct": -0.12,         # 止损线 -12%
        "color": "#f59e0b",             # 琥珀色系
        "icon": "⚖️",
        "description": "兼顾收益与风险，适度放大仓位容忍度",
    },
    "进取": {
        "max_position_pct": 0.50,      # 仓位上限 50%
        "stop_loss_pct": -0.18,         # 止损线 -18%
        "color": "#ef4444",             # 红色系
        "icon": "🚀",
        "description": "追求高收益，承受较大波动与回撤",
    },
}


def assess_position_level(position_ratio: float, max_pct: float):
    """
    评估仓位等级（三档制）
    参数：
      - position_ratio: 实际持仓比例（0~1）
      - max_pct: 风控阈值上限（0~1）
    返回：tuple (level_str, level_class, alert_icon)
      - "normal"   → 正常（绿色）
      - "mild"     → 轻度超配（黄色）
      - "heavy"    → 重仓预警（红色）
    """
    if position_ratio <= max_pct:
        return "✅ 正常", "normal", "#10b981"
    elif position_ratio <= max_pct + 0.15:
        # 超出阈值但在15%容忍范围内
        over_pct = (position_ratio - max_pct) * 100
        return f"⚠️ 轻度超配（超出上限 {over_pct:.1f}%）", "mild", "#f59e0b"
    else:
        over_pct = (position_ratio - max_pct) * 100
        return f"🔴 重仓预警（超出上限 {over_pct:.1f}%）", "heavy", "#ef4444"


def calculate_stop_loss(position_value: float, stop_loss_pct: float, current_price: float = None):
    """
    计算止损参考
    参数：
      - position_value: 持仓市值（元）
      - stop_loss_pct: 止损比例（负数，如 -0.08）
      - current_price: 当前股价（可选，用于计算止损价位）
    返回：dict 止损信息
    """
    max_loss_amount = position_value * abs(stop_loss_pct)
    stop_loss_value = position_value * (1 + stop_loss_pct)  # stop_loss_pct 为负数

    result = {
        "max_loss_amount": max_loss_amount,
        "stop_loss_value": stop_loss_value,
        "stop_loss_ratio": f"{abs(stop_loss_pct)*100:.0f}%",
        "current_price": current_price,
    }

    if current_price and current_price > 0:
        stop_loss_price = current_price * (1 + stop_loss_pct)
        result["stop_loss_price"] = stop_loss_price
        result["decline_per_share"] = current_price - stop_loss_price

    return result


def run_risk_calculation(parsed_data: dict, current_price: float = None):
    """
    核心风控测算函数：基于模块1解析结果，输出完整风控指标
    参数：
      - parsed_data: 模块1输出的解析数据
      - current_price: 当前股价（可选，默认按面值估算）
    返回：dict 完整风控测算结果
    """
    if not parsed_data:
        return None

    principal = parsed_data["principal"]
    position_ratio = parsed_data["position_ratio"]
    risk_pref = parsed_data["risk_preference"]
    stock_name = parsed_data["stock_name"]
    stock_code = parsed_data["stock_code"]

    # 获取风控配置
    config = RISK_CONTROL_CONFIG.get(risk_pref, RISK_CONTROL_CONFIG["稳健"])

    # ---- 1. 核算持仓市值与闲置资金 ----
    position_value = principal * position_ratio       # 持仓市值
    idle_funds = principal - position_value            # 闲置资金

    # ---- 2. 仓位等级评估 ----
    position_level, level_tag, level_color = assess_position_level(
        position_ratio, config["max_position_pct"]
    )

    # ---- 3. 止损参考计算 ----
    stop_loss_info = calculate_stop_loss(
        position_value, config["stop_loss_pct"], current_price
    )

    # ---- 4. 风险敞口 ----
    risk_exposure = position_value / principal if principal > 0 else 0

    # ---- 5. 建议仓位调整 ----
    suggested_max_position = principal * config["max_position_pct"]
    suggested_reduce = max(0, position_value - suggested_max_position)

    return {
        # 输入参数回显
        "principal": principal,
        "stock_name": stock_name,
        "stock_code": stock_code,
        "position_ratio": position_ratio,
        "risk_preference": risk_pref,
        "current_price": current_price,
        # 核算结果
        "position_value": position_value,
        "idle_funds": idle_funds,
        "risk_exposure": risk_exposure,
        # 风控配置
        "max_position_pct": config["max_position_pct"],
        "stop_loss_pct": config["stop_loss_pct"],
        "config_description": config["description"],
        # 仓位等级
        "position_level": position_level,
        "level_tag": level_tag,
        "level_color": level_color,
        # 止损
        "stop_loss_info": stop_loss_info,
        # 建议
        "suggested_max_position": suggested_max_position,
        "suggested_reduce": suggested_reduce,
        # 时间戳
        "calculated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# --- 模块2 UI 组件构建函数 ---

def create_module2_ui():
    """
    创建模块2的Gradio UI组件
    返回：包含当前股价输入、测算按钮、风控仪表盘的UI组件字典
    """
    with gr.Column(elem_classes=["module-container"]):
        # 模块标题
        gr.Markdown(
            """
            ## 📊 模块二：智能风控测算
            > 基于您的持仓信息，自动核算风控指标并给出仓位预警与止损参考
            """
        )

        # 输入区：当前股价（可选）
        with gr.Row():
            price_input = gr.Number(
                label="📈 当前股价（元/股，可选）",
                placeholder="如：1800.00（填完后可计算精确止损价位）",
                precision=2,
                minimum=0,
                scale=2,
                info="留空则仅按资金面测算，不输出止损价位",
            )
            calc_btn = gr.Button(
                "📊 开始风控测算",
                variant="primary",
                size="lg",
                scale=1,
                elem_classes=["parse-button"],
            )

        # ---- 风控仪表盘（测算完成后显示） ----
        with gr.Column(visible=False) as dashboard_col:
            gr.Markdown("---")

            # 第一行：核心指标卡片
            gr.Markdown("### 📋 账户概览")
            with gr.Row():
                position_value_disp = gr.Textbox(
                    label="💰 持仓市值",
                    interactive=False,
                    scale=1,
                )
                idle_funds_disp = gr.Textbox(
                    label="🏦 闲置资金",
                    interactive=False,
                    scale=1,
                )
                risk_exposure_disp = gr.Textbox(
                    label="📐 风险敞口",
                    interactive=False,
                    scale=1,
                )

            # 第二行：风控阈值 + 仓位等级
            gr.Markdown("### ⚙️ 风控阈值与仓位评估")
            with gr.Row():
                threshold_disp = gr.Textbox(
                    label="🎯 风控仓位上限",
                    interactive=False,
                    scale=1,
                )
                position_level_disp = gr.Textbox(
                    label="📶 仓位等级",
                    interactive=False,
                    scale=2,
                )

            # 第三行：止损参考
            gr.Markdown("### 🛑 止损参考")
            with gr.Row():
                stop_loss_ratio_disp = gr.Textbox(
                    label="📉 止损比例",
                    interactive=False,
                    scale=1,
                )
                max_loss_disp = gr.Textbox(
                    label="💸 最大可承受亏损",
                    interactive=False,
                    scale=1,
                )
                stop_loss_price_disp = gr.Textbox(
                    label="🎯 止损价位（元/股）",
                    interactive=False,
                    scale=1,
                )

            # 第四行：调仓建议
            gr.Markdown("### 💡 调仓建议")
            with gr.Row():
                suggestion_disp = gr.Textbox(
                    label="📝 智能建议",
                    interactive=False,
                    lines=3,
                    scale=1,
                )

        # 隐藏状态：存储测算结果供后续模块使用
        calc_result_state = gr.State(value=None)

    return {
        "price_input": price_input,
        "calc_btn": calc_btn,
        "dashboard_col": dashboard_col,
        "position_value_disp": position_value_disp,
        "idle_funds_disp": idle_funds_disp,
        "risk_exposure_disp": risk_exposure_disp,
        "threshold_disp": threshold_disp,
        "position_level_disp": position_level_disp,
        "stop_loss_ratio_disp": stop_loss_ratio_disp,
        "max_loss_disp": max_loss_disp,
        "stop_loss_price_disp": stop_loss_price_disp,
        "suggestion_disp": suggestion_disp,
        "calc_result_state": calc_result_state,
    }


def on_calculate_click(parsed_data, current_price):
    """
    测算按钮回调：执行风控计算并刷新仪表盘
    """
    if parsed_data is None:
        # 未完成模块1解析 → 提示
        return (
            gr.update(visible=False),   # dashboard_col
            "", "", "",                  # 概览
            "", "",                      # 阈值、仓位
            "", "", "",                  # 止损
            "",                          # 建议
            None,                        # calc_result_state
        )

    # 执行风控测算
    result = run_risk_calculation(parsed_data, current_price if current_price else None)

    if result is None:
        return (
            gr.update(visible=False), "", "", "", "", "", "", "", "", "", None
        )

    # ---- 构建显示文本 ----

    # 账户概览
    position_str = f"¥{result['position_value']:,.2f} 元"
    idle_str = f"¥{result['idle_funds']:,.2f} 元"
    exposure_str = f"{result['risk_exposure']*100:.1f}%"

    # 风控阈值
    threshold_str = (
        f"{result['risk_preference']}型 · 上限 {result['max_position_pct']*100:.0f}%\n"
        f"{result['config_description']}"
    )

    # 仓位等级
    level_str = result["position_level"]

    # 止损
    sl_info = result["stop_loss_info"]
    stop_loss_ratio_str = f"最大回撤 {sl_info['stop_loss_ratio']}"
    max_loss_str = f"¥{sl_info['max_loss_amount']:,.2f} 元"

    if sl_info.get("stop_loss_price"):
        price_str = f"¥{sl_info['stop_loss_price']:.2f}（每股跌 ¥{sl_info.get('decline_per_share', 0):.2f}）"
    else:
        price_str = "（未输入当前股价，无法计算）"

    # 调仓建议
    if result["suggested_reduce"] > 0:
        suggestion_str = (
            f"⚠️ 您当前持仓 {result['position_ratio']*100:.1f}%，"
            f"超出{result['risk_preference']}型上限 {result['max_position_pct']*100:.0f}%。\n"
            f"建议减仓 ¥{result['suggested_reduce']:,.2f} 元，"
            f"将仓位降至 ¥{result['suggested_max_position']:,.2f} 元以内。\n"
            f"📌 止损纪律：若持仓亏损达 {sl_info['stop_loss_ratio']}（¥{sl_info['max_loss_amount']:,.2f}），"
            f"应果断执行止损。"
        )
    else:
        surplus = result["suggested_max_position"] - result["position_value"]
        suggestion_str = (
            f"✅ 您当前持仓 {result['position_ratio']*100:.1f}%，"
            f"在{result['risk_preference']}型上限 {result['max_position_pct']*100:.0f}% 以内。\n"
            f"仍有 ¥{surplus:,.2f} 加仓空间，可择机增持。\n"
            f"📌 止损纪律：若持仓亏损达 {sl_info['stop_loss_ratio']}（¥{sl_info['max_loss_amount']:,.2f}），"
            f"应果断执行止损。"
        )

    return (
        gr.update(visible=True),     # dashboard_col
        position_str,                # position_value_disp
        idle_str,                    # idle_funds_disp
        exposure_str,                # risk_exposure_disp
        threshold_str,               # threshold_disp
        level_str,                   # position_level_disp
        stop_loss_ratio_str,         # stop_loss_ratio_disp
        max_loss_str,                # max_loss_disp
        price_str,                   # stop_loss_price_disp
        suggestion_str,              # suggestion_disp
        result,                      # calc_result_state
    )


# ============================================================
#  模块3：标准化风控报告模块
#  功能：分段生成正式风控报告单，包含账户概况、持仓明细、
#        风控结论、实操建议四大板块，排版工整可供打印/投屏
# ============================================================

def generate_risk_report(parsed_data: dict, calc_result: dict):
    """
    基于模块1解析结果 + 模块2测算结果，生成标准化风控报告
    参数：
      - parsed_data: 模块1输出的解析数据
      - calc_result: 模块2输出的测算结果
    返回：str 格式化的Markdown报告文本
    """
    if not parsed_data or not calc_result:
        return None

    # ---- 解包数据 ----
    principal = parsed_data["principal"]
    stock_name = parsed_data["stock_name"]
    stock_code = parsed_data["stock_code"]
    position_ratio = parsed_data["position_ratio"]
    risk_pref = parsed_data["risk_preference"]
    parsed_at = parsed_data.get("parsed_at", "")

    position_value = calc_result["position_value"]
    idle_funds = calc_result["idle_funds"]
    risk_exposure = calc_result["risk_exposure"]
    max_position_pct = calc_result["max_position_pct"]
    stop_loss_pct = calc_result["stop_loss_pct"]
    position_level = calc_result["position_level"]
    level_tag = calc_result["level_tag"]
    config_desc = calc_result["config_description"]
    sl_info = calc_result["stop_loss_info"]
    suggested_reduce = calc_result["suggested_reduce"]
    suggested_max = calc_result["suggested_max_position"]
    current_price = calc_result.get("current_price")
    calculated_at = calc_result["calculated_at"]

    # ---- 风险等级对应中文 ----
    risk_label_map = {"保守": "🛡️ 保守型", "稳健": "⚖️ 稳健型", "进取": "🚀 进取型"}

    # ---- 仓评状态徽章 ----
    if level_tag == "normal":
        level_badge = "🟢 正常"
    elif level_tag == "mild":
        level_badge = "🟡 轻度超配"
    else:
        level_badge = "🔴 重仓预警"

    # ---- 止损价位行 ----
    if sl_info.get("stop_loss_price") and current_price:
        stop_price_line = (
            f"| 当前股价 | ¥{current_price:,.2f} |\n"
            f"| 止损价位 | ¥{sl_info['stop_loss_price']:,.2f}"
            f"（每股下跌 ¥{sl_info.get('decline_per_share', 0):,.2f}） |"
        )
    else:
        stop_price_line = "| 当前股价 | （未输入） |\n| 止损价位 | 无法计算（请填写当前股价后重新测算） |"

    # ---- 组装报告 ----
    report = f"""
# 🐫 驼灵 · A股智能风控投顾 — 风控报告单

> **生成时间：** {calculated_at} &nbsp;|&nbsp; **解析时间：** {parsed_at}

---

## 一、账户概况

| 项目 | 数值 |
|------|------|
| 账户总资产 | ¥{principal:,.2f} 元 |
| 风险偏好 | {risk_label_map.get(risk_pref, risk_pref)} |
| 风控策略 | {config_desc} |

---

## 二、持仓明细

| 项目 | 详情 |
|------|------|
| 标的证券 | {stock_name}（{stock_code}） |
| 持仓比例 | {position_ratio*100:.1f}% |
| 持仓市值 | ¥{position_value:,.2f} 元 |
| 闲置资金 | ¥{idle_funds:,.2f} 元 |
| 风险敞口 | {risk_exposure*100:.1f}% |

---

## 三、风控结论

| 指标 | 判定 |
|------|------|
| 风控仓位上限 | {max_position_pct*100:.0f}%（{risk_pref}型标准） |
| 实际仓位 | {position_ratio*100:.1f}% |
| 仓位评估 | {level_badge} — {position_level} |
| 止损纪律 | 最大回撤 **{abs(stop_loss_pct)*100:.0f}%**，即亏损不超过 ¥{sl_info['max_loss_amount']:,.2f} |
{stop_price_line}

---

## 四、实操建议

"""

    # 根据仓位等级输出不同建议
    if suggested_reduce > 0:
        report += f"""
> ⚠️ **减仓建议**

当前仓位 **{position_ratio*100:.1f}%** 已超出「{risk_pref}型」上限 **{max_position_pct*100:.0f}%**，
建议按以下方案调仓：

1. **减仓金额：** ¥{suggested_reduce:,.2f} 元
2. **目标仓位：** 降至 ¥{suggested_max:,.2f} 元（占比 ≤ {max_position_pct*100:.0f}%）以内
3. **止损纪律：** 若持仓亏损触及 **{abs(stop_loss_pct)*100:.0f}%**（¥{sl_info['max_loss_amount']:,.2f}），**必须无条件执行止损**
4. **闲置配置：** 减仓释放的 ¥{suggested_reduce:,.2f} 元可配置货币基金或逆回购，保持流动性
"""
    else:
        surplus = suggested_max - position_value
        report += f"""
> ✅ **仓位合规**

当前仓位 **{position_ratio*100:.1f}%** 在「{risk_pref}型」上限 **{max_position_pct*100:.0f}%** 以内，风控绿灯。

1. **可用空间：** 仍有 ¥{surplus:,.2f} 加仓空间，可择机增持
2. **止损纪律：** 若持仓亏损触及 **{abs(stop_loss_pct)*100:.0f}%**（¥{sl_info['max_loss_amount']:,.2f}），**必须无条件执行止损**
3. **止盈建议：** 建议设置阶梯止盈，盈利 **+15%~+25%** 分批兑现
4. **定期复盘：** 建议每周复盘一次仓位，根据市场变化动态调整
"""

    report += f"""
---

> 📌 *本报告由驼灵智能体自动生成，仅供参考，不构成投资建议。投资有风险，入市需谨慎。*
> 报告编号：TL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{stock_code}
"""

    return report


# --- 模块3 UI 组件构建函数 ---

def create_module3_ui():
    """
    创建模块3的Gradio UI组件
    返回：报告生成按钮 + 报告展示区的UI组件字典
    """
    with gr.Column(elem_classes=["module-container"]):
        gr.Markdown(
            """
            ## 📄 模块三：标准化风控报告
            > 一键生成正式风控报告单，分段展示账户概况、持仓明细、风控结论与实操建议
            """
        )

        # 报告生成按钮
        with gr.Row():
            report_btn = gr.Button(
                "📄 生成风控报告",
                variant="primary",
                size="lg",
                scale=1,
                elem_classes=["parse-button"],
            )

        # 报告展示区
        with gr.Column(visible=False) as report_col:
            gr.Markdown("---")
            report_display = gr.Markdown(
                value="",
                elem_classes=["report-markdown"],
                latex_delimiters=[
                    {"left": "$$", "right": "$$", "display": True},
                ],
            )
            # 报告复制提示
            gr.Markdown(
                "> 💡 选中报告内容即可复制，或使用浏览器打印功能导出 PDF"
            )

    return {
        "report_btn": report_btn,
        "report_col": report_col,
        "report_display": report_display,
    }


def on_generate_report(parsed_data, calc_result):
    """
    报告生成按钮回调：生成标准化风控报告并展示
    """
    if parsed_data is None:
        return gr.update(visible=False), "### ⚠️ 请先完成模块一的自然语言解析"

    if calc_result is None:
        return gr.update(visible=False), "### ⚠️ 请先完成模块二的风控测算"

    report = generate_risk_report(parsed_data, calc_result)

    if report is None:
        return gr.update(visible=False), "### ❌ 报告生成失败，请检查输入数据"

    return gr.update(visible=True), report


# ============================================================
#  模块4：侧边投资知识库模块
#  功能：页面侧边栏嵌入不同风险偏好理财小贴士，
#        根据模块1解析结果自动高亮匹配知识卡片
# ============================================================

# --- 投资知识库内容（按风险偏好分级） ---

KNOWLEDGE_BASE = {
    "通用": {
        "icon": "📚",
        "color": "#4f46e5",
        "title": "投资通则",
        "tips": [
            {
                "title": "🔑 仓位管理黄金法则",
                "content": "单只股票仓位不超过总资产 **20%**，单一行业不超过 **40%**。"
                "永远保留至少 **10%** 现金应对极端行情。",
            },
            {
                "title": "📏 止损纪律铁律",
                "content": "任何一笔交易，亏损达到买入成本的 **7-8%** 无条件止损。"
                "不要因为'舍不得'而让亏损扩大——截断亏损，让利润奔跑。",
            },
            {
                "title": "📅 定期再平衡",
                "content": "每季度检查一次持仓，当某类资产偏离目标配置 **5%** 以上时，"
                "执行再平衡操作，恢复原始配置比例。",
            },
            {
                "title": "📰 信息甄别原则",
                "content": "优先关注 **公司公告、财报、行业研报** 等一手信息。"
                "对'内幕消息'、'荐股群'、'涨停预测'保持警惕——这些往往是割韭菜的镰刀。",
            },
        ],
    },
    "保守": {
        "icon": "🛡️",
        "color": "#10b981",
        "title": "保守型投资指南",
        "tips": [
            {
                "title": "🏦 货币基金打底",
                "content": "建议 **50%+** 资金配置货币基金（如余额宝、零钱通），"
                "年化约 **2-3%**，流动性极好，随时可取。适合作为资金'蓄水池'。",
            },
            {
                "title": "📊 宽基指数定投",
                "content": "推荐 **沪深300ETF（510300）** 或 **中证500ETF（510500）**，"
                "采用每月定投方式，分散入场时点，长期年化预期 **6-10%**。",
            },
            {
                "title": "🏆 高股息蓝筹",
                "content": "关注股息率 **>3.5%** 的大盘蓝筹股，如银行、电力、交运板块。"
                "股利稳定、波动较小，适合保守型投资者长期持有吃息。",
            },
            {
                "title": "🛡️ 可转债打新",
                "content": "开通证券账户即可参与可转债打新，几乎零风险，中签后上市首日卖出，"
                "平均每签收益 **200-500元**，适合保守型投资者增厚收益。",
            },
        ],
    },
    "稳健": {
        "icon": "⚖️",
        "color": "#f59e0b",
        "title": "稳健型投资指南",
        "tips": [
            {
                "title": "⚖️ 股债平衡策略",
                "content": "经典的 **60/40 组合**：60% 权益类（股票/指数基金）+ 40% 固收类（债券/理财）。"
                "每半年再平衡一次，长期年化预期 **8-12%**，波动可控。",
            },
            {
                "title": "📈 行业ETF轮动",
                "content": "关注 **消费、医药、科技、新能源** 四大赛道 ETF，"
                "每季度根据行业景气度调整配置比例，避免押注单一行业。",
            },
            {
                "title": "💼 混合型基金精选",
                "content": "优选管理年限 **>5年**、年化收益 **>10%** 的混合型基金，"
                "由专业经理人进行股债配置，适合没有时间盯盘的稳健型投资者。",
            },
            {
                "title": "🔍 分批建仓法",
                "content": "将计划投入资金分为 **3-5 批**，每隔 **2-4 周** 买入一批。"
                "避免一次性在阶段性高点建仓，有效降低买入成本波动。",
            },
        ],
    },
    "进取": {
        "icon": "🚀",
        "color": "#ef4444",
        "title": "进取型投资指南",
        "tips": [
            {
                "title": "📡 赛道选择框架",
                "content": "优先选择 **政策支持 + 产业趋势 + 业绩兑现** 三重共振的赛道。"
                "当前重点关注：AI应用、低空经济、人形机器人、创新药。",
            },
            {
                "title": "📉 技术分析入门",
                "content": "结合 **均线系统（MA5/20/60）** 和 **MACD 指标** 判断买卖点。"
                "金叉买入、死叉卖出；股价站上60日均线为中线多头信号。",
            },
            {
                "title": "🎢 波动率管理",
                "content": "进取型策略允许单月 **-15%** 的回撤，但需设置硬止损线 **-20%**。"
                "单个交易周内连续亏损 **3次** 即暂停交易，冷静复盘后再入场。",
            },
            {
                "title": "🧪 小仓位试错",
                "content": "对新策略或新标的，先用 **5-10%** 仓位进行 **1-2个月** 实盘验证。"
                "验证通过后再逐步加大仓位，避免重仓踩坑造成不可逆损失。",
            },
        ],
    },
}


def get_knowledge_for_risk(risk_preference: str = None):
    """
    根据风险偏好获取对应知识库内容
    参数：
      - risk_preference: "保守" / "稳健" / "进取" / None
    返回：dict 包含通用知识 + 对应风险等级知识的Markdown文本
    """
    # 通用知识
    general = KNOWLEDGE_BASE.get("通用")
    general_md = f"## {general['icon']} {general['title']}\n\n"
    for tip in general["tips"]:
        general_md += f"### {tip['title']}\n{tip['content']}\n\n"

    # 特定风险知识
    if risk_preference and risk_preference in KNOWLEDGE_BASE:
        specific = KNOWLEDGE_BASE[risk_preference]
        specific_md = f"## {specific['icon']} {specific['title']}\n\n"
        for tip in specific["tips"]:
            specific_md += f"### {tip['title']}\n{tip['content']}\n\n"
    else:
        specific_md = "> 💡 完成模块一解析后，将自动匹配对应风险偏好的投资建议"

    return {
        "general_md": general_md,
        "specific_md": specific_md,
        "risk_icon": KNOWLEDGE_BASE.get(risk_preference, {}).get("icon", "📚") if risk_preference else "📚",
        "risk_title": KNOWLEDGE_BASE.get(risk_preference, {}).get("title", "投资知识") if risk_preference else "投资知识",
        "risk_color": KNOWLEDGE_BASE.get(risk_preference, {}).get("color", "#4f46e5") if risk_preference else "#4f46e5",
    }


def create_module4_sidebar():
    """
    创建模块4侧边栏知识库UI组件
    在 gr.Sidebar 内部调用，返回组件引用
    """
    with gr.Column():
        gr.Markdown(
            """
            ### 📚 投资知识库
            > 理财小贴士 · 风控纪律 · 策略指南
            """
        )

        # 手动切换风险偏好的选项卡
        with gr.Tabs():
            with gr.Tab("🛡️ 保守", id="tab_conservative"):
                conservative_radio = gr.State(value="保守")
            with gr.Tab("⚖️ 稳健", id="tab_moderate"):
                moderate_radio = gr.State(value="稳健")
            with gr.Tab("🚀 进取", id="tab_aggressive"):
                aggressive_radio = gr.State(value="进取")

        # 知识内容展示区
        knowledge_display = gr.Markdown(
            value=get_knowledge_for_risk(None)["general_md"],
            elem_classes=["knowledge-markdown"],
            latex_delimiters=[
                {"left": "$$", "right": "$$", "display": True},
            ],
        )

        # 底部提示
        gr.Markdown(
            """
            ---
            > ⚠️ *以上内容仅供参考学习，不构成投资建议。*
            """
        )

    return {
        "knowledge_display": knowledge_display,
    }


def on_knowledge_tab_select(risk_preference: str):
    """
    知识库选项卡切换回调：更新显示内容
    """
    knowledge = get_knowledge_for_risk(risk_preference)
    full_md = knowledge["general_md"] + "\n---\n" + knowledge["specific_md"]
    return full_md


# ============================================================
#  模块5：历史存储查询模块
#  功能：本地JSON文件缓存每次测算记录，页面控件翻阅/
#        搜索/删除历史账单，支持一键回看完整报告
# ============================================================

import uuid


def _load_json_safe(filepath: str, default=None):
    """安全读取JSON文件，不存在或损坏时返回默认值"""
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else default
    except (json.JSONDecodeError, OSError):
        return default


def _save_json_safe(filepath: str, data):
    """安全写入JSON文件"""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[历史存储] 写入失败: {e}")


def save_history_record(parsed_data: dict, calc_result: dict, report: str):
    """
    保存一条测算记录到本地历史文件
    参数：
      - parsed_data: 模块1解析结果
      - calc_result: 模块2测算结果
      - report: 模块3生成的报告全文
    返回：str 记录ID
    """
    records = _load_json_safe(HISTORY_FILE, default=[])

    record_id = f"TL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    # 序列化时过滤掉不可JSON化的对象，仅保留关键信息
    record = {
        "id": record_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stock_name": parsed_data.get("stock_name", ""),
        "stock_code": parsed_data.get("stock_code", ""),
        "principal": parsed_data.get("principal", 0),
        "position_ratio": parsed_data.get("position_ratio", 0),
        "risk_preference": parsed_data.get("risk_preference", ""),
        "principal_display": f"¥{parsed_data.get('principal', 0):,.0f}",
        "position_display": f"{parsed_data.get('position_ratio', 0)*100:.1f}%",
        "report": report,
        # 保留关键测算指标，便于列表展示
        "position_value": calc_result.get("position_value", 0),
        "position_level": calc_result.get("position_level", ""),
        "level_tag": calc_result.get("level_tag", ""),
    }

    records.insert(0, record)  # 最新在前

    # 最多保留50条防止文件膨胀
    if len(records) > 50:
        records = records[:50]

    _save_json_safe(HISTORY_FILE, records)
    return record_id


def load_all_history():
    """
    加载全部历史记录
    返回：list[dict] 按时间倒序排列
    """
    return _load_json_safe(HISTORY_FILE, default=[])


def delete_history_record(record_id: str):
    """
    删除指定ID的历史记录
    返回：bool 是否成功
    """
    records = _load_json_safe(HISTORY_FILE, default=[])
    new_records = [r for r in records if r.get("id") != record_id]
    if len(new_records) == len(records):
        return False
    _save_json_safe(HISTORY_FILE, new_records)
    return True


def build_history_list_markdown(records: list):
    """
    将历史记录列表构建为可供下拉选择的Markdown摘要
    返回：(choices_list, details_map)
      - choices: list[str] 用于 gr.Dropdown 选项
      - details: dict[str, str] 记录ID→完整报告
    """
    choices = []
    details = {}

    if not records:
        return ["（暂无历史记录）"], {}

    for r in records:
        # 构建简洁的一行摘要
        risk_icon = {"保守": "🛡️", "稳健": "⚖️", "进取": "🚀"}.get(
            r.get("risk_preference", ""), "📊"
        )
        level_icon = {"normal": "🟢", "mild": "🟡", "heavy": "🔴"}.get(
            r.get("level_tag", ""), "⚪"
        )

        label = (
            f"{risk_icon} {r['created_at']} | {r['stock_name']}({r['stock_code']}) | "
            f"本金{r['principal_display']} 仓位{r['position_display']} | {level_icon}"
        )
        choices.append(label)
        details[label] = r.get("report", "（报告内容缺失）")

    return choices, details


# --- 模块5 UI 组件构建函数 ---

def create_module5_ui():
    """
    创建模块5的Gradio UI组件
    返回：历史记录下拉框 + 操作按钮 + 报告回显区
    """
    with gr.Column(elem_classes=["module-container"]):
        gr.Markdown(
            """
            ## 📁 模块五：历史存储查询
            > 每次生成报告后自动保存，支持随时翻阅、回看、删除历史账单
            """
        )

        # 控制栏：下拉选择 + 操作按钮
        with gr.Row():
            history_dropdown = gr.Dropdown(
                label="📋 历史记录",
                choices=["（暂无历史记录）"],
                value=None,
                interactive=True,
                scale=4,
                info="选择一条记录即可回看完整报告",
            )
            refresh_btn = gr.Button(
                "🔄 刷新列表",
                variant="secondary",
                scale=1,
            )
            delete_btn = gr.Button(
                "🗑️ 删除选中",
                variant="stop",
                scale=1,
            )

        # 历史报告回显区
        with gr.Column(visible=False) as history_report_col:
            gr.Markdown("---")
            history_report_display = gr.Markdown(
                value="",
                elem_classes=["report-markdown"],
                latex_delimiters=[
                    {"left": "$$", "right": "$$", "display": True},
                ],
            )

        # 隐藏状态：缓存choices→report的映射
        history_details_state = gr.State(value={})

    return {
        "history_dropdown": history_dropdown,
        "refresh_btn": refresh_btn,
        "delete_btn": delete_btn,
        "history_report_col": history_report_col,
        "history_report_display": history_report_display,
        "history_details_state": history_details_state,
    }


def on_refresh_history():
    """
    刷新历史列表回调
    """
    records = load_all_history()
    choices, details = build_history_list_markdown(records)
    return (
        gr.update(choices=choices, value=choices[0] if choices else None),
        details,
    )


def on_select_history(selected_label: str, details_map: dict):
    """
    选择历史记录回调：回显对应完整报告
    """
    if not selected_label or selected_label == "（暂无历史记录）":
        return gr.update(visible=False), ""

    report = details_map.get(selected_label, "")
    if not report:
        return gr.update(visible=False), "### ❌ 记录内容缺失"

    return gr.update(visible=True), report


def on_delete_history(selected_label: str, details_map: dict):
    """
    删除选中历史记录回调
    """
    if not selected_label or selected_label == "（暂无历史记录）":
        return (
            gr.update(choices=["（暂无历史记录）"], value=None),
            {},
            gr.update(visible=False),
            "",
        )

    # 从详情映射中找到对应的记录ID
    records = load_all_history()
    target_id = None
    for r in records:
        risk_icon = {"保守": "🛡️", "稳健": "⚖️", "进取": "🚀"}.get(
            r.get("risk_preference", ""), "📊"
        )
        level_icon = {"normal": "🟢", "mild": "🟡", "heavy": "🔴"}.get(
            r.get("level_tag", ""), "⚪"
        )
        label = (
            f"{risk_icon} {r['created_at']} | {r['stock_name']}({r['stock_code']}) | "
            f"本金{r['principal_display']} 仓位{r['position_display']} | {level_icon}"
        )
        if label == selected_label:
            target_id = r.get("id")
            break

    if target_id:
        delete_history_record(target_id)

    # 刷新列表
    records = load_all_history()
    choices, details = build_history_list_markdown(records)
    return (
        gr.update(choices=choices, value=choices[0] if choices else None),
        details,
        gr.update(visible=False),
        "",
    )


# ============================================================
#  主界面组装
# ============================================================

def build_demo():
    """
    构建完整的Gradio应用界面（含侧边知识库 + 主内容区）
    """
    with gr.Blocks(
        title="驼灵 · A股智能风控投顾",
        analytics_enabled=False,
    ) as demo:
        # ========== 模块4：侧边投资知识库（左侧栏） ==========
        with gr.Sidebar():
            module4 = create_module4_sidebar()

        # ========== 主内容区 ==========
        # 页面大标题
        with gr.Column(elem_classes=["main-title"]):
            gr.Markdown(
                """
                # 🐫 驼灵 · A股智能风控投顾
                """
            )
        with gr.Column(elem_classes=["subtitle"]):
            gr.Markdown(
                """
                **AI 赋能价值创造** &nbsp;|&nbsp; 智投未来赛道 &nbsp;|&nbsp; 自然语言驱动 · 智能风控测算
                """
            )
        gr.Markdown("---")

        # ========== 模块1：自然语言解析 ==========
        module1 = create_module1_ui()

        # ========== 模块2：智能风控测算 ==========
        gr.Markdown("---")
        module2 = create_module2_ui()

        # ========== 模块3：标准化风控报告 ==========
        gr.Markdown("---")
        module3 = create_module3_ui()

        # ========== 模块5：历史存储查询 ==========
        gr.Markdown("---")
        module5 = create_module5_ui()

        # ========== 模块1 事件绑定 ==========
        module1["parse_btn"].click(
            fn=on_parse_click,
            inputs=[module1["nl_input"]],
            outputs=[
                module1["result_row"],
                module1["principal_display"],
                module1["stock_display"],
                module1["position_display"],
                module1["risk_display"],
                module1["warning_row"],
                module1["missing_display"],
                module1["parsed_state"],
            ],
        )

        # ========== 模块2 事件绑定 ==========
        module2["calc_btn"].click(
            fn=on_calculate_click,
            inputs=[module1["parsed_state"], module2["price_input"]],
            outputs=[
                module2["dashboard_col"],
                module2["position_value_disp"],
                module2["idle_funds_disp"],
                module2["risk_exposure_disp"],
                module2["threshold_disp"],
                module2["position_level_disp"],
                module2["stop_loss_ratio_disp"],
                module2["max_loss_disp"],
                module2["stop_loss_price_disp"],
                module2["suggestion_disp"],
                module2["calc_result_state"],
            ],
        )

        # ========== 模块3 事件绑定：生成报告 + 自动存入历史 ==========
        module3["report_btn"].click(
            fn=on_generate_report,
            inputs=[module1["parsed_state"], module2["calc_result_state"]],
            outputs=[
                module3["report_col"],
                module3["report_display"],
            ],
        )

        # 报告生成后自动存入历史缓存
        def _on_report_save_to_history(parsed_data, calc_result):
            """报告生成时自动保存到本地历史"""
            if parsed_data is None or calc_result is None:
                return gr.update(), {}
            report = generate_risk_report(parsed_data, calc_result)
            if report:
                save_history_record(parsed_data, calc_result, report)
            # 刷新历史列表
            records = load_all_history()
            choices, details = build_history_list_markdown(records)
            return gr.update(choices=choices, value=choices[0] if choices else None), details

        module3["report_btn"].click(
            fn=_on_report_save_to_history,
            inputs=[module1["parsed_state"], module2["calc_result_state"]],
            outputs=[
                module5["history_dropdown"],
                module5["history_details_state"],
            ],
        )

        # ========== 模块4 知识库联动：解析完成后自动更新侧边知识库 ==========
        module1["parse_btn"].click(
            fn=lambda parsed: get_knowledge_for_risk(
                parsed["risk_preference"] if parsed else None
            )["general_md"]
            + "\n---\n"
            + get_knowledge_for_risk(
                parsed["risk_preference"] if parsed else None
            )["specific_md"],
            inputs=[module1["parsed_state"]],
            outputs=[module4["knowledge_display"]],
        )

        # ========== 模块5 事件绑定：刷新/选择/删除历史记录 ==========
        module5["refresh_btn"].click(
            fn=on_refresh_history,
            inputs=[],
            outputs=[
                module5["history_dropdown"],
                module5["history_details_state"],
            ],
        )

        module5["history_dropdown"].change(
            fn=on_select_history,
            inputs=[module5["history_dropdown"], module5["history_details_state"]],
            outputs=[
                module5["history_report_col"],
                module5["history_report_display"],
            ],
        )

        module5["delete_btn"].click(
            fn=on_delete_history,
            inputs=[module5["history_dropdown"], module5["history_details_state"]],
            outputs=[
                module5["history_dropdown"],
                module5["history_details_state"],
                module5["history_report_col"],
                module5["history_report_display"],
            ],
        )

        # 页面底部间距
        gr.Markdown("<br>")

    return demo


# ============================================================
#  启动入口
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  驼灵 · A股智能风控投顾")
    print("  AI 赋能价值创造 | 智投未来赛道")
    print("=" * 60)

    demo = build_demo()

    print("[INFO] 启动服务，正在获取公网链接...")
    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True,
        show_error=True,
        theme=CUSTOM_THEME,
        css=CUSTOM_CSS,
    )
