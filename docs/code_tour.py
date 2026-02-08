#!/usr/bin/env python3
import os
import sys
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_slow(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def show_file_snippet(path, lines=15):
    print(f"\n--- FILE: {path} ---")
    try:
        with open(path, 'r') as f:
            content = f.readlines()
            for i, line in enumerate(content[:lines]):
                print(f"{i+1:2d} | {line.rstrip()}")
            if len(content) > lines:
                print("...")
    except FileNotFoundError:
        print("File not found.")
    print("-" * 40)

def tour():
    clear_screen()
    print_slow("🚀 欢迎来到 EmailApp 代码交互式导览！")
    print_slow("我们将带你浏览核心模块。按回车键继续...")
    input()

    steps = [
        {
            "title": "1. 项目入口 (app.py)",
            "desc": "这是开发环境的启动脚本。它调用 create_app() 工厂函数。",
            "file": "app.py"
        },
        {
            "title": "2. 应用工厂 (app/__init__.py)",
            "desc": "Flask 应用在此初始化。配置加载和蓝图注册都发生在这里。",
            "file": "app/__init__.py"
        },
        {
            "title": "3. 路由定义 (app/routes.py)",
            "desc": "这里处理 Web 请求。核心逻辑在 index() 函数中。",
            "file": "app/routes.py"
        },
        {
            "title": "4. 邮件服务 (app/email_utils.py)",
            "desc": "封装了 SMTP 发送逻辑。注意这里的重试机制和异常处理。",
            "file": "app/email_utils.py"
        },
        {
            "title": "5. 配置管理 (app/config.py)",
            "desc": "从环境变量读取配置，保证敏感信息安全。",
            "file": "app/config.py"
        }
    ]

    for step in steps:
        clear_screen()
        print(f"## {step['title']}")
        print_slow(step['desc'])
        show_file_snippet(step['file'])
        print("\n[按回车键继续，输入 'q' 退出]")
        if input().lower() == 'q':
            break

    clear_screen()
    print_slow("🎉 导览结束！请阅读 docs/guide.md 获取更多详情。")

if __name__ == "__main__":
    # Ensure we are in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    tour()