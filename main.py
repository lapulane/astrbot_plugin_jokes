from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
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
    "repeat": "\"+1\"篇",
    "showtime": "群魔乱舞篇",
    "ququ": "QUQU篇"
}

@register("随机烂梗", "lapulane", "从json数组随机一条烂梗", "1.0.1")
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
        load_success = 0
        for file in json_files:
            file_path = os.path.join(self.jokes_data_dir, file)
            category = os.path.splitext(file)[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and all(isinstance(item, str) for item in data):
                        self.jokes_cache[category] = data
                        load_success += 1
            except Exception as e:
                logger.error(f"❌ 加载失败 {category}: {e}")
        logger.info(f"🚀 加载完成 {load_success} 个分类，共 {sum(len(v) for v in self.jokes_cache.values())} 条烂梗")

    # --------------------- 最终完美修复 ---------------------
    @filter.command("烂梗")
    async def random_joke(self, event: AstrMessageEvent):
        if not self.jokes_cache:
            yield event.plain_result("⚠️ 暂无烂梗数据")
            return

        # ✅ 完美！QQ 官方适配器正确 API：get_message_str()
        text = event.get_message_str().strip()
        parts = text.split(maxsplit=1)
        target_category = parts[1] if len(parts) >= 2 else None

        if target_category:
            category_key = next((k for k, v in CATEGORY_MAP.items() if v == target_category), None)
            if not category_key:
                category_key = target_category if target_category in self.jokes_cache else None
            if not category_key:
                clist = "\n".join([f"- {v}" for v in CATEGORY_MAP.values()])
                yield event.plain_result(f"⚠️ 未找到分类「{target_category}」\n可用分类：\n{clist}")
                return
            joke = random.choice(self.jokes_cache[category_key])
            yield event.plain_result(f"🎲 随机烂梗[{CATEGORY_MAP.get(category_key, category_key)}]\n\n{joke}")
        else:
            category_key = random.choice(list(self.jokes_cache.keys()))
            joke = random.choice(self.jokes_cache[category_key])
            yield event.plain_result(f"🎲 随机烂梗[{CATEGORY_MAP.get(category_key, category_key)}]\n\n{joke}")

    @filter.command("烂梗列表")
    async def list_jokes(self, event: AstrMessageEvent):
        if not self.jokes_cache:
            yield event.plain_result("⚠️ 暂无烂梗分类数据")
            return
        clist = "\n".join([f"- {v}" for v in CATEGORY_MAP.values()])
        yield event.plain_result(f"📋 可用烂梗分类：\n{clist}\n\n使用方法：发送「/烂梗 分类名」获取指定分类的烂梗")

    async def terminate(self):
        self.jokes_cache.clear()
        logger.info("✅ 烂梗插件已卸载")