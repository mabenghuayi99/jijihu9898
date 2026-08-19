import concurrent.futures
import io
import os
import re
import sys
import time
import requests
import base64
from urllib.parse import quote_plus, urlparse

# ===================== 配置区 =====================
GITHUB_TOKEN = os.getenv("PYTHON_GH_TOKEN") or os.getenv("MY_GH_TOKEN") or os.getenv("GITHUB_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")  # 必须配置，用于保存记忆文件

MEMORY_FILE_PATH = "sub_learned_domains.txt" # 订阅域名的专属记忆文件

# 1. 基础探针词 (种子)
SEARCH_QUERIES = [
    "xjhsub1.top", "sukiaira.com", "subxiandan.top", "bnsubservdom.com", 
    "ccsub.org", "flowercloud.xyz", "urlapi-dodo.sbs", "spphhnhg.top", 
    "lmscunb.pro", "oxycontinon.com", "suying666.info", "trafficmanager.net", 
    "starlinkstatic.cc", "terminal69.win", "xz61.cn", "carpetpacific.com", 
    "laoyao.ltd", "subtangniu.top", "fbsubcn01.cc", "fcapp.run", 
    "love-coffee.one", "ytoo.xyz", "todust.cc", "ggbong.xyz", 
    "liangxin.xyz", "mjurl.com", "xn--cp3a08l.com", "xn--m7r52rosihxm.com", 
    "mojie.app", "mojie.co", "mhlnf.cn", "byte11.com", "config-sync.com", 
    "ktmcloud01.cc", "wdyserver.com", "smallstrawberry.com", "knjc.cfd", 
    "yuetoto.com", "pqjc.site", "ymjc.cfd", "glados-config.com", 
    "byte77.com", "boost1.shop", "nervixapp.top", "yfjc.xyz", 
    "342242.icu", "efanyunapi.com", "djjc.cfd", "jsjc.cfd", 
    "12.kg", "subscription-shortlink.pages.dev", "hokkaido-toyoni.com", 
    "ktmcloud.id", "smjcdh.top", "bigairport-nineteenth-sub",
    "api/v1/client/subscribe?token=",
    "osubscribe.php?sid=",
    "api/v1/trails/bolster?token=",
    "clash=3&extend=1"
]

# 2. 基础过滤特征
BASE_FILTER_KEYWORDS = [
    "/api/v1/client/subscribe?token=",
    "/link/",
    "/osubscribe.php?sid=",
    "/s?t=",
    "clash=3",
    "sub=3",
    "/dazhutou",
    "/sub"
]

BLACKLIST_DOMAINS = [
    "github.com", "google.com", "baidu.com", "w3.org", "cloudflare.com", 
    "microsoft.com", "apple.com", "github.io", "gitlab.com", "wikipedia.org", 
    "example.com", "127.0.0.1", "localhost", "t.me", "api.telegram.org",
    "jsdelivr.net", "raw.githubusercontent.com"
]

API_BASE_URL = "https://api.github.com/search/code"
MAX_FILES = 800
# =================================================

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# ----------------- 🧠 长效记忆模块 -----------------
def load_learned_domains():
    if not GITHUB_TOKEN or not GITHUB_REPO: return set(), None
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{MEMORY_FILE_PATH}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            return set(line.strip() for line in content.split('\n') if line.strip()), data['sha']
    except: pass
    return set(), None

def save_learned_domains(domains_set, sha):
    if not GITHUB_TOKEN or not GITHUB_REPO: return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{MEMORY_FILE_PATH}"
    content = "\n".join(sorted(domains_set))
    payload = {
        "message": "🤖 Auto-update Sub Harvester learned domains (AI Memory)",
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
    }
    if sha: payload["sha"] = sha
    try:
        requests.put(url, headers=HEADERS, json=payload, timeout=10)
        print("  ✓ 长效记忆库已成功同步写入 Github 仓库！")
    except Exception as e:
        print(f"  ✗ 记忆同步异常: {e}")

# ----------------- 🔍 Github 搜索与提取模块 -----------------
def search_github_files(keywords, pass_name="搜索"):
    file_urls = set()
    print(f"\n[*] 开始【{pass_name}】(代码搜索)，探针数量: {len(keywords)}")

    for kw_idx, keyword in enumerate(keywords, 1):
        if len(file_urls) >= MAX_FILES: break
            
        search_term = keyword.replace("https://", "").replace("http://", "")
        if len(search_term) > 60: search_term = search_term[:60]
        
        # 加上双引号精确匹配
        q_str = f'"{search_term}"' if "=" not in search_term else search_term

        print(f"  [{kw_idx}/{len(keywords)}] 搜索词: {search_term[:40]}...")

        page = 1
        while page <= 3 and len(file_urls) < MAX_FILES:
            params = {
                "q": q_str,
                "sort": "indexed", 
                "order": "desc",
                "page": page,
                "per_page": 100
            }
            
            try:
                r = requests.get(API_BASE_URL, headers=HEADERS, params=params, timeout=20)
            except Exception as e:
                print(f"    - 搜索异常: {e}"); break

            if r.status_code in [403, 429]:
                reset_timestamp = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait_time = max(1, reset_timestamp - int(time.time()) + 1)
                print(f"    [!] 触发限流，智能等待 {wait_time} 秒至重置...")
                time.sleep(wait_time)
                continue 
                
            if r.status_code != 200: break

            items = r.json().get("items", [])
            if not items: break

            new_count = 0
            for item in items:
                html = item.get("html_url", "")
                raw = html.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                if raw not in file_urls:
                    file_urls.add(raw)
                    new_count += 1

            page += 1
            time.sleep(2.5) # 防封禁间隔

    return list(file_urls)[:MAX_FILES]

def extract_links_from_text(text, filter_keywords):
    found = set()
    pattern = r'https?://[^\s\'"<>\]\)]+'
    candidates = re.findall(pattern, text)

    for link in candidates:
        link = link.rstrip('.,;\'")]}>\\')
        for kw in filter_keywords:
            if kw in link or kw.replace("https://", "") in link:
                found.add(link)
                break
    return found

def download_and_extract(file_url, keywords):
    try:
        r = requests.get(file_url, timeout=12)
        if r.status_code == 200:
            return extract_links_from_text(r.text, keywords)
    except: pass
    return set()

def extract_infection_domains(links, known_domains):
    """从提取出的订阅链接中，扒出新的机场域名"""
    new_domains = set()
    for link in links:
        try:
            domain = urlparse(link).netloc.lower()
            if not domain or any(b in domain for b in BLACKLIST_DOMAINS): continue
            # 排除纯 IP
            if re.match(r'^\d+\.\d+\.\d+\.\d+(:\d+)?$', domain): continue
            
            clean_domain = domain.split(':')[0]
            if "." in clean_domain and len(clean_domain) > 5:
                if clean_domain not in known_domains: 
                    new_domains.add(clean_domain)
        except: continue
    return list(new_domains)

# ===================== 🚀 主函数入口 =====================
def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("错误: 缺少 Telegram 环境变量配置 (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        sys.exit(1)

    print("="*50)
    print(" 🚀 启动 [订阅自动收割机] (AI 感染进化版)")
    print("="*50)

    # 1. 加载大脑记忆
    learned_domains, memory_sha = load_learned_domains()
    known_all_domains = set(SEARCH_QUERIES) | learned_domains
    
    if learned_domains:
        print(f"[*] 唤醒记忆，当前已积累 {len(learned_domains)} 个机场订阅域名。")
        import random
        # 混合基础词和随机记忆词
        active_keywords = SEARCH_QUERIES + random.sample(list(learned_domains), min(len(learned_domains), 10))
    else:
        active_keywords = SEARCH_QUERIES

    # 动态组装白名单：基础特征 + 所有的域名
    dynamic_filters = BASE_FILTER_KEYWORDS + list(known_all_domains)

    # 2. 第一波搜索 (初次感染)
    file_urls_pass1 = search_github_files(active_keywords, "初次搜刮")
    if not file_urls_pass1:
        print("未搜索到有效代码文件，提早下班。")
        sys.exit(1)

    all_extracted_links = set()
    print(f"\n[*] 正在并发降维解析 {len(file_urls_pass1)} 个文件...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(download_and_extract, url, dynamic_filters) for url in file_urls_pass1]
        for future in concurrent.futures.as_completed(futures):
            all_extracted_links.update(future.result())

    # 3. 提取特征，触发二次感染
    new_domains = extract_infection_domains(all_extracted_links, known_all_domains)
    if new_domains:
        print(f"\n[🧠 记忆进化!] 从提取的链接中，裂变出 {len(new_domains)} 个全新机场域名！")
        learned_domains.update(new_domains)
        save_learned_domains(learned_domains, memory_sha)
        
        # 将新学到的域名马上加入过滤白名单
        dynamic_filters.extend(new_domains)
        
        # 取最新的 5 个域名发起二次暴击搜索
        file_urls_pass2 = search_github_files(list(new_domains)[:5], "二次深度感染")
        
        print(f"\n[*] 正在并发解析二次感染的 {len(file_urls_pass2)} 个文件...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(download_and_extract, url, dynamic_filters) for url in file_urls_pass2]
            for future in concurrent.futures.as_completed(futures):
                all_extracted_links.update(future.result())

    if not all_extracted_links:
        print("[!] 灾难级情况：提取完毕，没有找到任何有效订阅链接！")
        sys.exit(1)

    all_links_sorted = sorted(set(all_extracted_links))
    print(f"\n[*] 任务完美结束！共刮出 {len(all_links_sorted)} 个订阅链接。")
    print("[*] 正在打包推送至 Telegram...")

    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    txt_all_content = "\n".join(all_links_sorted)
    file_all_obj = io.BytesIO(txt_all_content.encode("utf-8"))
    file_all_obj.name = f"Sub_Links_{len(all_links_sorted)}.txt"

    evo_text = f"🧬 <b>AI进化:</b> 本次裂变 {len(new_domains)} 个新机场\n" if new_domains else ""
    payload_all = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": f"📂 <b>[全网订阅收割包] (AI进化版)</b>\n\n🎯 <b>提取数量:</b> {len(all_links_sorted)} 个链接\n{evo_text}🛡 <b>模式:</b> 宽进严出 + 二次感染\n🕒 <b>时间:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(tg_url, data=payload_all, files={"document": file_all_obj}, timeout=60)
        if resp.status_code == 200:
            print("  ✓ 完整候选链接文件推送成功！")
        else:
            print(f"  ✗ 推送失败，状态码: {resp.status_code}")
    except Exception as e:
        print(f"  ✗ 完整链接推送异常: {e}")

if __name__ == '__main__':
    main()
