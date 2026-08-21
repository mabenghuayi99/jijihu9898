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

def search_serper(query: str, num: int = 100) -> list[dict]:
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json().get("organic", [])
    except Exception as e:
        print(f"[ERROR] 搜索失败: {e}")
        return []


def is_potential_sub_link(url: str) -> bool:
    """判断是否像机场订阅链接"""
    url_lower = url.lower()
    # 排除明显无关的
    exclude = ["google.", "youtube.", "facebook.", "twitter.", "github.com", "stackoverflow",
               "wikipedia.", "microsoft.", "apple.com", "amazon.", "baidu.com", "zhihu.com"]
    if any(x in url_lower for x in exclude):
        return False

    # 订阅特征
    positive = [
        "subscribe", "token=", "sid=", "/link/", "/s?", "osubscribe",
        "api/v1/client", "sub=", "clash", "v2ray", "vmess", "trojan",
        ".txt", "getprofile", "sublink", "subscription"
    ]
    return any(p in url_lower for p in positive) or len(url) > 60


def extract_links_from_results(results: list[dict]) -> set[str]:
    """从搜索结果中尽可能多地提取潜在订阅链接"""
    links = set()
    url_pattern = re.compile(r'https?://[^\s<>"\'\)\]\}\{\|,]{15,400}')

    for item in results:
        # 1. 优先使用搜索结果自带的 link
        link = item.get("link", "").strip()
        if link and is_potential_sub_link(link):
            links.add(link.rstrip('.,;:!?)\'\"'))

        # 2. 从 title + snippet 里正则提取
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
        if len(text.strip()) > 100 and "error" not in text[:300] and "not found" not in text[:300]:
            return url, True, "可能存活"
        return url, False, "内容不像订阅"

    except requests.exceptions.Timeout:
        return url, False, "超时"
    except Exception as e:
        return url, False, str(e)[:40]


def batch_test(urls: list[str]) -> list[str]:
    alive = []
    print(f"  测活中（共 {len(urls)} 个）...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(is_alive, u): u for u in urls}
        for future in as_completed(futures):
            url, ok, reason = future.result()
            if ok:
                alive.append(url)
                print(f"    ✅ {url}")
            else:
                print(f"    ❌ {url[:75]}... ({reason})")
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
                print("✅ txt 文件已发送")
                return True
            print(f"[ERROR] 发送失败: {r.text}")
            return False
    except Exception as e:
        print(f"[ERROR] 发送异常: {e}")
        return False


# ==================== 主逻辑 ====================

def main():
    if not SERPER_API_KEY:
        print("❌ 缺少 SERPER_API_KEY")
        return

    print(f"🚀 开始扫描，共 {len(KEYWORDS)} 个关键词")
    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing).strftime("%Y-%m-%d %H:%M:%S")

    all_candidates = set()

    for idx, kw in enumerate(KEYWORDS, 1):
        print(f"\n[{idx}/{len(KEYWORDS)}] {kw}")

        # 策略1：直接搜关键词
        results1 = search_serper(kw, NUM_RESULTS)
        links1 = extract_links_from_results(results1)

        # 策略2：加相关词提高命中率
        results2 = search_serper(f"{kw} (subscribe OR clash OR v2ray OR token)", NUM_RESULTS)
        links2 = extract_links_from_results(results2)

        found = links1 | links2
        print(f"  本轮找到 {len(found)} 个候选")
        all_candidates.update(found)

        time.sleep(SLEEP_BETWEEN_KEYWORDS)

    print(f"\n📦 总共收集到 {len(all_candidates)} 个候选链接，开始测活...")

    if not all_candidates:
        with open("empty.txt", "w", encoding="utf-8") as f:
            f.write(f"扫描时间: {now}\n本次未找到任何候选链接。\n")
        send_txt_file("empty.txt", f"📡 扫描完成\n时间: {now}\n未找到链接")
        return

    alive_links = batch_test(list(all_candidates))
    alive_links = sorted(set(alive_links))

    print(f"\n✅ 存活链接数量: {len(alive_links)}")

    # 写文件
    filename = f"alive_subs_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"扫描时间: {now}\n")
        f.write(f"候选链接: {len(all_candidates)}\n")
        f.write(f"存活链接: {len(alive_links)}\n")
        f.write("=" * 60 + "\n\n")
        for link in alive_links:
            f.write(link + "\n")

    caption = f"📡 机场订阅扫描\n时间: {now}\n候选: {len(all_candidates)} | 存活: {len(alive_links)}"
    send_txt_file(filename, caption)

    try:
        os.remove(filename)
    except:
        pass

    print("完成")


if __name__ == "__main__":
    main()
