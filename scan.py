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

NUM_RESULTS = 100          # 最大值
SLEEP_BETWEEN_KEYWORDS = 1.5
MAX_WORKERS = 30
TEST_TIMEOUT = 12

# 高价值站点（优先搜）
HIGH_VALUE_SITES = [
    "youtube.com",
    "bilibili.com",
    "tieba.baidu.com",
]

# 低价值社交平台（降低频率，避免浪费额度）
LOW_VALUE_SITES = [
    "facebook.com",
    "x.com",
    "twitter.com",
    "instagram.com",
    "xiaohongshu.com",
    "douyin.com",
    "tiktok.com",
]

KEYWORDS = [
    "sub.xjhsub1.top/api/v1/client/subscribe?token=",
    "subscription.sukiaira.com/api/v1/client/subscribe?token=",
    "times1733632330.subxiandan.top:9604/v2b/paopaogou/api/v1/client/subscribe?token=",
    "let.bnsubservdom.com/api/v1/client/subscribe?token=",
    "www.ccsub.org/link/",
    "api.flowercloud.xyz/osubscribe.php?sid=",
    "no7-svip.urlapi-dodo",
    "ierboryt.spphhnhg.top/link",
    "lmlla.lmscunb.pro:2087/api/v1/client/subscribe?token=",
    "api.oxycontinon.com/osubscribe.php?sid",
    "s.suying666.info/link/",
    "afun-waf.trafficmanager.net/api/v1/client/subscribe?token=",
    "www.starlinkstatic.cc",
    "ratchada.terminal69.win/api/v1/trails/bolster?token=",
    "submit.xz61.cn:23443/api/v1/client/subscribe?token=",
    "carpetpacific.com/blanket/api/v1/client/subscribe?token=",
    "0b96e976-9ec3-44c0-aa2b-30bf8b0792ea.com/api/v1/client/subscribe?token=",
    "no1-svip.urlapi-dodo.sbs/s?t=",
    "linksc.laoyao.ltd/api/v1/client/subscribe?token=",
    "times1746075059.subtangniu.top:9606/v2b/catnet/api/v1/client/subscribe?token=",
    "ierboryt.spphhnhg.top/link/",
    "fba01.fbsubcn01.cc:2096/flydsubal/4migrboppnogh8ia?",
    "fm-sub-mainpanel-vygijfogpm.cn-shanghai.fcapp.run/api/v1/client/subscribe?token=",
    "love-coffee.one/api/v1/client/subscribe?token=",
    "api.ytoo.xyz/osubscribe.php?sid=",
    "oymr1a9aua.todust.cc/",
    "ggbong.xyz/sub",
    "liangxin.xyz",
    "onlysub.mjurl.com",
    "clash=3",
    "dash.xn--cp3a08l.com",
    "msub.xn--m7r52rosihxm.com",
    "mojie.app",
    "mojie.co",
    "47.112.97.173:5000",
    "43.129.78.33:5000",
    "yuyun.mhlnf.cn",
    "s1.byte11.com",
    "dp3.config-sync.com",
    "147.45.60.162:8081/dazhutou",
    "clash=3&extend=1",
    "url.ktmcloud01.cc",
    "sub0530.wdyserver.com",
    "sub1.smallstrawberry.com",
    "sub2.smallstrawberry.com",
    "sub3.smallstrawberry.com",
    "dash.knjc.cfd",
    "sso.yuetoto.com",
    "dash.pqjc.site",
    "dp3.config-sync.com",
    "47.242.128.61:5000",
    "ymjc.cfd",
    "update.glados-config.com",
    "s1.byte77.com",
    "dy.boost1.shop",
    "nervixapp.top",
    "8.138.113.193",
    "sub=3&extend=1",
    "login.yfjc.xyz",
    "sf.342242.icu",
    "efanyunapi.com",
    "gates.djjc.cfd",
    "jsjc.cfd",
    "w.12.kg",
    "subscription-shortlink.pages.dev",
    "conf1.hokkaido-toyoni.com",
    "ktmcloud.id",
    "sub-1.smjcdh.top",
]

# ==================== 工具函数 ====================

def search_serper(query: str, num: int = 100, endpoint: str = "search") -> list[dict]:
    url = f"https://google.serper.dev/{endpoint}"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": min(num, 100)}  # 强制不超过100
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if endpoint == "videos":
            return data.get("videos", [])
        return data.get("organic", [])
    except Exception as e:
        print(f"[ERROR] 搜索失败: {e}")
        return []


def is_potential_sub_link(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    url_lower = url.lower()

    # 排除平台页面
    exclude = [
        "google.", "youtube.com/watch", "youtube.com/channel", "youtu.be",
        "facebook.com/", "fb.com/", "x.com/", "twitter.com/",
        "github.com", "stackoverflow", "wikipedia.", "microsoft.", "apple.com",
        "amazon.", "baidu.com/s", "zhihu.com", "bilibili.com/video",
        "qq.com", "taobao.", "xiaohongshu.com/explore", "douyin.com/video",
        "instagram.com/p/", "instagram.com/reel/", "tiktok.com/@",
        "tieba.baidu.com/p/", "tieba.baidu.com/f"
    ]
    if any(x in url_lower for x in exclude):
        return False

    positive = [
        "subscribe", "token=", "sid=", "/link/", "/s?", "osubscribe",
        "api/v1/client", "sub=", "clash", "v2ray", "vmess", "trojan",
        "getprofile", "sublink", "subscription", "suying", "flowercloud",
        "ytoo", "mojie", "glados", "xn--", ".cc/", ".top/", ".xyz/",
        ".cfd", ".sbs", ".run/", ".icu", ".info/", ".ltd", ".win/"
    ]
    if any(p in url_lower for p in positive):
        return True
    if len(url) > 65:
        return True
    return False


def extract_links_from_results(results: list[dict]) -> set[str]:
    links = set()
    url_pattern = re.compile(r'https?://[^\s<>"\'\)\]\}\{\|,\\\\]{10,600}')

    for item in results:
        link = item.get("link", "").strip()
        if link:
            clean = link.rstrip('.,;:!?)\'\"')
            if is_potential_sub_link(clean):
                links.add(clean)

        text = " ".join([
            item.get("title", ""),
            item.get("snippet", ""),
            item.get("link", ""),
            item.get("description", "")
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

    print(f"🚀 开始扫描，共 {len(KEYWORDS)} 个关键词（优化策略版）")
    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing).strftime("%Y-%m-%d %H:%M:%S")
    time_tag = datetime.now().strftime("%Y%m%d_%H%M")

    all_candidates = set()

    for idx, kw in enumerate(KEYWORDS, 1):
        print(f"\n[{idx}/{len(KEYWORDS)}] {kw}")
        found = set()

        # ===== 高价值搜索（必须跑）=====
        # 1. 普通搜索
        results = search_serper(kw, 100)
        found |= extract_links_from_results(results)

        # 2. 相关词搜索
        results = search_serper(f"{kw} (subscribe OR clash OR v2ray OR token OR 订阅)", 100)
        found |= extract_links_from_results(results)

        # 3. 精确短语（长关键词很有效）
        if len(kw) > 20:
            results = search_serper(f'"{kw}"', 100)
            found |= extract_links_from_results(results)

        # 4. YouTube 视频搜索
        results = search_serper(kw, 50, "videos")
        found |= extract_links_from_results(results)

        # 5. 高价值站点
        for site in HIGH_VALUE_SITES:
            results = search_serper(f"{kw} site:{site}", 100)
            found |= extract_links_from_results(results)
            time.sleep(0.3)

        # ===== 低价值社交平台（每 3 个关键词才跑一次，节省额度）=====
        if idx % 3 == 1:
            for site in LOW_VALUE_SITES:
                results = search_serper(f"{kw} site:{site}", 100)
                found |= extract_links_from_results(results)
                time.sleep(0.3)

        print(f"  本轮找到 {len(found)} 个候选")
        all_candidates.update(found)
        time.sleep(SLEEP_BETWEEN_KEYWORDS)

    all_candidates = sorted(all_candidates)
    print(f"\n📦 总共收集到 {len(all_candidates)} 个候选链接")

    # 发送完整候选
    full_filename = f"full_candidates_{time_tag}.txt"
    save_and_send(all_candidates, full_filename, f"📋 完整候选订阅列表\n时间: {now}\n数量: {len(all_candidates)}")

    if not all_candidates:
        return

    # 测活
    alive_links = batch_test(all_candidates)
    alive_links = sorted(set(alive_links))
    print(f"\n✅ 测活完成：存活 {len(alive_links)} / {len(all_candidates)}")

    # 发送存活列表
    alive_filename = f"alive_subs_{time_tag}.txt"
    save_and_send(alive_links, alive_filename, f"✅ 测活后存活订阅列表\n时间: {now}\n候选: {len(all_candidates)} | 存活: {len(alive_links)}")

    print("全部完成")


if __name__ == "__main__":
    main()
