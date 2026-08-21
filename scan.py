#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

# ==================== 配置 ====================
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NUM_RESULTS = 100
SLEEP_BETWEEN_KEYWORDS = 1.5
MAX_WORKERS = 30
TEST_TIMEOUT = 12

# ==================== 终极版关键词 ====================
KEYWORDS = [
    # ==================== 核心订阅路径（最高优先级） ====================
    "/api/v1/client/subscribe?token=",
    "/api/v1/client/subscribe?token",
    "osubscribe.php?sid=",
    "subscribe?token=",
    "sub?token=",
    "/link/",
    "/api/v1/client/subscribe",
    "/s?",
    "api/v1/ss/",
    "/sub/",
    "/api/v1/liangxin",
    "/api/v1/chuixue",
    "token=",
    "sid=",
    "clash=1",
    "clash=2",
    "clash=3",
    "sub=1",
    "sub=2",
    "sub=3",
    "extend=1",

    # ==================== 高频机场域名 / 特征 ====================
    "sub.xjhsub",
    "suying666",
    "flowercloud",
    "ytoo.xyz",
    "mojie",
    "glados-config",
    "ktmcloud",
    "smallstrawberry",
    "config-sync.com",
    "subtangniu",
    "subxiandan",
    "bnsubservdom",
    "starlinkstatic",
    "urlapi-dodo",
    "xn--cp3a08l.com",
    "xn--m7r52rosihxm.com",
    "ccsub.org",
    "spphhnhg.top",
    "lmscunb.pro",
    "oxycontinon.com",
    "trafficmanager.net",
    "terminal69.win",
    "xz61.cn",
    "carpetpacific.com",
    "laoyao.ltd",
    "fbsubcn01.cc",
    "fcapp.run",
    "love-coffee.one",
    "todust.cc",
    "ggbong.xyz",
    "liangxin.xyz",
    "onlysub.mjurl.com",
    "byte11.com",
    "byte77.com",
    "byte33.com",
    "wdyserver.com",
    "yuetoto.com",
    "knjc.cfd",
    "pqjc.site",
    "ymjc.cfd",
    "djjc.cfd",
    "jsjc.cfd",
    "yfjc.xyz",
    "342242.icu",
    "efanyunapi.com",
    "hokkaido-toyoni.com",
    "smjcdh.top",
    "nervixapp.top",
    "boost1.shop",
    "nydy.cc",
    "22na.cn",
    "flybit",
    "sealosgzg.site",
    "cocoduck.cc",
    "cdc502.online",
    "cd520.xyz",
    "cd1314.xyz",
    "xnyun.wiki",
    "skygo0527.top",
    "onlineweb.work",
    "nextport.top",
    "bakapie.cf",
    "ermao.net",
    "fastestcloud",
    "v2ny.com",
    "99ba2026",
    "waimaosass.icu",
    "wjkc.xyz",
    "sub987.top",
    "kuaidog005.top",
    "jichang.123417.xyz",
    "spwvpn.com",
    "wenliansub.com",
    "elephant223.com",
    "a335.sbs",
    "1bbbaf.one",
    "bafang",
    "ikuuu",
    "mojie.me",
    "dyljstar.sbs",
    "kuke-sub.com",
    "xlajiao.xyz",
    "mzyglc.xyz",
    "acyunsa.sbs",
    "ttyun.eu.org",
    "windowsv1.com",
    "xn--9kqs1lo79d.cc",
    "louwangzhiyu.org",
    "kuaivpn.app",
    "beifengyuns.top",
    "ppacc.cc",
    "ssr.sh",
    "ga-sub.hair",
    "f2vip.net",
    "ccwu.cc",
    "fn0618.xyz",
    "pokelink",
    "neteasegames.site",
    "xlajiao",
    "acyun",
    "ttyun",
    "beifengyun",
    "qijia",
    "7jia",
    "chuixue",
    "liangxin",
    "mzyglc",
    "kuke-sub",
    "ss88",
    "appurl.ppacc",
    "suba.f2vip",
    "s1.byte",
    "sub2.smallstrawberry",
    "sub1.smallstrawberry",
    "sub3.smallstrawberry",
    "47.242.128.61",
    "47.76.155.27",
    "139.196.241.76",
    "38.175.196.72",

    # ==================== 中文高召回 + 精准词 ====================
    "机场 订阅链接",
    "机场订阅 token",
    "clash 机场 订阅",
    "v2ray 机场 订阅",
    "免费机场 订阅",
    "白嫖机场 订阅",
    "机场面板 订阅",
    "机场 订阅地址",
    "机场 订阅链接 分享",
    "v2board 订阅",
    "机场 token 订阅",
    "免费机场 token",
    "白嫖机场 链接",
    "机场订阅 分享",
    "轻语机场",
    "美汁源 机场",
    "良心云 订阅",
    "机场 订阅",
    "白嫖机场",
    "免费机场 链接",
    "机场分享 订阅",
    "机场节点 订阅",
    "v2board 机场",
    "面板订阅 链接",
    "token 订阅 机场",
    "sid 订阅 机场",
    "clash订阅 机场",
    "机场 免费订阅",
    "试用机场 订阅",
    "机场 订阅地址 分享",
]

# ==================== 工具函数 ====================

def search_serper(query: str, num: int = 100) -> list[dict]:
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    clean_query = query.strip()
    payload = {"q": clean_query, "num": num}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 400:
            print(f"[ERROR] 400 Bad Request → 查询被拒绝: {clean_query[:80]}")
            return []
        resp.raise_for_status()
        return resp.json().get("organic", [])
    except Exception as e:
        print(f"[ERROR] 搜索失败 [{clean_query[:50]}]: {e}")
        return []


def is_potential_sub_link(url: str) -> bool:
    if not url.startswith("http"):
        return False
    url_lower = url.lower()

    exclude = [
        "google.", "youtube.", "facebook.", "twitter.", "x.com", "github.com",
        "stackoverflow", "wikipedia.", "microsoft.", "apple.com", "amazon.",
        "baidu.com", "zhihu.com", "bilibili.", "weixin.", "qq.com", "taobao.",
        "reddit.com", "medium.com"
    ]
    if any(x in url_lower for x in exclude):
        return False

    positive = [
        "subscribe", "token=", "sid=", "/link/", "/s?", "osubscribe",
        "api/v1/client", "sub=", "clash", "v2ray", "vmess", "trojan",
        "getprofile", "sublink", "subscription", "suying", "flowercloud",
        "ytoo", "mojie", "glados", "xn--", ".cc/", ".top/", ".xyz/",
        ".cfd", ".sbs", ".run/", ".icu", ".info/", ".ltd", ".win/",
        "nydy", "22na", "flybit", "cocoduck", "cdc502", "cd520",
        "xnyun", "skygo", "nextport", "bakapie", "ermao", "v2ny",
        "wjkc", "sub987", "kuaidog", "spwvpn", "wenlian", "elephant",
        "bafang", "ikuuu", "dyljstar", "kuke-sub", "xlajiao", "mzyglc",
        "acyunsa", "ttyun", "windowsv1", "louwangzhiyu", "kuaivpn",
        "beifengyuns", "ppacc", "ssr.sh", "ga-sub", "f2vip", "fn0618",
        "pokelink", "neteasegames", "liangxin", "chuixue"
    ]
    if any(p in url_lower for p in positive):
        return True

    if len(url) > 70:
        return True

    return False


def extract_links_from_results(results: list[dict]) -> set[str]:
    links = set()
    url_pattern = re.compile(r'https?://[^\s<>"\'\)\]\}\{\|,\\\\]{12,500}')

    for item in results:
        link = item.get("link", "").strip()
        if link:
            clean = link.rstrip('.,;:!?)\'\"')
            if is_potential_sub_link(clean):
                links.add(clean)

        text = " ".join([
            item.get("title", ""),
            item.get("snippet", ""),
            item.get("link", "")
        ])
        for m in url_pattern.findall(text):
            clean = m.rstrip('.,;:!?)\'\"')
            if is_potential_sub_link(clean):
                links.add(clean)

    return links


def is_alive(url: str) -> tuple[str, bool, str]:
    headers = {
        "User-Agent": "ClashforWindows/0.20.39",
        "Accept": "*/*",
    }
    try:
        r = requests.get(url, headers=headers, timeout=TEST_TIMEOUT, allow_redirects=True, stream=True)
        if r.status_code != 200:
            return url, False, f"HTTP {r.status_code}"

        content = b""
        for chunk in r.iter_content(1024):
            content += chunk
            if len(content) >= 4096:
                break

        text = content.decode("utf-8", errors="ignore").lower()

        signs = [
            "proxies:", "proxy-groups:", "rules:", "port:", "socks-port:",
            "vmess://", "vless://", "trojan://", "ss://", "ssr://", "hysteria",
            "uuid", "cipher:", "password:", "network:", "ws-opts", "grpc-opts",
            "server:", "tls:", "reality", "flow:", "client-fingerprint"
        ]
        if any(s in text for s in signs):
            return url, True, "存活"
        if len(text.strip()) > 120 and "error" not in text[:400] and "not found" not in text[:400]:
            return url, True, "可能存活"
        return url, False, "内容不像订阅"

    except requests.exceptions.Timeout:
        return url, False, "超时"
    except Exception as e:
        return url, False, str(e)[:40]


def batch_test(urls: list[str]) -> list[str]:
    alive = []
    print(f"  开始测活，共 {len(urls)} 个链接...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(is_alive, u): u for u in urls}
        for future in as_completed(futures):
            url, ok, reason = future.result()
            if ok:
                alive.append(url)
                print(f"    ✅ {url}")
            else:
                print(f"    ❌ {url[:80]}... ({reason})")
    return alive


def send_txt_file(file_path: str, caption: str = "") -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] 未配置 Telegram")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": (os.path.basename(file_path), f)}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1000]}
            r = requests.post(url, data=data, files=files, timeout=60)
            if r.status_code == 200:
                print(f"✅ 已发送: {os.path.basename(file_path)}")
                return True
            print(f"[ERROR] 发送失败: {r.text}")
            return False
    except Exception as e:
        print(f"[ERROR] 发送异常: {e}")
        return False


def save_and_send(links: list[str], filename: str, caption: str):
    with open(filename, "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")
    send_txt_file(filename, caption)
    try:
        os.remove(filename)
    except:
        pass


# ==================== 主逻辑 ====================

def main():
    if not SERPER_API_KEY:
        print("❌ 缺少 SERPER_API_KEY")
        return

    print(f"🚀 开始扫描，共 {len(KEYWORDS)} 个关键词（终极关键词版）")
    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing).strftime("%Y-%m-%d %H:%M:%S")
    time_tag = datetime.now().strftime("%Y%m%d_%H%M")

    all_candidates = set()

    for idx, kw in enumerate(KEYWORDS, 1):
        print(f"\n[{idx}/{len(KEYWORDS)}] {kw}")

        results1 = search_serper(kw, NUM_RESULTS)
        links1 = extract_links_from_results(results1)

        results2 = search_serper(f"{kw} 订阅", NUM_RESULTS)
        links2 = extract_links_from_results(results2)

        results3 = search_serper(f"{kw} token OR sid", NUM_RESULTS)
        links3 = extract_links_from_results(results3)

        found = links1 | links2 | links3
        print(f"  本轮找到 {len(found)} 个候选")
        all_candidates.update(found)

        time.sleep(SLEEP_BETWEEN_KEYWORDS)

    all_candidates = sorted(all_candidates)
    print(f"\n📦 总共收集到 {len(all_candidates)} 个候选链接")

    full_filename = f"full_candidates_{time_tag}.txt"
    caption_full = (
        f"📋 完整候选机场订阅列表（终极关键词版）\n"
        f"时间: {now}\n"
        f"数量: {len(all_candidates)}"
    )
    save_and_send(all_candidates, full_filename, caption_full)

    if not all_candidates:
        print("没有候选链接，结束")
        return

    alive_links = batch_test(all_candidates)
    alive_links = sorted(set(alive_links))
    print(f"\n✅ 测活完成：存活 {len(alive_links)} / {len(all_candidates)}")

    alive_filename = f"alive_subs_{time_tag}.txt"
    caption_alive = (
        f"✅ 测活后存活机场订阅列表（终极关键词版）\n"
        f"时间: {now}\n"
        f"候选: {len(all_candidates)} | 存活: {len(alive_links)}"
    )
    save_and_send(alive_links, alive_filename, caption_alive)

    print("全部完成，两个文件都已发送")


if __name__ == "__main__":
    main()
