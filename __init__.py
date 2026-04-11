from astrbot.api import Plugin

class RandomJokes(Plugin):
    def __init__(self):
        super().__init__()
        self.metadata = ...
    
    async def on_load(self):
        ...

# 这里绝对不能写 __plugin__ = RandomJokes()