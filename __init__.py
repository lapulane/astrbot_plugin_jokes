# 这是 AstrBot 插件必须的 __init__.py 配置文件
from .main import RandomJokes

# 导出插件类（框架靠这个找到你的插件）
__plugin__ = RandomJokes