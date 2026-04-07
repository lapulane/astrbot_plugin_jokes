from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
import json
import random
import os

# ==================== IDE 提示 ====================
try:
    from astrbot.api import *
except ImportError:
    pass
# ================================================

class RandomJokes(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 插件根目录下的 jokes_data 文件夹路径
        self.data_dir = os.path.join(os.path.dirname(__file__), "data", "jokes_data")
        self.jokes = {}          # 缓存所有分类的烂梗
        self.categories = []     # 分类名称列表

    async def initialize(self):
        """插件启动时加载所有 JSON 文件"""
        await self.load_all_jokes()
        logger.info(f"随机烂梗插件已启动！共加载 {len(self.categories)} 个分类，{sum(len(v) for v in self.jokes.values())} 条烂梗")

    async def load_all_jokes(self):
        """加载 jokes_data 目录下所有 .json 文件"""
        if not os.path.exists(self.data_dir):
            logger.error("未找到 jokes_data 文件夹！")
            return

        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                category = filename.replace(".json", "")
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 兼容两种常见格式：纯字符串列表 或 [{"text": "..."}, ...]
                        if isinstance(data, list):
                            if data and isinstance(data[0], dict) and "text" in data[0]:
                                self.jokes[category] = [item["text"] for item in data]
                            else:
                                self.jokes[category] = data
                            self.categories.append(category)
                            logger.info(f"已加载分类 [{category}]：{len(self.jokes[category])} 条")
                except Exception as e:
                    logger.error(f"加载 {filename} 失败: {e}")

    @filter.command("烂梗")
    async def random_joke(self, event: AstrMessageEvent):
        """随机一条烂梗（可指定分类）"""
        if not self.jokes:
            yield event.plain_result("⚠️ 烂梗数据未加载，请检查插件文件夹结构")
            return

        # 支持 /烂梗 fk-player 这种指定分类
        args = event.message_str.strip().split()
        category = args[1] if len(args) > 1 else random.choice(self.categories)

        if category in self.jokes:
            joke = random.choice(self.jokes[category])
            cat_name = category.replace("fk-", "互骂-").replace("showtime", "整活")
            yield event.plain_result(f"🎲 【{cat_name}】烂梗\n\n{joke}\n\n发送 /烂梗 [分类] 再来一条")
        else:
            # 随机一个分类
            cat = random.choice(self.categories)
            joke = random.choice(self.jokes[cat])
            yield event.plain_result(f"🎲 随机烂梗\n\n{joke}\n\n可用分类：{'、'.join(self.categories[:6])}...")

    @filter.command("烂梗列表")
    async def list_categories(self, event: AstrMessageEvent):
        """显示所有分类"""
        cats = "\n".join([f"• {c}" for c in self.categories])
        yield event.plain_result(f"📋 当前支持的烂梗分类：\n\n{cats}\n\n使用方法：/烂梗 分类名")