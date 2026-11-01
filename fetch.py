import os, io, requests
import xml.etree.ElementTree as ET
from PIL import Image

SAVE_DIR = "./archived"
XML_URL  = "http://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/SEC/xml/FY4B-china-72h.xml"
RESIZE_W = 1500          # 压缩到宽1500像素（约500KB/张）；None=存原图
MAX_NUM  = 10            # 每轮最多处理最新10张，已存在的自动跳过

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": "http://www.nsmc.org.cn/nsmc/cn/image/animation/FY4B_china.html",
}

os.makedirs(SAVE_DIR, exist_ok=True)

# 1. 获取云图清单
r = requests.get(XML_URL, headers=HEADERS, timeout=30)
r.raise_for_status()
root = ET.fromstring(r.content)

items = []
for el in root.iter("image"):
    u = el.get("url", "")
    if "-thumb" in u:
        continue
    if u.startswith("//"):
        u = "http:" + u
    items.append((el.get("time", ""), u))
print(f"清单共 {len(items)} 张", flush=True)

# 2. 下载最新若干张（已存在则跳过）
new_count = 0
for t, u in items[:MAX_NUM]:
    name = u.split("/")[-1]
    path = os.path.join(SAVE_DIR, name)
    if os.path.exists(path):
        continue
    try:
        ri = requests.get(u, headers=HEADERS, timeout=120)
        ri.raise_for_status()
        if RESIZE_W:
            img = Image.open(io.BytesIO(ri.content))
            w, h = img.size
            img = img.resize((RESIZE_W, int(h * RESIZE_W / w)))
            img.save(path, quality=90)
        else:
            with open(path, "wb") as f:
                f.write(ri.content)
        new_count += 1
        print(f"已保存 {name} ({t})", flush=True)
    except Exception as e:
        print("单张失败，下轮自动重试:", name, e, flush=True)

print(f"本轮新增 {new_count} 张，仓库累计 {len(os.listdir(SAVE_DIR))} 张", flush=True)
