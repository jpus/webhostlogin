from playwright.sync_api import sync_playwright
import os
import requests
import time

def send_telegram_message(message):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        raise ValueError("Telegram bot token 或 chat ID 未正确配置.")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Telegram 消息发送失败: {response.text}")
    return response.json()

def login_koyeb(email, password, browser_path=None):
    try:
        with sync_playwright() as p:
            # 指定 Playwright 浏览器路径
            firefox = p.firefox.launch(headless=True, executable_path=browser_path)
            page = firefox.new_page()

            # 访问登录页面
            page.goto("https://webhostmost.com/login")

            # 输入邮箱和密码
            page.get_by_placeholder("Enter email").fill(email)
            page.get_by_placeholder("Password").fill(password)
        
            # 点击登录按钮
            page.get_by_role("button", name="Login").click()

            # 等待错误消息或成功登录后的页面
            try:
                error_message = page.wait_for_selector('.MuiAlert-message', timeout=5000)
                error_text = error_message.inner_text()
                return f"账号 {email} 登录失败: {error_text}"
            except:
                # 如果错误消息不存在，检查是否跳转到仪表板页面
                page.wait_for_url("https://webhostmost.com/clientarea.php", timeout=5000)
                return f"账号 {email} 登录成功!"
    except Exception as e:
        return f"账号 {email} 登录失败: {str(e)}"
    finally:
        firefox.close()

if __name__ == "__main__":
    accounts = os.environ.get('WEBHOST', '').split()
    if not accounts:
        error_message = "没有配置任何账号"
        send_telegram_message(error_message)
        print(error_message)
    else:
        # Playwright 浏览器路径
        browser_path = os.environ.get('PLAYWRIGHT_BROWSER_PATH', None)
        if not browser_path:
            print("未指定浏览器路径，将使用默认浏览器.")

        login_statuses = []
        for account in accounts:
            try:
                email, password = account.split(':')
                status = login_koyeb(email, password, browser_path=browser_path)
            except ValueError:
                status = f"账号配置错误: {account}"
            login_statuses.append(status)
            print(status)
            
            # 每个账号延时 30 秒
            time.sleep(30)

        message = "WEBHOST登录状态:\n\n" + "\n".join(login_statuses)
        result = send_telegram_message(message)
        print("消息已发送到Telegram:", result)
