from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import json
import random
import os
from typing import Dict, List

# 完全对应tab.ts的分类名映射（中文分类名+JSON文件名对应）
CATEGORY_MAP = {
    "fk-wjq": "喷玩机器篇",
    "fk-eachother": "直播间互喷篇",
    "fk-player": "喷选手篇",
    "repeat": "\"+1\"篇",
    "showtime": "群魔乱舞篇",
    "ququ": "QUQU篇"
}

@register("随机烂梗", "你的名字", "从json数组随机一条烂梗", "1.0.1")
class RandomJokes(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 插件根目录下的jokes_data文件夹（和GitHub数据目录对应）
        self.jokes_data_dir = os.path.join(os.path.dirname(__file__), "jokes_data")
        # 内存缓存：key=分类名，value=梗列表
        self.jokes_cache: Dict[str, List[str]] = {}

    async def initialize(self):
        """插件启动时：预加载所有JSON到内存，避免每次读磁盘"""
        if not os.path.exists(self.jokes_data_dir):
            logger.error("❌ 未找到 jokes_data 文件夹，请检查插件目录结构")
            return

        # 遍历所有JSON文件，预加载到缓存
        json_files = [f for f in os.listdir(self.jokes_data_dir) if f.endswith(".json")]
        if not json_files:
            logger.warning("⚠️ jokes_data 文件夹下无JSON数据文件")
            return

        load_success = 0
        for file in json_files:
            file_path = os.path.join(self.jokes_data_dir, file)
            category = os.path.splitext(file)[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 校验数据格式：必须是字符串数组
                    if isinstance(data, list) and all(isinstance(item, str) for item in data):
                        self.jokes_cache[category] = data
                        load_success += 1
                        logger.info(f"✅ 加载分类 [{CATEGORY_MAP.get(category, category)}] 成功，共 {len(data)} 条梗")
                    else:
                        logger.error(f"❌ 分类 [{category}] JSON格式错误：必须是字符串数组")
            except json.JSONDecodeError:
                logger.error(f"❌ 分类 [{category}] JSON解析失败，请检查文件格式")
            except Exception as e:
                logger.error(f"❌ 加载分类 [{category}] 失败：{str(e)}")

        logger.info(f"🚀 烂梗插件初始化完成，成功加载 {load_success} 个分类，共 {sum(len(v) for v in self.jokes_cache.values())} 条烂梗")

    @filter.command("随机烂梗")
    async def random_joke(self, event: AstrMessageEvent):
        """随机一条烂梗（支持指定分类，不指定则全部分类随机）"""
        # 检查缓存是否为空
        if not self.jokes_cache:
            yield event.plain_result("⚠️ 暂无烂梗数据，请检查 jokes_data 文件夹")
            return

        # 支持指令：/烂梗 分类名（比如 /烂梗 QUQU篇）
        msg = event.get_message().content.strip().split()
        target_category = msg[1] if len(msg) > 1 else None

        # 处理分类查询
        if target_category:
            # 支持中文分类名/英文文件名两种输入
            # 先找中文分类名对应的key
            category_key = next((k for k, v in CATEGORY_MAP.items() if v == target_category), None)
            # 没找到就直接用输入当key（兼容英文文件名）
            if not category_key:
                category_key = target_category if target_category in self.jokes_cache else None

            if not category_key:
                # 分类不存在，提示可用分类
                category_list = "\n".join([f"- {v}" for v in CATEGORY_MAP.values()])
                yield event.plain_result(f"⚠️ 未找到分类「{target_category}」\n可用分类：\n{category_list}")
                return

            # 从指定分类随机
            joke = random.choice(self.jokes_cache[category_key])
            category_name = CATEGORY_MAP.get(category_key, category_key)
            yield event.plain_result(f"🎲 随机烂梗[{category_name}]\n\n{joke}")
        else:
            # 全部分类随机
            category_key = random.choice(list(self.jokes_cache.keys()))
            joke = random.choice(self.jokes_cache[category_key])
            category_name = CATEGORY_MAP.get(category_key, category_key)
            yield event.plain_result(f"🎲 随机烂梗[{category_name}]\n\n{joke}")

    @filter.command("烂梗列表")
    async def list_jokes(self, event: AstrMessageEvent):
        """查看所有可用分类（完全对应tab.ts的中文分类名）"""
        if not self.jokes_cache:
            yield event.plain_result("⚠️ 暂无烂梗分类数据")
            return

        # 按tab.ts的顺序输出分类
        category_list = "\n".join([f"- {v}" for v in CATEGORY_MAP.values() if v in CATEGORY_MAP.values()])
        yield event.plain_result(f"📋 可用烂梗分类（共 {len(self.jokes_cache)} 个）：\n{category_list}\n\n使用方法：发送「烂梗 分类名」获取指定分类的烂梗")

    async def terminate(self):
        """插件卸载时清空缓存"""
        self.jokes_cache.clear()
        logger.info("✅ 烂梗插件已卸载，缓存已清空")