#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from pathlib import Path

# ==================== 配置 ====================
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NUM_RESULTS = 100
SLEEP_BETWEEN_KEYWORDS = 1.5
MAX_WORKERS = 30
TEST_TIMEOUT = 12

SEEDS_FILE = "seeds_domains.txt"

# ==================== 关键词（代码内硬编码，一定会执行） ====================
KEYWORDS = [
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
    "试用机场 订阅",
    "机场 免费订阅",
]

# ==================== 真实订阅域名最终完整种子 ====================
INITIAL_SEEDS = [
    # 核心高频
    "nydy.cc", "22na.cn", "fb.22na.cn", "sealosgzg.site", "sub.cocoduck.cc",
    "cdc502.online", "xnyun.wiki", "skygo0527.top", "onlineweb.work", "nextport.top",
    "bakapie.cf", "ermao.net", "fastestcloud.xyz", "kuaidog005.top", "jichang.123417.xyz",
    "spwvpn.com", "wenliansub.com", "elephant223.com", "a335.sbs", "1bbbaf.one",
    "dyljstar.sbs", "kuke-sub.com", "xlajiao.xyz", "mzyglc.xyz", "acyunsa.sbs",
    "ttyun.eu.org", "windowsv1.com", "xn--9kqs1lo79d.cc", "louwangzhiyu.org",
    "kuaivpn.app", "beifengyuns.top", "ppacc.cc", "ssr.sh", "ga-sub.hair",
    "f2vip.net", "suba.f2vip.net", "ccwu.cc", "fn0618.xyz", "pokelink.xn--4gsvmh74cwxi.cn",
    "neteasegames.site", "smallstrawberry.com", "sub1.smallstrawberry.com",
    "sub2.smallstrawberry.com", "sub3.smallstrawberry.com", "liangxin.xyz", "ytoo.xyz",
    "suying666.info", "flowercloud.xyz", "ktmcloud.id", "glados-config.com",
    "byte11.com", "byte33.com", "byte77.com", "wdyserver.com", "config-sync.com",
    "starlinkstatic.cc", "urlapi-dodo.sbs", "ccsub.org", "spphhnhg.top", "lmscunb.pro",
    "oxycontinon.com", "terminal69.win", "xz61.cn", "carpetpacific.com", "laoyao.ltd",
    "fbsubcn01.cc", "fcapp.run", "love-coffee.one", "todust.cc", "ggbong.xyz",
    "onlysub.mjurl.com", "yuetoto.com", "knjc.cfd", "pqjc.site", "ymjc.cfd",
    "djjc.cfd", "jsjc.cfd", "yfjc.xyz", "342242.icu", "efanyunapi.com",
    "hokkaido-toyoni.com", "smjcdh.top", "nervixapp.top", "boost1.shop",

    # 一二三线 + 低中高端
    "sub.xjhsub1.top", "subscription.sukiaira.com", "let.bnsubservdom.com",
    "api.flowercloud.xyz", "api.oxycontinon.com", "s.suying666.info",
    "afun-waf.trafficmanager.net", "ratchada.terminal69.win", "submit.xz61.cn",
    "linksc.laoyao.ltd", "fba01.fbsubcn01.cc",
    "fm-sub-mainpanel-vygijfogpm.cn-shanghai.fcapp.run", "oymr1a9aua.todust.cc",
    "dash.xn--cp3a08l.com", "msub.xn--m7r52rosihxm.com", "s1.byte11.com",
    "s1.byte77.com", "dp3.config-sync.com", "update.glados-config.com",
    "dy.boost1.shop", "sub0530.wdyserver.com", "dash.knjc.cfd", "sso.yuetoto.com",
    "dash.pqjc.site", "login.yfjc.xyz", "sf.342242.icu", "gates.djjc.cfd",
    "w.12.kg", "subscription-shortlink.pages.dev", "conf1.hokkaido-toyoni.com",
    "sub-1.smjcdh.top", "ss88.beifengyuns.top", "appurl.ppacc.cc",
    "145zz.acyunsa.sbs", "svip.ttyun.eu.org", "qijiavpn.salnc.kuaivpn.app",
    "sss.xlajiao.xyz", "api.kuke-sub.com", "apa.dyljstar.sbs",

    # 更多真实出现过的
    "c0d97821eafa5.nydy.cc", "s.fb.22na.cn", "ycexbktkoctx.sealosgzg.site",
    "sub.cocoduck.cc", "cdc502.online", "sub.xnyun.wiki",
    "lnithefedhwadf2qhhald5l23zdadzci.skygo0527.top", "portal.nextport.top",
    "bakapie.cf", "www.ermao.net", "fastestcloud.xyz", "www.kuaidog005.top",
    "jichang.123417.xyz", "m11.spwvpn.com", "dy.wenliansub.com",
    "www.elephant223.com", "jkun.waimaosass.icu", "ec.wjkc.xyz",
    "316.sub987.top", "sub.ssr.sh", "www7th.ga-sub.hair", "suba.f2vip.net",
    "r2-c11-dd.0-w.ccwu.cc", "ndy.fn0618.xyz", "pokelink.xn--4gsvmh74cwxi.cn",
    "www.neteasegames.site", "api.immtel.me", "s1.byte33.com",
    "47.242.128.61", "47.76.155.27", "139.196.241.76", "38.175.196.72",
    "skyfd.chuna.nulaiha.aasxuan.yfftftf.shop", "download.8886698.xyz",
    "area.chinadevelop21.org",

    # 低端/白嫖/试用常见
    "sub.xjhsub", "suying666", "flowercloud", "ytoo", "mojie", "glados",
    "ktmcloud", "smallstrawberry", "config-sync", "subtangniu", "subxiandan",
    "bnsubservdom", "starlinkstatic", "urlapi-dodo", "ccsub", "spphhnhg",
    "lmscunb", "oxycontinon", "terminal69", "xz61", "carpetpacific",
    "laoyao", "fbsubcn", "fcapp", "love-coffee", "todust", "ggbong",
    "liangxin", "onlysub", "byte11", "byte77", "wdyserver", "yuetoto",
    "knjc", "pqjc", "ymjc", "djjc", "jsjc", "yfjc", "efanyunapi",
    "hokkaido-toyoni", "smjcdh", "nervixapp", "boost1", "nydy", "22na",
    "flybit", "cocoduck", "cdc502", "xnyun", "skygo", "nextport", "bakapie",
    "ermao", "v2ny", "wjkc", "sub987", "kuaidog", "spwvpn", "wenlian",
    "elephant", "bafang", "ikuuu", "dyljstar", "kuke-sub", "xlajiao",
    "mzyglc", "acyunsa", "ttyun", "windowsv1", "louwangzhiyu", "kuaivpn",
    "beifengyuns", "ppacc", "ssr.sh", "ga-sub", "f2vip", "fn0618",
    "pokelink", "neteasegames",

    # 中高端常见泄露
    "sub.glados-config.com", "update.glados-config.com", "api.ytoo.xyz",
    "osubscribe.ytoo.xyz", "sub.mojie.me", "sub.mojie.app", "sub.mojie.co",
    "api.suying666.info", "sub.suying666.info", "link.suying666.info",
    "sub.flowercloud.xyz", "api.flowercloud.xyz", "osubscribe.flowercloud.xyz",
    "sub.ktmcloud.id", "api.ktmcloud.id", "sub.smallstrawberry.com",
    "sub1.smallstrawberry.com", "sub2.smallstrawberry.com", "sub3.smallstrawberry.com",
    "sub.liangxin.xyz", "api.liangxin.xyz", "sub.byte11.com", "s1.byte11.com",
    "s1.byte33.com", "s1.byte77.com", "sub.wdyserver.com", "sub0530.wdyserver.com",
    "sub.config-sync.com", "dp3.config-sync.com", "sub.starlinkstatic.cc",
    "sub.urlapi-dodo.sbs", "no1-svip.urlapi-dodo.sbs", "no7-svip.urlapi-dodo",
    "sub.ccsub.org", "www.ccsub.org", "sub.spphhnhg.top", "ierboryt.spphhnhg.top",
    "sub.lmscunb.pro", "lmlla.lmscunb.pro", "sub.oxycontinon.com",
    "api.oxycontinon.com", "sub.terminal69.win", "ratchada.terminal69.win",
    "sub.xz61.cn", "submit.xz61.cn", "sub.carpetpacific.com",
    "sub.laoyao.ltd", "linksc.laoyao.ltd", "sub.fbsubcn01.cc", "fba01.fbsubcn01.cc",
    "sub.fcapp.run", "fm-sub-mainpanel-vygijfogpm.cn-shanghai.fcapp.run",
    "sub.love-coffee.one", "sub.todust.cc", "oymr1a9aua.todust.cc",
    "sub.ggbong.xyz", "sub.onlysub.mjurl.com", "sub.yuetoto.com",
    "sso.yuetoto.com", "sub.knjc.cfd", "dash.knjc.cfd", "sub.pqjc.site",
    "dash.pqjc.site", "sub.ymjc.cfd", "sub.djjc.cfd", "gates.djjc.cfd",
    "sub.jsjc.cfd", "sub.yfjc.xyz", "login.yfjc.xyz", "sub.342242.icu",
    "sf.342242.icu", "sub.efanyunapi.com", "sub.hokkaido-toyoni.com",
    "conf1.hokkaido-toyoni.com", "sub.smjcdh.top", "sub-1.smjcdh.top",
    "sub.nervixapp.top", "sub.boost1.shop", "dy.boost1.shop",
]

# ==================== 工具函数 ====================

def load_seeds() -> list[str]:
    path = Path(SEEDS_FILE)
    if path.exists():
        seeds = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"📂 已加载 {len(seeds)} 个种子域名（来自 {SEEDS_FILE}）")
        return seeds
    else:
        print(f"📂 种子文件不存在，写入初始 {len(INITIAL_SEEDS)} 个域名")
        path.write_text("\n".join(INITIAL_SEEDS) + "\n", encoding="utf-8")
        return INITIAL_SEEDS.copy()


def save_seeds(seeds: list[str]):
    unique = sorted(set(s.strip().lower() for s in seeds if s.strip()))
    Path(SEEDS_FILE).write_text("\n".join(unique) + "\n", encoding="utf-8")
    print(f"💾 已保存 {len(unique)} 个种子域名到 {SEEDS_FILE}")


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
            print(f"    [ERROR] 400 → {clean_query[:70]}")
            return []
        resp.raise_for_status()
        return resp.json().get("organic", [])
    except Exception as e:
        print(f"    [ERROR] 搜索失败: {e}")
        return []


def is_potential_sub_link(url: str) -> bool:
    if not url.startswith("http"):
        return False
    url_lower = url.lower()

    exclude = [
        "google.", "youtube.", "facebook.", "twitter.", "x.com", "github.com",
        "stackoverflow", "wikipedia.", "microsoft.", "apple.com", "amazon.",
        "baidu.com", "zhihu.com", "bilibili.", "weixin.", "qq.com", "taobao.",
        "reddit.com", "medium.com", "csdn.net", "juejin.", "cnblogs.",
        "gitlab.com", "bitbucket.org"
    ]
    if any(x in url_lower for x in exclude):
        return False

    strong = [
        "token=", "sid=", "/api/v1/client/subscribe", "osubscribe.php",
        "/link/", "/s?", "sub?token", "subscribe?token"
    ]
    if not any(s in url_lower for s in strong):
        if len(url) < 80:
            return False
        if not any(ext in url_lower for ext in [".cc/", ".top/", ".xyz/", ".cfd", ".sbs", ".run/", ".icu", ".info/", ".ltd", ".win/", ".shop/", ".online/", ".site/"]):
            return False

    return True


def extract_links_from_results(results: list[dict]) -> set[str]:
    links = set()
    url_pattern = re.compile(r'https?://[^\s<>"\'\)\]\}\{\|,\\\\]{15,600}')

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


def is_alive(url: str) -> tuple[str, bool, str, int]:
    headers = {
        "User-Agent": "ClashforWindows/0.20.39",
        "Accept": "*/*",
    }
    try:
        r = requests.get(url, headers=headers, timeout=TEST_TIMEOUT, allow_redirects=True, stream=True)
        if r.status_code != 200:
            return url, False, f"HTTP {r.status_code}", 0

        content = b""
        for chunk in r.iter_content(1024):
            content += chunk
            if len(content) >= 8192:
                break

        text = content.decode("utf-8", errors="ignore").lower()
        length = len(text)

        signs = [
            "proxies:", "proxy-groups:", "rules:", "port:", "socks-port:",
            "vmess://", "vless://", "trojan://", "ss://", "ssr://", "hysteria",
            "uuid", "cipher:", "password:", "network:", "ws-opts", "grpc-opts",
            "server:", "tls:", "reality", "flow:", "client-fingerprint"
        ]
        if any(s in text for s in signs):
            return url, True, "存活", length
        if length > 150 and "error" not in text[:500] and "not found" not in text[:500]:
            return url, True, "可能存活", length
        return url, False, "内容不像订阅", length

    except requests.exceptions.Timeout:
        return url, False, "超时", 0
    except Exception as e:
        return url, False, str(e)[:40], 0


def batch_test(urls: list[str]) -> list[tuple[str, int]]:
    results = []
    print(f"  开始测活，共 {len(urls)} 个链接...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(is_alive, u): u for u in urls}
        for future in as_completed(futures):
            url, ok, reason, length = future.result()
            if ok:
                results.append((url, length))
                print(f"    ✅ {url}  (len={length})")
            else:
                print(f"    ❌ {url[:70]}... ({reason})")
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def extract_domains_from_urls(urls: list[str]) -> set[str]:
    domains = set()
    for u in urls:
        try:
            parsed = urlparse(u)
            host = parsed.netloc.lower()
            if not host:
                continue
            if host.startswith("www."):
                host = host[4:]
            if re.match(r"^\d+\.\d+\.\d+\.\d+", host):
                continue
            if len(host) > 5 and "." in host:
                domains.add(host)
        except:
            pass
    return domains


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


# ==================== 主逻辑 ====================

def main():
    if not SERPER_API_KEY:
        print("❌ 缺少 SERPER_API_KEY 环境变量")
        return

    print("🚀 真实订阅域名最终完整版 + 自动升级启动")
    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing).strftime("%Y-%m-%d %H:%M:%S")
    time_tag = datetime.now().strftime("%Y%m%d_%H%M")

    seeds = load_seeds()

    # 强制把 INITIAL_SEEDS 里缺失的也合并进去（防止种子文件过旧）
    before_merge = set(s.lower() for s in seeds)
    added_from_initial = []
    for d in INITIAL_SEEDS:
        d_low = d.lower().strip()
        if d_low and d_low not in before_merge:
            seeds.append(d_low)
            added_from_initial.append(d_low)
    if added_from_initial:
        print(f"🔄 从 INITIAL_SEEDS 补充了 {len(added_from_initial)} 个缺失域名")
        save_seeds(seeds)

    all_candidates = set()

    # ========== 1. 关键词搜索（代码内 KEYWORDS，一定会执行） ==========
    print(f"\n{'='*60}")
    print(f"===== ① 关键词搜索（共 {len(KEYWORDS)} 个，来自代码内 KEYWORDS）=====")
    print(f"{'='*60}")
    for idx, kw in enumerate(KEYWORDS, 1):
        print(f"\n[{idx}/{len(KEYWORDS)}] 关键词: {kw}")
        queries = [kw, f"{kw} 订阅", f"{kw} token OR sid"]
        for q in queries:
            results = search_serper(q, NUM_RESULTS)
            found = extract_links_from_results(results)
            all_candidates.update(found)
            time.sleep(0.4)
        print(f"  当前累计候选: {len(all_candidates)}")
        time.sleep(SLEEP_BETWEEN_KEYWORDS)

    print(f"\n✅ 关键词搜索完成，当前候选链接: {len(all_candidates)}")

    # ========== 2. 真实订阅域名定向搜索 ==========
    print(f"\n{'='*60}")
    print(f"===== ② 真实订阅域名定向搜索（共 {len(seeds)} 个种子）=====")
    print(f"{'='*60}")
    for idx, domain in enumerate(seeds, 1):
        print(f"  [{idx}/{len(seeds)}] → {domain}")
        results = search_serper(f"{domain} (subscribe OR token OR 订阅 OR sid)", 60)
        found = extract_links_from_results(results)
        all_candidates.update(found)
        time.sleep(0.8)

    all_candidates = sorted(all_candidates)
    print(f"\n📦 总共收集到 {len(all_candidates)} 个候选链接")

    full_filename = f"full_candidates_{time_tag}.txt"
    save_and_send(all_candidates, full_filename,
                  f"📋 完整候选列表（真实订阅域名最终完整版）\n时间: {now}\n数量: {len(all_candidates)}")

    if not all_candidates:
        print("没有候选链接，结束")
        return

    # ========== 3. 测活 ==========
    alive_with_score = batch_test(all_candidates)
    alive_links = [u for u, _ in alive_with_score]
    print(f"\n✅ 测活完成：存活 {len(alive_links)} / {len(all_candidates)}")

    alive_filename = f"alive_subs_{time_tag}.txt"
    save_and_send(alive_links, alive_filename,
                  f"✅ 存活机场订阅（已按质量排序）\n时间: {now}\n候选: {len(all_candidates)} | 存活: {len(alive_links)}")

    # ========== 4. 提取新域名并升级种子库 ==========
    new_domains = extract_domains_from_urls(alive_links)
    print(f"\n🧬 本次发现 {len(new_domains)} 个域名")

    before = set(s.lower() for s in seeds)
    added = []
    for d in sorted(new_domains):
        if d not in before:
            seeds.append(d)
            added.append(d)

    if added:
        print(f"✨ 新增 {len(added)} 个种子域名")
        for a in added[:30]:
            print(f"   + {a}")
        if len(added) > 30:
            print(f"   ... 还有 {len(added)-30} 个")
        save_seeds(seeds)
    else:
        print("没有新域名需要追加")

    if new_domains:
        domain_file = f"new_domains_{time_tag}.txt"
        with open(domain_file, "w", encoding="utf-8") as f:
            for d in sorted(new_domains):
                f.write(d + "\n")
        send_txt_file(domain_file, f"🧬 本次发现域名\n时间: {now}\n数量: {len(new_domains)}")

    print("\n🎉 全部完成！关键词搜索 + 域名搜索 + 种子自动升级均已执行。")


if __name__ == "__main__":
    main()
