# 账号资料加载器：号名、公众号名片 HTML、文首图床地址。
#
# 查找顺序：
#   1. 当前工作目录的 account_profile.json —— 装成插件时用这条：
#      资料属于用户自己的项目，不能放进插件目录（插件更新会被覆盖）。
#   2. 本脚本所在目录的 account_profile.json —— 克隆仓库当脚手架用时的兜底。
#
# 两处都没有就用中性占位符，转换流水线照常可用。
import json
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULTS = {
    "author": "公众号作者",
    "profile_card_html": "",  # 微信编辑器里复制的 mp-common-profile 名片 HTML，留空则文末不插名片
    "head_image_url": "",     # 文首占位图的微信图床地址，留空则不输出该图
}


def load():
    for base in (os.getcwd(), _SCRIPT_DIR):
        path = os.path.join(base, "account_profile.json")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            return {**_DEFAULTS, **data}
    return dict(_DEFAULTS)
