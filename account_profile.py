# 账号资料加载器：真实号名、公众号资料卡放在根目录 account_profile.json（已 gitignore，不进仓库）。
# 没有该文件时使用通用占位符，转换/同步流水线照常可用；使用者克隆本仓库后按 README 填自己的资料。
import json
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
_DEFAULTS = {
    "author": "公众号作者",
    "profile_card_html": "",  # 微信编辑器里复制的 mp-common-profile 名片 HTML，留空则文末不插名片
    "head_image_url": "",     # 文首占位图的微信图床地址，留空则不输出该图
}


def load():
    path = os.path.join(_ROOT, "account_profile.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return dict(_DEFAULTS)
    return {**_DEFAULTS, **data}
