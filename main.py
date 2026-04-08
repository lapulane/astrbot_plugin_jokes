from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import random
import os
from typing import Dict, List

CATEGORY_MAP = {
    "fk-wjq": "喷玩机器篇",
    "fk-eachother": "直播间互喷篇",
    "fk-player": "喷选手篇",
    "repeat": "+1篇",
    "showtime": "群魔乱舞篇",
    "ququ": "QUQU篇"
}

@register("astrbot_plugin_jokes", "lapulane", "纯脚本随机烂梗插件", "1.0.3")
class RandomJokes(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.jokes_data_dir = os.path.join(os.path.dirname(__file__), "jokes_data")
        self.jokes_cache: Dict[str, List[str]] = {}

    async def initialize(self):
        if not os.path.exists(self.jokes_data_dir):
            logger.error("❌ 未找到 jokes_data 文件夹")
            return

        json_files = [f for f in os.listdir(self.jokes_data_dir) if f.endswith(".json")]
        for file in json_files:
            category = os.path.splitext(file)[0]
            try:
                with open(os.path.join(self.jokes_data_dir, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.jokes_cache[category] = [str(item) for item in data if item]
                        logger.info(f"✅ 加载 [{CATEGORY_MAP.get(category, category)}] {len(data)} 条")
            except Exception as e:
                logger.error(f"加载 {file} 失败: {e}")

        logger.info(f"🚀 烂梗插件初始化完成，共 {len(self.jokes_cache)} 个分类")

    @filter.command("烂梗")
    @filter.command("随机烂梗")
    async def random_joke(self, event: AstrMessageEvent):
        """随机一条烂梗"""
        if not self.jokes_cache:
            yield event.plain_result("⚠️ 烂梗数据未加载，请检查 jokes_data 文件夹")
            return

        # 支持指定分类，例如：/烂梗 fk-player
        text = event.message_str.strip()
        parts = text.split(maxsplit=1)
        target = parts[1] if len(parts) > 1 else None

        if target and target in self.jokes_cache:
            category_key = target
        else:
            category_key = random.choice(list(self.jokes_cache.keys()))

        joke = random.choice(self.jokes_cache[category_key])
        cat_name = CATEGORY_MAP.get(category_key, category_key)

        yield event.plain_result(f"🎲 【{cat_name}】\n\n{joke}\n\n发送 /烂梗 再来一条～")

    @filter.command("烂梗列表")
    async def list_jokes(self, event: AstrMessageEvent):
        categories = "\n".join([f"• {k} ({v})" for k, v in CATEGORY_MAP.items()])
        yield event.plain_result(f"📋 可用烂梗分类：\n\n{categories}")