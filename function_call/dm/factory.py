from typing import Text

from dm import weather

from dm import music

from dm import time


PARSER_MAPPING = {

    "weather": weather,

    "time": time,

    "music": music,
    "play_music": music

}


class DMFactory:

    "根据工具名称创建对话管理器。"


    @staticmethod

    def get(name: Text):


        if name in PARSER_MAPPING:

            return PARSER_MAPPING[name].process

        else:

            return None
