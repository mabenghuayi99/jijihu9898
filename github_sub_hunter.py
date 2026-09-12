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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")          # 强烈建议配置
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MAX_WORKERS = 25
TEST_TIMEOUT = 12
SEEDS_FILE = "github-sub-hunter.txt"
GITHUB_SEARCH_PER_PAGE = 50
MAX_PAGES_PER_QUERY = 1              # 每个查询最多翻页数

# ==================== 关键词 (已优化：精简 + 高级过滤器) ====================
KEYWORDS = [
    # 【王牌1：搜配置文件里的 proxy-providers】
    '"proxy-providers:" "url:" extension:yaml',
    '"proxy-providers:" "url:" extension:yml',
    
    # 【王牌2：搜 V2board 等面板的固定路径，不限文件类型】
    '"/api/v1/client/subscribe?token="',
    '"/link/" "clash="',
    '"osubscribe.php?sid="',
    '"sub?token="',
    '"/api/v1/ss/"',
    
    # 【王牌3：搜硬编码在脚本里的聚合订阅源】
    '"sub" "url" extension:py', # 找找别人写的抓取脚本里的订阅源
]

# ==================== 完整 INITIAL_SEEDS ====================
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

# 将自带种子统一小写用于去重判断
INITIAL_SEEDS_LOWER = [s.lower() for s in INITIAL_SEEDS]

# ==================== 工具函数 ====================

def get_headers():
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Sub-Hunter/2.3"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def load_dynamic_seeds() -> list[str]:
    """读取 txt 文件中的动态种子，并剔除已经在 INITIAL_SEEDS 中的项"""
    path = Path(SEEDS_FILE)
    if path.exists():
        seeds = [line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        valid_seeds = [s for s in seeds if s not in INITIAL_SEEDS_LOWER]
        print(f"📂 已加载 {len(valid_seeds)} 个额外动态种子域名")
        return valid_seeds
    else:
        print("📂 种子文件不存在，将跳过外部读取。")
        return []


def save_dynamic_seeds(new_domains: list[str]):
    """将新发现的域名写入 txt，并严格保证它不包含 INITIAL_SEEDS 里的内容"""
    path = Path(SEEDS_FILE)
    existing = []
    if path.exists():
        existing = [line.strip().lower() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    
    combined_set = set(existing) | set(d.strip().lower() for d in new_domains)
    final_seeds = sorted([d for d in combined_set if d not in INITIAL_SEEDS_LOWER])
    
    path.write_text("\n".join(final_seeds) + "\n", encoding="utf-8")
    print(f"💾 已保存 {len(final_seeds)} 个动态种子域名到 {SEEDS_FILE}")


def github_code_search(query: str, page: int = 1) -> list[dict]:
    url = "https://api.github.com/search/code"
    params = {
        "q": query,
        "per_page": GITHUB_SEARCH_PER_PAGE,
        "page": page
    }
    
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=get_headers(), params=params, timeout=30)
            if resp.status_code == 403:
                reset_time = resp.headers.get("X-RateLimit-Reset")
                if reset_time:
                    sleep_time = max(int(reset_time) - int(time.time()), 65)
                else:
                    sleep_time = 66
                print(f"    [WARN] 触发速率限制，等待 {sleep_time} 秒后重试 (第 {attempt+1} 次)...")
                time.sleep(sleep_time + 1)
                continue
            if resp.status_code == 422:
                return []
            resp.raise_for_status()
            return resp.json().get("items", [])
        except Exception as e:
            print(f"    [ERROR] 请求异常: {e}")
            time.sleep(5)
            
    return []


def get_raw_content(html_url: str) -> str:
    """获取文件原始内容"""
    raw_url = html_url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
    try:
        r = requests.get(raw_url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""


def extract_sub_links_from_text(text: str) -> set[str]:
    """从文本中提取真正的机场订阅链接（排除 GitHub 自身链接）"""
    links = set()
    
    # 【增强1：专门提取 proxy-providers 里的 url: 链接】
    provider_pattern = re.compile(r'url:\s*[\'\"](https?://[^\s\'\"]+)[\'\"]')
    for m in provider_pattern.findall(text):
        low = m.lower()
        if not any(x in low for x in ["github.com", "githubusercontent.com", "gist.github", "raw.github", "google.", "youtube.", "facebook.", "twitter.", "x.com", "baidu.com", "zhihu.com"]):
            links.add(m)

    # 【增强2：通用正则提取带有订阅特征的链接】
    pattern = re.compile(r'https?://[^\s<>"\'\)\]\}\{\|,\\]{20,500}')
    for m in pattern.findall(text):
        clean = m.rstrip('.,;:!?)\'\"')
        low = clean.lower()

        if any(x in low for x in ["github.com", "githubusercontent.com", "gist.github", "raw.github"]):
            continue
        if any(x in low for x in ["google.", "youtube.", "facebook.", "twitter.", "x.com", "baidu.com", "zhihu.com"]):
            continue

        if any(k in low for k in [
            "token=", "sid=", "/api/v1/client/subscribe", "osubscribe.php",
            "subscribe?token", "sub?token", "/link/", "/s?", "clash=", "sub="
        ]):
            links.add(clean)
            
    return links


def is_alive(url: str) -> tuple[str, bool, str, int]:
    headers = {
        "User-Agent": "ClashforWindows/0.20.39",
        "Accept": "*/*",
    }
    try:
        with requests.get(url, headers=headers, timeout=TEST_TIMEOUT, allow_redirects=True, stream=True) as r:
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
            if length > 120 and "error" not in text[:400] and "not found" not in text[:400]:
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
                print(f"    ✅ {url}")
            else:
                print(f"    ❌ {url[:80]}... ({reason})")
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def extract_domains_from_urls(urls: list[str]) -> set[str]:
    domains = set()
    for u in urls:
        try:
            parsed = urlparse(u)
            host = parsed.netloc.lower()
            if not host or "github" in host:
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
    print("🚀 纯 GitHub 搜索版（精准配置挖掘 + 测活）")
    if not GITHUB_TOKEN:
        print("⚠️  未配置 GITHUB_TOKEN，可能触发严厉限流")
    else:
        print("✅ 已检测到 GITHUB_TOKEN")

    beijing = timezone(timedelta(hours=8))
    now = datetime.now(beijing).strftime("%Y-%m-%d %H:%M:%S")
    time_tag = datetime.now().strftime("%Y%m%d_%H%M")

    general_keywords = list(dict.fromkeys(KEYWORDS))
    
    dynamic_seeds = load_dynamic_seeds()
    domain_keywords = list(dict.fromkeys(INITIAL_SEEDS + dynamic_seeds))

    ALL_SEARCH_TERMS = general_keywords + domain_keywords
    all_candidates = set()

    print(f"\n{'='*60}")
    print(f"===== GitHub Code Search（共 {len(ALL_SEARCH_TERMS)} 个搜索词）=====")
    print(f"  - 精准特征词 (含高级过滤器): {len(general_keywords)} 个")
    print(f"  - 具体域名 (精准匹配): {len(domain_keywords)} 个")
    print(f"{'='*60}")

    for idx, kw in enumerate(ALL_SEARCH_TERMS, 1):
        print(f"\n[{idx}/{len(ALL_SEARCH_TERMS)}] 搜索词: {kw}")

        # 统一使用关键词原样搜索 (已包含高级过滤器语法)
        queries = [kw]

        for q in queries:
            print(f"  → 执行查询: {q[:75]}...")
            for page in range(1, MAX_PAGES_PER_QUERY + 1):
                items = github_code_search(q, page=page)
                
                if items:
                    for item in items:
                        html_url = item.get("html_url", "")
                        if not html_url:
                            continue
                        content = get_raw_content(html_url)
                        if content:
                            found = extract_sub_links_from_text(content)
                            all_candidates.update(found)
                
                print(f"    第{page}页处理完成 | 当前真实订阅链接: {len(all_candidates)}")
                
                time.sleep(3.0)
                
                if not items:
                    break

    all_candidates = sorted(all_candidates)
    print(f"\n📦 总共提取到 {len(all_candidates)} 个真实机场订阅链接")

    if not all_candidates:
        print("没有找到真实订阅链接，结束")
        return

    chunk_size = 5000
    total_parts = (len(all_candidates) + chunk_size - 1) // chunk_size
    
    for i in range(0, len(all_candidates), chunk_size):
        chunk = all_candidates[i:i + chunk_size]
        part_idx = (i // chunk_size) + 1
        
        full_file = f"github_real_subs_{time_tag}_part{part_idx}.txt"
        caption = f"📋 GitHub 提取原始订阅 ({part_idx}/{total_parts})\n时间: {now}\n本组数量: {len(chunk)}"
        save_and_send(chunk, full_file, caption)

    alive_with_score = batch_test(all_candidates)
    alive_links = [u for u, _ in alive_with_score]
    print(f"\n✅ 测活完成：存活 {len(alive_links)} / {len(all_candidates)}")

    alive_file = f"alive_subs_{time_tag}.txt"
    save_and_send(alive_links, alive_file,
                  f"✅ 存活机场订阅（GitHub来源）\n时间: {now}\n候选: {len(all_candidates)} | 存活: {len(alive_links)}")

    new_domains = extract_domains_from_urls(alive_links)
    print(f"\n🧬 本次有效结果涉及 {len(new_domains)} 个域名")
    
    if new_domains:
        save_dynamic_seeds(list(new_domains))
        
        domain_file = f"new_domains_{time_tag}.txt"
        with open(domain_file, "w", encoding="utf-8") as f:
            for d in sorted(new_domains):
                f.write(d + "\n")
        send_txt_file(domain_file, f"🧬 存活来源域名\n时间: {now}\n数量: {len(new_domains)}")

    print("\n🎉 全部完成！")


if __name__ == "__main__":
    main()
