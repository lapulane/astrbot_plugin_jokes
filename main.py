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
    "ququ": "QUQU篇",
    "CNCS": "群处篇"
}

@register("随机烂梗", "lapulane", "从json数组随机一条烂梗，支持提交烂梗", "1.1.0")
class RandomJokes(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.jokes_data_dir = os.path.join(os.path.dirname(__file__), "jokes_data")
        self.jokes_cache: Dict[str, List[str]] = {}

    async def initialize(self):
        if not os.path.exists(self.jokes_data_dir):
            os.makedirs(self.jokes_data_dir)
            logger.info("✅ 自动创建 jokes_data 文件夹")
        
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

    # --------------------- 随机烂梗 ---------------------
    @filter.command("随机烂梗")
    async def random_joke(self, event: AstrMessageEvent):
        if not self.jokes_cache:
            yield event.plain_result("⚠️ 暂无烂梗数据")
            return

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

    # --------------------- 烂梗列表 ---------------------
    @filter.command("烂梗列表")
    async def list_jokes(self, event: AstrMessageEvent):
        if not self.jokes_cache:
            yield event.plain_result("⚠️ 暂无烂梗分类数据")
            return
        clist = "\n".join([f"- {v}" for v in CATEGORY_MAP.values()])
        yield event.plain_result(f"📋 可用烂梗分类：\n{clist}\n\n使用示例：\n/随机烂梗 QUQU篇\n/提交烂梗 QUQU篇 这是提交的烂梗内容")

    # --------------------- ✅ 新增：提交烂梗 ---------------------
    @filter.command("提交烂梗")
    async def add_joke(self, event: AstrMessageEvent):
        text = event.get_message_str().strip()
        parts = text.split(maxsplit=2)
        
        # 格式校验
        if len(parts) < 3:
            yield event.plain_result("⚠️ 格式错误！\n使用方法：/提交烂梗 分类名 烂梗内容")
            return

        _, target_category, content = parts
        content = content.strip()
        
        if not content:
            yield event.plain_result("⚠️ 烂梗内容不能为空！")
            return

        # 匹配分类（支持中文分类名）
        category_key = next((k for k, v in CATEGORY_MAP.items() if v == target_category), None)
        if not category_key:
            category_key = target_category if target_category in self.jokes_cache else None

        if not category_key:
            clist = "\n".join([f"- {v}" for v in CATEGORY_MAP.values()])
            yield event.plain_result(f"⚠️ 分类「{target_category}」不存在！\n可用分类：\n{clist}")
            return

        # 去重判断
        if content in self.jokes_cache[category_key]:
            yield event.plain_result(f"✅ 该烂梗已存在于「{CATEGORY_MAP[category_key]}」，无需重复提交~")
            return

        # 写入缓存
        self.jokes_cache[category_key].append(content)

        # 写入文件
        file_path = os.path.join(self.jokes_data_dir, f"{category_key}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.jokes_cache[category_key], f, ensure_ascii=False, indent=2)
            
            show_name = CATEGORY_MAP[category_key]
            yield event.plain_result(f"✅ 提交成功！\n分类：{show_name}\n内容：{content}\n当前分类共有 {len(self.jokes_cache[category_key])} 条烂梗")
            logger.info(f"📝 用户提交烂梗：{category_key} - {content}")
        
        except Exception as e:
            yield event.plain_result(f"❌ 保存失败：{str(e)}")
            # 回滚缓存
            self.jokes_cache[category_key].pop()

    async def terminate(self):
        self.jokes_cache.clear()
        logger.info("✅ 烂梗插件已卸载")