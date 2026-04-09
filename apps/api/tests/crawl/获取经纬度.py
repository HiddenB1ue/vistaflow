import os
import time
import argparse
from typing import Optional, Tuple

import httpx

# 高德地图地理编码 API 地址
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"

class AmapRateLimitError(RuntimeError):
    """当触发高德 QPS 限制时抛出"""
    pass

def query_amap_geocode(
    client: httpx.Client,
    api_key: str,
    address: str,
    city: Optional[str] = None,
    timeout: float = 8.0
) -> Optional[Tuple[float, float]]:
    """
    调用高德 API 获取经纬度。
    address: 原样传入，不做任何修改。
    city: 如果用户没指定城市，这里也不自动推断，直接传 None。
    """
    params = {
        "key": api_key,
        "address": address, # 原样使用
        "output": "json"
    }
    # 只有当用户显式提供了 city 参数时才添加，否则不添加 city 限制
    if city:
        params["city"] = city

    try:
        response = client.get(AMAP_GEOCODE_URL, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        print(f"网络请求错误: {e}")
        return None

    status = str(payload.get("status", ""))
    
    if status != "1":
        infocode = str(payload.get("infocode", ""))
        info = payload.get("info", "未知错误")
        
        if infocode == "10021":
            raise AmapRateLimitError(f"触发频率限制 (QPS): {info}")
        elif infocode == "10009":
            raise RuntimeError("Key 类型错误：请使用 Web 服务 Key (10009)")
        elif infocode in {"10001", "10002", "10003", "10004"}:
            raise RuntimeError(f"API Key 无效或过期: {info}")
        
        return None

    geocodes = payload.get("geocodes", [])
    if not geocodes:
        return None

    location_str = geocodes[0].get("location", "")
    if "," not in location_str:
        return None

    lng, lat = map(float, location_str.split(","))
    return lng, lat

def geocode_exact_address(
    api_key: str,
    query: str,
    sleep_seconds: float = 0.2,
    max_retries: int = 3
) -> Optional[Tuple[float, float]]:
    """
    核心逻辑：完全忠实于用户输入，不进行任何变体尝试。
    """
    with httpx.Client(headers={"User-Agent": "ExactGeoCoder/1.0"}) as client:
        for attempt in range(max_retries):
            try:
                # 直接查询，不加城市限定，不改地址文字
                result = query_amap_geocode(
                    client=client,
                    api_key=api_key,
                    address=query, 
                    city=None, 
                )
                if result:
                    return result
            except AmapRateLimitError:
                wait_time = sleep_seconds * (attempt + 1)
                print(f"   ⚠️  触发限流，等待 {wait_time:.2f} 秒后重试...")
                time.sleep(wait_time)
            except RuntimeError as e:
                print(f"   ❌ 错误: {e}")
                return None
            
            # 即使没有报错，如果没结果或为了安全，也休眠一下
            if sleep_seconds > 0 and attempt < max_retries - 1:
                time.sleep(sleep_seconds)
    
    return None

def main():
    parser = argparse.ArgumentParser(description="高德地图经纬度查询工具 (严格模式：输入即所得)")
    parser.add_argument("address", nargs="?", help="要查询的完整地址 (例如: '北京市朝阳区朝阳公园南路')")
    parser.add_argument("--key", default=os.getenv("AMAP_KEY"), help="高德 Web 服务 Key")
    parser.add_argument("--sleep", type=float, default=0.2, help="请求间隔秒数")
    
    args = parser.parse_args()

    if not args.key:
        print("❌ 错误: 未找到 API Key。请设置 --key 参数或 export AMAP_KEY=your_key")
        return

    def run_query(addr: str):
        print(f"🔍 正在严格查询: '{addr}' ...")
        result = geocode_exact_address(args.key, addr, sleep_seconds=args.sleep)
        
        if result:
            lng, lat = result
            print(f"✅ 成功!")
            print(f"   经度: {lng:.6f}")
            print(f"   纬度: {lat:.6f}")
            print(f"   CSV格式: {lng},{lat}")
        else:
            print("❌ 未找到结果。请检查地址是否准确，或尝试在高德地图官网手动搜索验证。")

    if not args.address:
        # 交互模式
        print("🌍 高德地图经纬度查询 (严格模式)")
        print("   提示: 输入什么查什么，不会自动补全'站'字或拆分城市。")
        print("   输入 q 退出\n")
        while True:
            addr = input("请输入地址: ").strip()
            if addr.lower() in ['q', 'quit', 'exit']:
                break
            if not addr:
                continue
            run_query(addr)
            print("-" * 30)
    else:
        # 命令行模式
        run_query(args.address)

if __name__ == "__main__":
    main()