import os
import json
import re
from collections import defaultdict
from stock_data_fetcher import StockDataFetcher
import anthropic
import concurrent.futures

class EventRadarAgent:
    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.prompt_1_path = "prompt_1_extractor.md"
        self.prompt_2_path = "prompt_2_summarizer.md"
        self._init_llm_client()

    def _load_prompt(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到提示词文件: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _init_llm_client(self):
        # 兜底获取本地环境变量
        self.default_api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
            
        self.default_client = anthropic.Anthropic(
            base_url="https://api.minimaxi.com/anthropic",
            api_key=self.default_api_key
        )

    def call_llm(self, sys_prompt, user_msg, expect_json=False, client=None, model="MiniMax-M2.7"):
        """调用大模型，支持动态传入独立的 client 实例与模型控制参数"""
        use_client = client if client else self.default_client
        try:
            message = use_client.messages.create(
                model=model,
                max_tokens=4000,
                system=sys_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_msg}]
                    }
                ]
            )
            
            resp_text = ""
            for block in message.content:
                if block.type == "text":
                    resp_text += block.text
            
            if expect_json:
                # 提取 markdown 中的 json
                match = re.search(r'```json\s*(.*?)\s*```', resp_text, re.DOTALL)
                if match:
                    resp_text = match.group(1)
                return json.loads(resp_text)
            
            return resp_text
        except Exception as e:
            print(f"[LLM Error] 调用大模型异常: {e}")
            return None

    def layer1_build_map_prompts(self, symbol="603906", days_back=30):
        """
        第一层 (Map)：抓取大量官方公告全文，为每一篇公告单独生成 JSON 请求结构
        这里仅做结构组装，真实的 LLM 并发请求需要您接入真实的 API Key
        """
        print(f"==================================================")
        print(f"[阶段 1 - Map 层] 正在提取公告底稿并装配单篇抽提器...")
        print(f"目标股票: {symbol} | 回溯周期: 最近 {days_back} 天")
        print(f"==================================================\n")
        
        sys_prompt_1 = self._load_prompt(self.prompt_1_path)
        notices = self.fetcher.fetch_notice_list_em(symbol, days_back)
        if not notices:
            print("近期无任何官方公告发布。")
            return sys_prompt_1, []
            
        print(f"[Agent] 找到 {len(notices)} 篇公告，准备单篇提取逻辑...")
        
        map_requests = []
        for i, notice in enumerate(notices):
            try:
                # 抓取正文
                content = self.fetcher.fetch_notice_content(
                    art_code=notice['art_code'], 
                    title=notice['title'], 
                    notice_type=notice['type']
                )
                
                # 若正文非常简短且可能为重复发文可尝试做前置 Python 过滤，这里为保真度完全交给 LLM 标类
                user_msg = (
                    f"请基于以下公告抽取结构化卡片：\n"
                    f"【公告元数据】 日期: {notice['date']} | 类型: {notice['type']} | 标题: {notice['title']}\n"
                    f"【公告原文】:\n{content}\n"
                )
                
                # 记录请求
                map_requests.append({
                    "id": f"doc_{i+1}",
                    "title": notice['title'],
                    "sys_prompt": sys_prompt_1,
                    "user_msg": user_msg
                })
            except Exception as e:
                print(f"[Error] 组装 {notice['title']} 失败: {e}")
                continue
                
        return map_requests

    def layer2_cluster_cards(self, llm_json_results):
        """
        第二层 (Shuffle)：纯 Python 层逻辑。
        接收第一批大模型返回的百十来个 JSON 卡片（列表），将同属于一个事件 (event_key) 的篇章聚合
        并智能丢弃低价值的程序噪音。
        """
        print("\n[阶段 2 - Python Shuffle] 开始在外部环境自动降噪和事件簇重组...")
        clusters = defaultdict(list)
        
        for card in llm_json_results:
            # 数据清洗与降噪
            role = card.get('doc_role', '').lower()
            is_mat = card.get('is_material', False)
            
            # 过滤掉明显的杂音
            if role in ['noise', 'procedural'] and not is_mat:
                continue
                
            e_key = card.get('event_key', '未分类事项')
            clusters[e_key].append(card)
            
        # 整理输出最终的文本形式的聚类串，便于喂给最终提示词
        final_cluster_str = ""
        for e_key, cards in clusters.items():
            final_cluster_str += f"\n◆ 事件簇内核: 【{e_key}】 ◆\n"
            final_cluster_str += f"包含文档数: {len(cards)} 篇相关公告\n"
            
            for c in cards:
                role_tag = f"[{c.get('doc_role', 'unknown').upper()}]"
                final_cluster_str += (
                    f"  {role_tag} 日期: {c.get('date', '')} | 标题: {c.get('title', '')}\n"
                    f"    - 等级: {c.get('materiality', 'C')} | 影响路线: {c.get('impact_path', [])}\n"
                    f"    - 核心事实提取: {c.get('key_fact', '')}\n"
                    f"    - 关键数字与增量: {c.get('incremental_information', '')} (数据: {c.get('key_numbers', [])})\n"
                )
        return final_cluster_str

    def layer3_build_reduce_prompt(self, final_cluster_str):
        """
        第三层 (Reduce)：将浓缩后的事件簇喂给最高维度的专家总评模型
        """
        print("\n[阶段 3 - Reduce 层] 装配最终高管视角事件雷达简报 Request...")
        sys_prompt_2 = self._load_prompt(self.prompt_2_path)
        
        user_msg = (
            f"以下是经过前期信息浓缩和同类关联聚类后的【公司近 30 天核心事件簇列表】。\n"
            f"绝大多数例行公文与杂音已被过滤。请你通盘考量并出具《最终研判》：\n\n"
            f"<clustered_events>\n{final_cluster_str}\n</clustered_events>\n"
        )
        return sys_prompt_2, user_msg

    def run_analysis_pipeline(self, symbol="603906", days_back=30, custom_api_key=None, custom_model=None):
        """Web 后端或其他模块调用的标准入口，支持前端覆盖 API Key 和 底座模型"""
        # 如果存在前端传入的自定义 key，则实例化一个专属 client 给这个请求周期
        run_client = self.default_client
        target_model = custom_model if custom_model else "MiniMax-M2.7"
        
        if custom_api_key:
            run_client = anthropic.Anthropic(
                base_url="https://api.minimaxi.com/anthropic",
                api_key=custom_api_key
            )
            
        # 1. 构建底层抽取请求
        map_requests = self.layer1_build_map_prompts(symbol, days_back=days_back)
        if not map_requests:
            return "✅ 近期无任何官方公告发布或处理异常。"
        
        print(f"\n[阶段 1 - 请求] 正在向 MiniMax-M2.7 发起 {len(map_requests)} 个并发抽提请求...")
        mock_llm_responses = []
        
        # 使用线程池并发请求，大幅缩短单篇公告抽取的时间
        def worker(req):
            res = self.call_llm(req["sys_prompt"], req["user_msg"], expect_json=True, client=run_client, model=target_model)
            if res:
                res['title'] = req['title'] # 保底赋予 title 以防 json 内漏掉
                return res
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(worker, map_requests))
            
        for res in results:
            if res:
                mock_llm_responses.append(res)
        
        print(f"\n[阶段 1 - 完成] 成功结构化提取出 {len(mock_llm_responses)} 篇公告卡片！")
        
        # 3. 执行 Python 数据聚合层过滤
        cluster_text = self.layer2_cluster_cards(mock_llm_responses)
        
        # 4. 构建最终总结提词请求，并由大模型进行 Reduce 总评
        sys_p2, user_p2 = self.layer3_build_reduce_prompt(cluster_text)
        
        print(f"\n[阶段 3 - Reduce 调用] 正在向模型提交最终 {len(user_p2)} 个字符的事件簇...")
        final_report = self.call_llm(sys_p2, user_p2, expect_json=False, client=run_client, model=target_model)
        
        return final_report

if __name__ == "__main__":
    import sys
    agent = EventRadarAgent()
    symbol = sys.argv[1] if len(sys.argv) > 1 else "603906"
    
    # 检查环境变量
    if not os.environ.get("MINIMAX_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n[错误] 请先配置环境变量 MINIMAX_API_KEY 以驱动真实执行！")
        sys.exit(0)
        
    final_report = agent.run_analysis_pipeline(symbol, days_back=30)
    
    if final_report:
        # 保存结果展示给用户
        with open("final_report_output.md", "w", encoding="utf-8") as f:
            f.write("# 【事件雷达最终输出研报】\n\n")
            f.write(final_report)
            
        print(f"\n✅ 整个事件雷达流程已真实跑通！研报已保存至: final_report_output.md")
