#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WTA301 U-Boot 中断脚本 v4
优化：更快的响应速度、更多中断字符、连续发送
"""

import serial
import time
import sys

# 串口配置
PORT = "COM3"  # 改成你的串口号
BAUD = 115200

# 中断字符列表（尝试各种可能的中断键）
BREAK_CHARS = [
    b"\x03",      # Ctrl+C
    b"\x04",      # Ctrl+D
    b" ",         # 空格
    b"\r",        # 回车
    b"\n",        # 换行
    b"\x1b",      # Esc
    b"x",         # 有些 U-Boot 用 'x' 中断
    b"q",         # 有些 U-Boot 用 'q' 中断
]

def main():
    print(f"=== WTA301 U-Boot 中断脚本 v4 ===")
    print(f"串口: {PORT}, 波特率: {BAUD}")
    print(f"请现在给路由器上电！")
    print(f"等待 U-Boot 启动...\n")

    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
    except Exception as e:
        print(f"打开串口失败: {e}")
        print(f"请检查串口号是否正确，以及串口是否被占用")
        return

    start_time = time.time()
    char_idx = 0
    received = b""

    # 持续监听和发送中断，持续 10 秒
    while time.time() - start_time < 10:
        # 读取串口输出
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            received += data
            # 打印可显示的字符
            try:
                text = data.decode("utf-8", errors="replace")
                print(text, end="", flush=True)
            except:
                pass

            # 检查是否已经进入 U-Boot 命令行
            if b"IPQ" in received or b"Qualcomm" in received or b"U-Boot" in received:
                # 看到 U-Boot 输出，立即开始发送中断
                print(f"\n\n[!] 检测到 U-Boot 输出，开始发送中断...")

                # 快速连续发送所有中断字符
                for i in range(50):
                    char = BREAK_CHARS[char_idx % len(BREAK_CHARS)]
                    ser.write(char)
                    ser.flush()
                    char_idx += 1
                    time.sleep(0.01)  # 10ms 间隔

                # 等待看是否进入命令行
                time.sleep(1)
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    print(data.decode("utf-8", errors="replace"), end="", flush=True)

                # 检查是否看到 "=>" 提示符（U-Boot 命令行）
                if b"=>" in received or b"IPQ5018" in received:
                    print(f"\n\n[✓] 成功进入 U-Boot 命令行！")
                    print(f"现在你可以输入命令了")
                    print(f"常用命令:")
                    print(f"  printenv           - 查看环境变量")
                    print(f"  setenv ipaddr 192.168.2.2  - 设置路由器 IP")
                    print(f"  setenv serverip 192.168.2.100 - 设置 TFTP 服务器 IP")
                    print(f"  tftpboot 0x44000000 openwrt.itb - 从 TFTP 下载镜像")
                    print(f"  bootm 0x44000000   - 启动镜像")

                    # 进入交互模式
                    print(f"\n--- 交互模式（输入 'exit' 退出）---")
                    while True:
                        cmd = input("> ")
                        if cmd.lower() == "exit":
                            break
                        ser.write((cmd + "\r\n").encode())
                        time.sleep(0.5)
                        if ser.in_waiting > 0:
                            print(ser.read(ser.in_waiting).decode("utf-8", errors="replace"))

                    ser.close()
                    return

        # 即使没有收到数据，也持续发送中断字符
        # 这样在 U-Boot 刚启动时就能立即发送中断
        if time.time() - start_time < 3:  # 前3秒持续发送
            char = BREAK_CHARS[char_idx % len(BREAK_CHARS)]
            ser.write(char)
            ser.flush()
            char_idx += 1
            time.sleep(0.02)  # 20ms 间隔

    print(f"\n\n[×] 10 秒内没有成功进入 U-Boot 命令行")
    print(f"接收到的数据:")
    print(received.decode("utf-8", errors="replace"))

    ser.close()

if __name__ == "__main__":
    main()
