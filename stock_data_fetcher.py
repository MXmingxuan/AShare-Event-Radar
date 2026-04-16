import akshare as ak
import pandas as pd
import requests
import re
from datetime import datetime, timedelta

class StockDataFetcher:
    """
    纯公告版事件雷达数据底座。专注于 A 股公告的全量抓取与财报核心（MD&A）截取。
    """

    @staticmethod
    def fetch_notice_list_em(symbol: str, days_back: int = 30) -> list:
        """
        抓取个股近期公告列表，提取核心字段及 art_code。
        :param symbol: 股票代码
        :param days_back: 回溯天数
        :return: 包含公告标题、类型、日期及 art_code 的字典列表
        """
        end_date = datetime.now().strftime("%Y%m%d")
        begin_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        
        try:
            notice_df = ak.stock_individual_notice_report(
                security=symbol, 
                symbol="全部", 
                begin_date=begin_date, 
                end_date=end_date
            )
            
            if notice_df.empty:
                return []
            
            results = []
            for _, row in notice_df.iterrows():
                url = row.get('网址', '')
                art_code_match = re.search(r'/(AN\d+)\.html', url)
                art_code = art_code_match.group(1) if art_code_match else None
                
                results.append({
                    "title": row.get("公告标题", ""),
                    "type": row.get("公告类型", ""),
                    "date": str(row.get("公告日期", "")).split()[0],
                    "art_code": art_code,
                    "url": url
                })
            return results
        except Exception as e:
            print(f"[Error] Fetching notice list failed: {e}")
            return []

    @staticmethod
    def _extract_mda(content: str) -> str:
        """
        利用正则从定期大额报告中提炼“管理层讨论与分析(MD&A)”章节。
        容错：若未匹配到标准章节，采用前 5000 字 Fallback。
        """
        content_cleaned = content.replace(" ", "").replace("　", "")
        
        # 常见 A 股财报 MD&A 章节标头匹配（如“第三节管理层讨论与分析”或“第四节经营情况讨论与分析”）
        # 寻找起点
        mda_start_pattern = r"(第[二三四五]节.*?管理层讨论与分析|第[二三四五]节.*?经营情况讨论与分析|一、.*管理层讨论与分析)"
        # 寻找终点（下一个常见章节一般为“重要事项”或“公司治理”）
        mda_end_pattern = r"(第[三四五六]节.*?公司治理|第[三四五六]节.*?重要事项|第[三四五六]节.*?环境与社会责任)"
        
        start_match = re.search(mda_start_pattern, content_cleaned)
        if start_match:
            start_idx = start_match.start()
            
            # 从起点之后的文本中寻找终点
            sub_content = content_cleaned[start_idx:]
            end_match = re.search(mda_end_pattern, sub_content[10:]) # 偏移10字符避免立刻匹配到异常
            
            if end_match:
                end_idx = start_idx + 10 + end_match.start()
                extracted = content_cleaned[start_idx:end_idx]
                return f"[✅ 成功提取 MD&A 章节 ({len(extracted)} 字)]\n" + content[start_match.start():start_match.start() + len(extracted)+500] 
                # 模糊切片恢复原始排版与空格
            else:
                # 找到起点但找不到标准终点，向后截取一定的核心安全字数
                return "[⚠️ 成功提取 MD&A 起点，安全向后截取]\n" + content[start_match.start() : start_match.start() + 10000]
        
        # Fallback 机制：如非标准大纲文本(极少数、或短长季报)，截取头部
        return "[⚠️ 未匹配到标准的 MD&A 章节段落，执行 Fallback 提取前 5000 字]\n" + content[:5000]

    @staticmethod
    def fetch_notice_content(art_code: str, title: str = "", notice_type: str = "") -> str:
        """
        请求底层 API 直接拉取公告全量原文本。针对财报自动路由至 MD&A 智能提取器。
        :param art_code: 公告 ID
        :param title: 用于协助判断是否为财报的标题
        :param notice_type: 公告的类型分类
        :return: 解析处理后的文本
        """
        url = "https://np-cnotice-stock.eastmoney.com/api/content/ann"
        params = {
            "art_code": art_code,
            "client_source": "web",
            "page_index": "1"
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://data.eastmoney.com/"
        }
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            
            text_resp = resp.text
            json_text = re.sub(r'^[^{]*({.*})[^}]*$', r'\1', text_resp, flags=re.DOTALL)
            
            import json
            data = json.loads(json_text)
            
            if "data" in data and "notice_content" in data["data"]:
                content = data["data"]["notice_content"]
                content = content.replace("\n\n", "\n").strip()
                
                # 判断是否为定期（财务）报告
                keywords = ["财报", "财务报告", "定期报告", "年报", "半年报", "季度报告"]
                is_report = "报告" in notice_type or any(k in title for k in keywords)
                
                if is_report:
                    return StockDataFetcher._extract_mda(content)
                else:
                    return "[全量完整抓取]\n" + content
            else:
                return "API 返回为空。"
        except Exception as e:
            print(f"[Error] Fetching notice content for {art_code} failed: {e}")
            return ""

if __name__ == "__main__":
    fetcher = StockDataFetcher()
    symbol = "600519"
    
    print(f"\\n正在获取 {symbol} 近期最新公告列表...")
    notices = fetcher.fetch_notice_list_em(symbol, days_back=60) 
    
    # 我们测试抓两篇：一篇普通公告，一篇定期报告 (如果有)
    normal_notice = None
    report_notice = None
    
    for n in notices:
        if not normal_notice and "报告" not in n['title']:
            normal_notice = n
        if not report_notice and ("半年报" in n['title'] or "季报" in n['title'] or "年报" in n['title'] or "年度报告" in n['title']):
            report_notice = n
    
    if normal_notice:
        print(f"\\n=== 测试 1: 普通公告全量提取 ===")
        print(f"【{normal_notice['type']}】 {normal_notice['title']}")
        text = fetcher.fetch_notice_content(normal_notice['art_code'], title=normal_notice['title'], notice_type=normal_notice['type'])
        print(text[:400] + "\\n...[展示截断]...")
        print(f"总抽提字数: {len(text)}")
        
    if report_notice:
        print(f"\\n=== 测试 2: 财报 MD&A 智能摘要 ===")
        print(f"【{report_notice['type']}】 {report_notice['title']}")
        text = fetcher.fetch_notice_content(report_notice['art_code'], title=report_notice['title'], notice_type=report_notice['type'])
        print(text[:400] + "\\n...[展示截断]...")
        print(f"总抽提字数: {len(text)}")
    elif notices:
        # 没有年报则借用其中某篇执行强制 report 测试
        fake_report = notices[0]
        print(f"\\n=== 测试 2: (模拟)强制按财报形式提取普通公告 ===")
        print(f"【{fake_report['type']}】 {fake_report['title']}")
        text = fetcher.fetch_notice_content(fake_report['art_code'], title="模拟年报", notice_type="定期报告")
        print(text[:400] + "\\n...[展示截断]...")
        print(f"总抽提字数: {len(text)}")
