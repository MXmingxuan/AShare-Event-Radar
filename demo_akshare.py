import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def get_stock_data(symbol="600519", days_back=30):
    print(f"==========================================")
    print(f"正在获取股票代码 {symbol} 的数据分析...")
    print(f"==========================================\n")
    
    # 1. 获取近期个股新闻
    print(">>> 1. 抓取东方财富个股新闻 (ak.stock_news_em)")
    try:
        news_df = ak.stock_news_em(symbol=symbol)
        if not news_df.empty:
            # 只取前 5 条展示
            recent_news = news_df.head(5)
            print(f"成功获取 {len(news_df)} 条新闻数据，展示前 5 条：")
            for idx, row in recent_news.iterrows():
                print(f"  时间: {row['发布时间']}")
                print(f"  标题: {row['新闻标题']}")
                text_snippet = str(row['新闻内容']).replace('\n', ' ').replace('\r', '')[:80] + "..." if '新闻内容' in row else "无内容"
                print(f"  正文: {text_snippet}")
                print("-" * 50)
        else:
            print("未获取到新闻数据。")
    except Exception as e:
        print(f"新闻获取失败: {e}")

    print("\n>>> 2. 抓取东方财富个股公告 (ak.stock_individual_notice_report)")
    # 计算日期
    end_date = datetime.now().strftime("%Y%m%d")
    begin_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
    try:
        notice_df = ak.stock_individual_notice_report(
            security=symbol, 
            symbol="全部", 
            begin_date=begin_date, 
            end_date=end_date
        )
        if not notice_df.empty:
            print(f"成功获取 {begin_date} 到 {end_date} 期间 {len(notice_df)} 条公告，展示前 5 条：")
            for idx, row in notice_df.head(5).iterrows():
                print(f"  日期: {row['公告日期']}")
                print(f"  标题: {row['公告标题']}")
                print(f"  类型: {row['公告类型']}")
                print("-" * 50)
        else:
            print(f"近期 ({begin_date} - {end_date}) 无公告发布。")
    except Exception as e:
        print(f"公告获取失败: {e}")

if __name__ == "__main__":
    # 以贵州茅台为例进行测试
    get_stock_data("600519", days_back=90)
