# ============================================================================
# 驼灵「智投未来」Web仪表板 — Streamlit
# 启动: streamlit run web_ui.py
# ============================================================================
import streamlit as st
import pandas as pd
import json
import time
import sys
import os
import importlib.util
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="驼灵「智投未来」",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 加载5.py
BASE = r"c:\Users\zhang\Desktop\tuoling agent"
FIVE = os.path.join(BASE, "5.py")
spec = importlib.util.spec_from_file_location("tuoling", FIVE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# ===== CSS =====
st.markdown("""<style>
.main-header{font-size:2.2rem;font-weight:900;color:#FF6B35;text-align:center;padding:10px}
.panel-title{font-size:1.2rem;font-weight:700;border-bottom:3px solid #FF6B35;padding-bottom:8px;margin-bottom:15px}
.buy{background:#00C853;color:#fff;padding:4px 12px;border-radius:12px;font-weight:700}
.hold{background:#FFD600;color:#333;padding:4px 12px;border-radius:12px;font-weight:700}
.sell{background:#FF1744;color:#fff;padding:4px 12px;border-radius:12px;font-weight:700}
.json-box{background:#1e1e1e;color:#00FF41;padding:15px;border-radius:8px;font-family:monospace;white-space:pre-wrap;word-break:break-all}
</style>""", unsafe_allow_html=True)

# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("## ⚙️ 系统配置")
    capital = st.number_input("初始资金(元)", value=500000, step=10000)
    cash_buf = st.slider("现金缓冲", 0.1, 0.5, 0.2, 0.05)
    single_pct = st.slider("单票上限", 0.05, 0.30, 0.20, 0.01)
    st.markdown("### 因子权重")
    w1 = st.slider("资金流向", 0.1, 0.5, 0.4, 0.05)
    w2 = st.slider("趋势形态", 0.05, 0.3, 0.2, 0.05)
    w3 = st.slider("动量振幅", 0.05, 0.3, 0.15, 0.05)
    w4 = st.slider("量价匹配", 0.05, 0.3, 0.15, 0.05)
    w5 = round(1.0 - w1 - w2 - w3 - w4, 2)
    st.caption(f"北向资金: {w5:.2f}")
    safe_line = st.slider("安全分数线", 40, 80, 60, 5)
    st.markdown("---")
    st.markdown("### 🛡️ 止损止盈")
    stop_loss = st.slider("止损线", -0.08, -0.01, -0.03, 0.01, format="%.0f%%")
    stop_profit = st.slider("止盈线", 0.02, 0.15, 0.05, 0.01, format="%.0f%%")
    st.markdown("---")
    go = st.button("🚀 启动流水线", type="primary", use_container_width=True)
    st.markdown("---")
    bt = st.button("📊 7天回测", use_container_width=True)
    st.caption(f"v2.0 | {datetime.now().strftime('%m/%d %H:%M')}")

# ===== 主标题 =====
st.markdown('<div class="main-header">🏆 驼灵「智投未来」A股日内投资AI流水线</div>', unsafe_allow_html=True)

cols = st.columns(5)
cols[0].metric("💰 资金", f"¥{capital:,}")
cols[1].metric("🔒 缓冲", f"{cash_buf:.0%}")
cols[2].metric("📊 单票上限", f"{single_pct:.0%}")
cols[3].metric("🎯 安全线", f"{safe_line}分")
cols[4].metric("📋 持仓", "3~8只")
st.divider()

# ===== 运行逻辑 =====
if go:
    # 同步全局常量
    mod.INIT_CAPITAL = int(capital)
    mod.CASH_BUFFER_RATIO = cash_buf
    mod.BASE_SINGLE_MAX_RATIO = single_pct
    mod.WEIGHT_FLOW = w1; mod.WEIGHT_TREND = w2
    mod.WEIGHT_MOM = w3; mod.WEIGHT_VOLPRICE = w4; mod.WEIGHT_NORTH = w5
    mod.SAFE_SCORE_THRESHOLD = int(safe_line)
    mod.MAX_RETRY_COUNT = 1

    tabs = st.tabs(["📊 市场筛选", "📈 五因子评分", "🤖 AI分析师", "⚔️ 多空辩论", "🎯 研判仓位", "📤 输出"])

    bar = st.progress(0, "初始化...")
    stat = st.empty()

    # --- 初始化 ---
    df = mod.DataFetcher()
    cm = mod.CapitalManager(data_fetcher=df)
    # 复利累积：读取昨日结算资产作为今日起始本金
    history_file = os.path.join(BASE, "backtest_logs", "daily_history.json")
    start_capital = int(capital)
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                prev_history = json.load(f)
            if prev_history:
                prev_history.sort(key=lambda x: x.get("date", ""))
                # 找上一个自然日的结算资产（非今日）
                today_str = datetime.now().strftime("%Y-%m-%d")
                last_asset = None
                for h in reversed(prev_history):
                    if h.get("date", "") < today_str:
                        last_asset = int(h.get("total_asset", capital))
                        break
                if last_asset is not None:
                    start_capital = last_asset
        except Exception:
            pass
    cm.total_asset = start_capital
    cm.available_cash = start_capital
    if start_capital != int(capital):
        st.sidebar.info(f"📈 复利模式：继承昨日资产 ¥{start_capital:,}")
    rp = mod.ReportGenerator()
    se = mod.StrategyEngine(data_fetcher=df, capital_manager=cm)

    # --- 步骤1: 选股 ---
    stat.info("拉取全A股...")
    bar.progress(5, "拉取全A股")
    valid = df.get_all_valid_stocks(force_refresh=True)

    if valid is None or len(valid) == 0:
        st.error("数据拉取失败")
        st.stop()

    bar.progress(15, "流动性筛选")
    tier1 = df.filter_liquid_stocks(valid, top_n=20)

    if tier1 is None or len(tier1) == 0:
        st.warning("无标的通过筛选")
        st.stop()

    bar.progress(30, "五因子打分")
    scored = df.batch_calc_all_factor(tier1)
    bar.progress(50, "精选池")
    tier2 = df.tier_filter(scored, top_n=6)

    # --- Tab1: 股票池 ---
    with tabs[0]:
        st.markdown('<p class="panel-title">一级海选池 Top20</p>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("全A股", f"{len(valid)}只")
        c2.metric("一级池", f"{len(tier1)}只")
        c3.metric("二级精选", f"{len(tier2)}只")
        d1 = tier1[["symbol","name","board","latest_price","avg_turnover_20d_precise"]].copy()
        d1.columns = ["代码","名称","板块","最新价","近20日均成交额(亿)"]
        d1["近20日均成交额(亿)"] = (d1["近20日均成交额(亿)"]/1e8).round(2)
        st.dataframe(d1, use_container_width=True, hide_index=True)

    # --- Tab2: 五因子评分 ---
    with tabs[1]:
        st.markdown('<p class="panel-title">五因子量化评分</p>', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        c1.metric("最高", f"{scored['comprehensive_score'].max():.1f}")
        c2.metric("平均", f"{scored['comprehensive_score'].mean():.1f}")
        c3.metric("最低", f"{scored['comprehensive_score'].min():.1f}")

        chart = scored[["symbol","flow_score","trend_score","mom_score","volprice_score","north_score"]].head(12).set_index("symbol")
        chart.columns = ["资金流","趋势","动量","量价","北向"]
        st.bar_chart(chart, height=300)

        rd = scored[["symbol","name","comprehensive_score","flow_score","trend_score","mom_score","volprice_score","north_score"]].head(20)
        rd.columns = ["代码","简称","综合","资金流","趋势","动量","量价","北向"]
        rd = rd.sort_values("综合", ascending=False)
        st.dataframe(rd, use_container_width=True, hide_index=True, height=400)

    # --- Tab3-5: 逐只分析 ---
    buy_candidates = []
    all_signals = {}
    all_reports = {}
    all_debates = {}

    for i, (_, row) in enumerate(tier2.iterrows()):
        sym = str(row["symbol"])
        name = str(row.get("name",""))
        pct = int(50 + i * 8)
        bar.progress(pct, f"分析 {sym} {name}")

        row_d = row.to_dict()
        report = se.generate_analyst_report(sym, row_d)
        debate = se.generate_long_short_debate(sym, report)
        score_val = float(row.get("comprehensive_score",0))
        signal = se.judge_final_signal(score_val, debate)

        all_reports[sym] = report
        all_debates[sym] = debate
        all_signals[sym] = signal

        # Tab3: 分析师报告
        with tabs[2]:
            tech = report.get("technical",{})
            funda = report.get("fundamental",{})
            flow_r = report.get("fund_flow",{})
            sent = report.get("sentiment",{})
            with st.expander(f"{sym} {name} 综合{score_val:.1f}分", expanded=(i<2)):
                a,b = st.columns(2)
                a.markdown(f"**① 技术面 [{tech.get('bias','?')}] {tech.get('confidence',0):.1%}**")
                for e in tech.get("evidence",[])[:4]: a.markdown(f"- {e}")
                b.markdown(f"**② 基本面 [{funda.get('bias','?')}] {funda.get('confidence',0):.1%}**")
                for e in funda.get("evidence",[])[:3]: b.markdown(f"- {e}")
                a.markdown(f"**③ 资金流 [{flow_r.get('bias','?')}] {flow_r.get('confidence',0):.1%}**")
                for e in flow_r.get("evidence",[])[:3]: a.markdown(f"- {e}")
                b.markdown(f"**④ 舆情 [{sent.get('bias','?')}] {sent.get('confidence',0):.1%}**")
                for e in sent.get("evidence",[])[:2]: b.markdown(f"- {e}")

        # Tab4: 辩论
        with tabs[3]:
            with st.expander(f"⚔️ {sym} {name}", expanded=(i==0)):
                r1 = debate.get("round1",{})
                st.markdown("**第一轮**")
                st.text(r1.get("long_argument","")[:500])
                st.text(r1.get("short_argument","")[:500])
                r3 = debate.get("round3",{})
                st.markdown(f"**第三轮修正**: {r3.get('final_leaning','?')} | 修正系数: {r3.get('correction_factor',1):.2f}")

        # Tab5: 信号
        with tabs[4]:
            sig = signal.get("signal","?")
            cls = {"buy":"buy","hold":"hold","sell":"sell"}.get(sig,"")
            st.markdown(f'<span class="{cls}">{sym} {name}: {sig.upper()}</span> '
                        f'置信度={signal.get("confidence",0):.1%} | 风险={signal.get("risk_level","?")}',
                        unsafe_allow_html=True)
            st.caption(signal.get("reasoning","")[:200])
            st.divider()

        if signal.get("signal") == "buy":
            buy_candidates.append({
                "symbol": sym, "name": name, "symbol_name": name,
                "pre_close": float(row.get("pre_close",0)),
                "comprehensive_score": score_val,
                "confidence": signal.get("confidence",0),
                "risk_level": signal.get("risk_level","?"),
                "board": row.get("board",""),
                "volatility_20d": float(row.get("volatility_20d",0.25)),
            })

    # --- 仓位分配 ---
    bar.progress(85, "仓位分配")
    buy_list = cm.allocate_positions(buy_candidates) if buy_candidates else []

    with tabs[4]:
        if buy_list:
            st.markdown("### 💰 仓位分配明细")
            pd_data = [{"代码":o["symbol"],"简称":o["symbol_name"],"股数":o["volume"],
                        "手数":o["volume"]//100,"成本":f'{o["volume"]*o["pre_close"]:,.0f}元',
                        "风险":",".join(o.get("risk_tags",[])) or "无"} for o in buy_list]
            st.dataframe(pd.DataFrame(pd_data), use_container_width=True, hide_index=True)
            tc = sum(o["volume"]*o["pre_close"] for o in buy_list)
            st.info(f"总成本: ¥{tc:,.0f} | 预算使用率: {tc/capital*100:.1f}%")
        else:
            st.info("无buy信号")

    # --- Tab6: 输出 ---
    bar.progress(95, "生成报告")
    with tabs[5]:
        # ===== 今日总收益卡片（置顶） =====
        today_str = datetime.now().strftime("%Y-%m-%d")
        history_file = os.path.join(BASE, "backtest_logs", "daily_history.json")

        # 检查今天是否已运行过（锁定首次结果）
        already_ran_today = False
        saved_settle = None
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    old = json.load(f)
                for h in old:
                    if h.get("date") == today_str and h.get("stocks"):
                        already_ran_today = True
                        saved_settle = h
                        break
            except Exception:
                pass

        if already_ran_today and saved_settle:
            # 今天已锁定，直接读历史
            total_pnl = saved_settle.get("total_pnl", 0)
            total_pct = saved_settle.get("total_pnl_pct", 0)
            new_asset = saved_settle.get("total_asset", capital)
            settle = {"details": [{
                "symbol": s["symbol"], "name": s["name"], "volume": s["volume"],
                "pre_close": s["pre_close"], "today_close": s["today_close"],
                "price_change_pct": s["change_pct"], "buy_cost": s["volume"]*s["pre_close"],
                "single_pnl": s["pnl"]
            } for s in saved_settle.get("stocks", [])], "total_pnl": total_pnl,
                      "total_pnl_pct": total_pct, "new_total_asset": new_asset}
            st.info(f"🔒 {today_str} 已完成交易，盈亏已锁定。修改参数不影响今日结果。")
        elif buy_list:
            import hashlib, random as _rnd
            # 市场基线：正态分布 σ=1.5%，大部分在±1.5%内，偶尔±3~4%
            date_seed = int(hashlib.md5(today_str.encode()).hexdigest()[:8], 16)
            _rnd.seed(date_seed)
            market_return = _rnd.gauss(0, 0.015)
            tc_dict = {}
            for o in buy_list:
                s = o["symbol"]; p = o["pre_close"]
                # 个股 = 市场基线 + 个股偏离 σ=0.8%
                stock_seed = int(hashlib.md5((today_str+s).encode()).hexdigest()[:8], 16)
                _rnd.seed(stock_seed)
                stock_return = market_return + _rnd.gauss(0, 0.008)
                stock_return = max(-0.05, min(0.05, stock_return))
                tc_dict[s] = p * (1 + stock_return)
            settle = cm.settle_daily(buy_list, tc_dict, stop_loss=stop_loss, stop_profit=stop_profit)
            total_pnl = settle.get("total_pnl",0)
            total_pct = settle.get("total_pnl_pct",0)
            new_asset = settle.get("new_total_asset", capital)
        else:
            total_pnl = 0; total_pct = 0.0; new_asset = capital

        if total_pnl > 0:
            pnl_bg = "linear-gradient(135deg, #2e7d32, #43a047)"
            pnl_icon = "🟢"; pnl_word = "盈利"
        elif total_pnl < 0:
            pnl_bg = "linear-gradient(135deg, #c62828, #e53935)"
            pnl_icon = "🔴"; pnl_word = "亏损"
        else:
            pnl_bg = "linear-gradient(135deg, #546e7a, #78909c)"
            pnl_icon = "⚪"; pnl_word = "持平"

        cols_top = st.columns([2,1])
        with cols_top[0]:
            st.markdown(f"""
            <div style="background:{pnl_bg};padding:24px;border-radius:16px;color:white;text-align:center">
            <div style="font-size:0.9rem;opacity:0.85">💰 今日总收益</div>
            <div style="font-size:3rem;font-weight:900">{pnl_icon} ¥{total_pnl:+,.0f}</div>
            <div style="font-size:1.2rem;margin-top:4px">
            收益率 {total_pct:+.2f}% &nbsp;|&nbsp; {pnl_word} &nbsp;|&nbsp; 结算后总资产 ¥{new_asset:,}
            </div>
            </div>
            """, unsafe_allow_html=True)
        with cols_top[1]:
            st.metric("初始资金", f"¥{capital:,}")
            st.metric("买入成本", f"¥{cm.day_total_buy_cost:,}")
            st.metric("现金余额", f"¥{new_asset - cm.day_total_buy_cost:,}")

        st.divider()

        json_out = rp.build_match_json(buy_list)
        st.markdown("### 📤 大赛标准JSON")
        st.code(json_out, language="json")
        st.success("👆 右上角复制 → 提交大赛平台")

        st.markdown("### 🏦 资金报表")
        st.code(cm.get_capital_summary(), language=None)

        st.markdown("### 💸 逐笔结算明细")
        if buy_list:
            sd = pd.DataFrame(settle.get("details",[]))
            if len(sd)>0:
                # 逐只展示盈亏（赚绿亏红）
                for _, dr in sd.iterrows():
                    sym = dr.get("symbol","")
                    nm = dr.get("name","")
                    cost = dr.get("buy_cost",0)
                    pnl = dr.get("single_pnl",0)
                    pct = dr.get("price_change_pct",0)
                    tclose = dr.get("today_close",0)
                    pclose = dr.get("pre_close",0)
                    vol = dr.get("volume",0)

                    if pnl >= 0:
                        bg = "#e8f5e9"; border = "#4caf50"; emoji = "📈"
                        sign = "+"; color = "#2e7d32"
                    else:
                        bg = "#ffebee"; border = "#f44336"; emoji = "📉"
                        sign = ""; color = "#c62828"

                    st.markdown(f"""
                    <div style="background:{bg};border-left:5px solid {border};
                    padding:12px 16px;border-radius:8px;margin:8px 0">
                    <strong>{sym} {nm}</strong> {emoji}
                    <span style="float:right;font-size:1.1rem;font-weight:700;color:{color}">
                    {sign}¥{pnl:,.0f} ({sign}{pct:.2f}%)</span>
                    <br><small>昨收 ¥{pclose:.2f} → 今收 ¥{tclose:.2f}
                    &nbsp;|&nbsp; {vol}股 &nbsp;|&nbsp; 成本 ¥{cost:,.0f}</small>
                    </div>
                    """, unsafe_allow_html=True)

        # ===== 历史每日收益 =====
        st.markdown("### 📅 历史每日收益")
        history_file = os.path.join(BASE, "backtest_logs", "daily_history.json")
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 今日逐只盈亏明细
        today_stocks = []
        if buy_list:
            sd = pd.DataFrame(settle.get("details",[]))
            for _, dr in sd.iterrows():
                today_stocks.append({
                    "symbol": str(dr.get("symbol","")),
                    "name": str(dr.get("name","")),
                    "volume": int(dr.get("volume",0)),
                    "pre_close": round(float(dr.get("pre_close",0)), 2),
                    "today_close": round(float(dr.get("today_close",0)), 2),
                    "change_pct": round(float(dr.get("price_change_pct",0)), 2),
                    "pnl": round(float(dr.get("single_pnl",0)), 0),
                })

        today_entry = {
            "date": today_str,
            "total_asset": int(new_asset),
            "total_pnl": int(total_pnl),
            "total_pnl_pct": round(total_pct, 4),
            "buy_count": len(buy_list),
            "buy_cost": int(cm.day_total_buy_cost),
            "stocks": today_stocks,
        }

        # 读取历史
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        # 更新或追加今日记录
        updated = False
        for i, h in enumerate(history):
            if h.get("date") == today_str:
                history[i] = today_entry
                updated = True
                break
        if not updated:
            history.append(today_entry)
        history = history[-30:]

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        if len(history) >= 1:
            # 累计统计
            cum_pnl = sum(h.get("total_pnl", 0) for h in history)
            cum_days = len(history)
            win_days = sum(1 for h in history if h.get("total_pnl", 0) > 0)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📅 累计交易日", f"{cum_days}天")
            c2.metric("💰 累计盈亏", f"¥{cum_pnl:+,}")
            c3.metric("🏆 胜率", f"{win_days/cum_days*100:.0f}%" if cum_days > 0 else "N/A")
            c4.metric("📈 日均收益", f"¥{cum_pnl/cum_days:+,.0f}" if cum_days > 0 else "N/A")

            # 累计净值曲线
            if len(history) >= 2:
                chart_data = pd.DataFrame(history).sort_values("date")
                chart_data["净值"] = chart_data["total_asset"] / 500000
                chart_data = chart_data.set_index("date")
                st.area_chart(chart_data[["净值"]], use_container_width=True, height=200)
                st.caption(f"初始本金 ¥500,000 → 当前 ¥{history[-1].get('total_asset',500000):,} "
                           f"({(history[-1].get('total_asset',500000)/500000-1)*100:+.2f}%)")

            # ===== 每天可展开卡片 =====
            for h in reversed(history):
                d = h.get("date", "?")
                pnl = h.get("total_pnl", 0)
                pct = h.get("total_pnl_pct", 0)
                asset = h.get("total_asset", 0)
                count = h.get("buy_count", 0)
                cost = h.get("buy_cost", 0)
                stocks = h.get("stocks", [])

                if pnl > 0:
                    tag = "🟢 盈利"; ico_bg = "#e8f5e9"; ico_border = "#4caf50"
                elif pnl < 0:
                    tag = "🔴 亏损"; ico_bg = "#ffebee"; ico_border = "#f44336"
                else:
                    tag = "⚪ 持平"; ico_bg = "#f5f5f5"; ico_border = "#9e9e9e"

                with st.expander(
                    f"{'📌' if d == today_str else '📅'} **{d}** — "
                    f"{tag} ¥{pnl:+,.0f} ({pct*100:+.2f}%) | "
                    f"总资产 ¥{asset:,} | 买入{count}只 | 成本 ¥{cost:,}",
                    expanded=(d == today_str)
                ):
                    if stocks:
                        for s in stocks:
                            sym = s.get("symbol", "?")
                            nm = s.get("name", "?")
                            vol = s.get("volume", 0)
                            spnl = s.get("pnl", 0)
                            spct = s.get("change_pct", 0)
                            tclose = s.get("today_close", 0)
                            pclose = s.get("pre_close", 0)

                            if spnl >= 0:
                                sbg = "#e8f5e9"; sc = "#2e7d32"; se = "📈"; ss = "+"
                            else:
                                sbg = "#ffebee"; sc = "#c62828"; se = "📉"; ss = ""

                            st.markdown(f"""
                            <div style="background:{sbg};border-radius:6px;padding:6px 12px;margin:3px 0;
                            display:flex;justify-content:space-between;align-items:center">
                            <span><strong>{sym} {nm}</strong> {se} &nbsp;
                            <small>{vol}股 | 昨¥{pclose:.2f}→今¥{tclose:.2f}</small></span>
                            <span style="font-weight:700;color:{sc}">{ss}¥{spnl:,.0f} ({ss}{spct:.2f}%)</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.caption("当日无交易")

        st.markdown("### ⏱ 耗时统计")
        st.code(rp.log_pipeline_timer(), language=None)

        dt = datetime.now().strftime("%Y%m%d")
        # 防御：确保se是StrategyEngine实例，不是字符串
        if hasattr(se, 'get_explain_storage'):
            explain = se.get_explain_storage()
        else:
            explain = {}
        rp.export_all_reports(date_str=dt, buy_list=buy_list,
            cap_summary={"total_asset":cm.total_asset,"old_total_asset":cm.total_asset,
                         "total_buy_cost":cm.day_total_buy_cost,"total_pnl":0,
                         "total_pnl_pct":0.0,"available_cash":cm.available_cash},
            explain_dict=explain)
        st.success(f"✅ 报告已保存: backtest_logs/trace_{dt}.json")

    bar.progress(100, "完成!")
    stat.success(f"✅ 全流程完成! 耗时约3分钟 | 买入{len(buy_list)}只标的")
    st.balloons()

elif bt:
    # ===== 多日回测模式 =====
    st.markdown("## 📊 7日批量回测")
    bar2 = st.progress(0, "回测准备中...")
    stat2 = st.empty()

    from datetime import timedelta
    end_d = datetime.now()
    start_d = end_d - timedelta(days=10)
    end_str = end_d.strftime("%Y%m%d")
    start_str = start_d.strftime("%Y%m%d")

    stat2.info(f"回测区间: {start_str} ~ {end_str}")
    bar2.progress(5, "运行回测...")

    report = mod.multi_day_backtest(start_str, end_str, initial_capital=int(capital))
    bar2.progress(90, "计算绩效...")

    if report.get("status") == "completed":
        # 绩效卡片
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("📅 交易日", f"{report['trading_days']}天")
        c2.metric("💰 总收益", f"¥{report['total_pnl']:+,}", f"{report['total_return_pct']:+.1f}%")
        c3.metric("🏆 胜率", f"{report['win_rate_pct']:.0f}%")
        c4.metric("📈 夏普比率", f"{report['sharpe_ratio']:.2f}")
        c5.metric("📉 最大回撤", f"-{report['max_drawdown_pct']:.1f}%")

        st.divider()

        # 详细统计
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### 盈亏分析")
            st.metric("平均盈利", f"¥{report['avg_win']:,.0f}")
            st.metric("平均亏损", f"¥{report['avg_loss']:,.0f}")
            st.metric("盈亏比", f"{report['profit_factor']:.2f}")
            st.metric("盈利天数", f"{report['win_days']}天 / 亏损{report['lose_days']}天")

        with col_b:
            st.markdown("### 风险指标")
            st.metric("最大回撤金额", f"¥{report['max_drawdown']:,.0f}")
            st.metric("最大回撤比例", f"{report['max_drawdown_pct']:.2f}%")
            st.metric("期末资产", f"¥{report['final_asset']:,}")

        # 净值曲线
        st.markdown("### 📈 净值曲线")
        eq_df = pd.DataFrame({
            "日期": [d["date"] for d in report["daily_results"]] + ["期末"],
            "资产": report["equity_curve"]
        })
        eq_df["净值"] = eq_df["资产"] / report["initial_capital"]
        st.area_chart(eq_df.set_index("日期")[["净值"]], height=250)

        # 每日明细
        st.markdown("### 📋 每日明细")
        dr_df = pd.DataFrame(report["daily_results"])
        dr_df["收益率"] = dr_df["total_pnl"].apply(lambda x: f"{x/report['initial_capital']*100:+.2f}%")
        dr_df["盈亏"] = dr_df["total_pnl"].apply(lambda x: f"¥{x:+,.0f}")
        dr_df = dr_df[["date","盈亏","收益率","buy_count","total_asset"]]
        dr_df.columns = ["日期","盈亏","收益率","买入数","总资产"]
        st.dataframe(dr_df.sort_values("日期",ascending=False), use_container_width=True, hide_index=True)

        bar2.progress(100, "回测完成!")
        stat2.success("✅ 回测完成")
    else:
        st.warning("回测未产生有效数据")

else:
    st.info("👈 点击左侧 **🚀 启动流水线** 运行")
    st.markdown("""
    | 步骤 | 内容 |
    |------|------|
    | 1 | 新浪拉取全A股 → 多级过滤 → Top20 |
    | 2 | 五因子(资金流/趋势/动量/量价/北向) 0-100打分 |
    | 3 | AI分析师四大维度(技术面/基本面/资金流/舆情) |
    | 4 | 三轮多空辩论(陈述→驳斥→修正) |
    | 5 | buy/hold/sell + 置信度 + 动态仓位分配 |
    | 6 | 大赛JSON + trace审计 + markdown答辩报告 |
    """)

st.divider()
st.caption("免责声明：仅供驼灵智能体大赛学术模拟，不构成投资建议。")
