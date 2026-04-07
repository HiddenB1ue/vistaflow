from __future__ import annotations

import csv
import random
import time
from pathlib import Path
from typing import Any

import httpx

# 基础请求头，保持与浏览器访问行为接近。
BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://kyfw.12306.cn",
    "Referer": "https://kyfw.12306.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# 12306 车次经停查询接口。
TRAIN_STOPS_URL = "https://kyfw.12306.cn/otn/queryTrainInfo/query"
STOP_FIELDNAMES = [
    "train_no",
    "train_date",
    "station_no",
    "station_name",
    "station_train_code",
    "arrive_time",
    "start_time",
    "running_time",
    "arrive_day_diff",
    "arrive_day_str",
    "is_start",
    "start_station_name",
    "end_station_name",
    "train_class_name",
    "service_type",
    "wz_num",
]


def normalize_train_date(train_date: str) -> str:
    """将日期标准化为 YYYY-MM-DD。"""
    # 支持传入 YYYYMMDD，便于和现有脚本配置保持一致。
    value = train_date.strip()
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    # 已是 YYYY-MM-DD 则直接返回。
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        return value
    raise ValueError("train_date must be YYYY-MM-DD or YYYYMMDD")


def build_query_params(train_no: str, train_date: str, rand_code: str) -> dict[str, str]:
    """构造经停查询请求参数。"""
    # 接口需要 leftTicketDTO.train_no / leftTicketDTO.train_date / rand_code。
    return {
        "leftTicketDTO.train_no": train_no,
        "leftTicketDTO.train_date": train_date,
        "rand_code": rand_code,
    }


def fetch_train_stops_payload(
    client: httpx.Client,
    train_no: str,
    train_date: str,
    rand_code: str,
    max_retries: int,
    retry_sleep_sec: float,
    block_pause_sec: float,
) -> dict[str, Any]:
    """请求 12306 经停接口并返回原始 JSON 响应。"""
    # 统一参数，重试时复用同一批请求参数。
    params = build_query_params(train_no=train_no, train_date=train_date, rand_code=rand_code)
    last_error = "unknown"

    # 简单重试逻辑：网络异常/状态码异常都进行有限次重试。
    for attempt in range(1, max_retries + 1):
        try:
            response = client.get(
                TRAIN_STOPS_URL,
                params=params,
                headers=BASE_HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            # 接口 status=False 视为业务失败。
            if not payload.get("status"):
                raise RuntimeError(f"12306 query failed: status={payload.get('status')}")
            return payload
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            last_error = f"HTTPStatus({status_code})"
            # 命中 403/429 时长暂停并退避重试同一车次。
            if status_code in (403, 429) and attempt < max_retries:
                pause_sec = block_pause_sec * (2 ** (attempt - 1)) + random.uniform(0.0, 5.0)
                print(
                    f"train_no={train_no}: hit {status_code}, pause {pause_sec:.1f}s, "
                    "then retry same train."
                )
                time.sleep(pause_sec)
                continue
            if attempt < max_retries:
                time.sleep(retry_sleep_sec * attempt + random.uniform(0.0, 1.0))
                continue
            break
        except httpx.RequestError as exc:
            last_error = f"{exc.__class__.__name__}"
            if attempt < max_retries:
                time.sleep(retry_sleep_sec * attempt + random.uniform(0.0, 1.0))
                continue
            break
        except Exception as exc:
            last_error = f"{exc.__class__.__name__}"
            if attempt < max_retries:
                time.sleep(retry_sleep_sec * attempt + random.uniform(0.0, 1.0))
                continue
            break

    raise RuntimeError(
        f"train_no={train_no}: failed after {max_retries} attempts, last={last_error}"
    )


def extract_stop_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """从接口响应中提取经停数组 data.data。"""
    # 接口结构为 {"data": {"data": [...]}}。
    data_block = payload.get("data")
    if not isinstance(data_block, dict):
        return []
    rows = data_block.get("data")
    if not isinstance(rows, list):
        return []
    return rows


def to_int(value: Any) -> int | None:
    """将字符串数字转换为 int，无法转换时返回 None。"""
    text = str(value or "").strip()
    if text.isdigit():
        return int(text)
    return None


def normalize_stop_row(row: dict[str, Any], train_no: str, train_date: str) -> dict[str, Any]:
    """将原始经停记录规范化为稳定字段。"""
    # 统一字段名，便于后续 CSV 导出和数据库入库。
    return {
        "train_no": train_no,
        "train_date": train_date,
        "station_no": to_int(row.get("station_no")),
        "station_name": row.get("station_name"),
        "station_train_code": row.get("station_train_code"),
        "arrive_time": row.get("arrive_time"),
        "start_time": row.get("start_time"),
        "running_time": row.get("running_time"),
        "arrive_day_diff": to_int(row.get("arrive_day_diff")),
        "arrive_day_str": row.get("arrive_day_str"),
        "is_start": row.get("is_start"),
        "start_station_name": row.get("start_station_name"),
        "end_station_name": row.get("end_station_name"),
        "train_class_name": row.get("train_class_name"),
        "service_type": row.get("service_type"),
        "wz_num": row.get("wz_num"),
    }


def dump_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    """将规范化经停结果写入 CSV 文件。"""
    # 固定列顺序，便于后续处理。
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=STOP_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def default_output_path(output_dir: Path, train_no: str, train_date: str) -> Path:
    """生成每个车次经停 CSV 的默认输出路径。"""
    # 文件名包含 train_no 与日期，方便多次抓取区分。
    date_token = train_date.replace("-", "")
    return output_dir / f"train_stops_{train_no}_{date_token}.csv"


def read_train_tasks_from_catalog(catalog_csv_path: Path) -> list[tuple[str, str]]:
    """从 trains_all CSV 读取 (train_no, train_date) 唯一任务列表。"""
    with catalog_csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if "train_no" not in reader.fieldnames or "date" not in reader.fieldnames:
            raise ValueError("catalog csv must contain columns: train_no, date")

        tasks: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        invalid_rows = 0
        for row in reader:
            train_no = (row.get("train_no") or "").strip()
            date_raw = (row.get("date") or "").strip()
            if not train_no:
                invalid_rows += 1
                continue

            try:
                train_date = normalize_train_date(date_raw)
            except ValueError:
                invalid_rows += 1
                continue

            key = (train_no, train_date)
            if key in seen:
                continue
            seen.add(key)
            tasks.append(key)

    if invalid_rows:
        print(f"ignored invalid rows: {invalid_rows}")
    return tasks


def dump_failed_tasks(rows: list[dict[str, str]], output_path: Path) -> None:
    """将失败任务写入 CSV，方便后续补抓。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["train_no", "train_date", "error"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """脚本入口：从 trains_all CSV 批量抓取经停，并按车次写入独立 CSV。"""
    # ===== 手动修改区（按需改这几项即可）=====
    catalog_csv_path = Path("test/output/trains_20260306.csv")
    output_dir = Path("test/output/train_stops_20260306/")
    rand_code = ""
    max_retries = 3
    retry_sleep_sec = 1.0
    block_pause_sec = 60.0
    request_sleep_min_sec = 0.2  # 1.2
    request_sleep_max_sec = 0.3  # 2.8
    cooldown_every = 200
    cooldown_sec = 45.0
    skip_existing = True
    max_tasks: int | None = None  # 调试时可设为 100 之类限制抓取规模。
    # ========================================

    if not catalog_csv_path.exists():
        raise FileNotFoundError(f"catalog csv not found: {catalog_csv_path}")
    if request_sleep_min_sec > request_sleep_max_sec:
        raise ValueError("request_sleep_min_sec must be <= request_sleep_max_sec")

    tasks = read_train_tasks_from_catalog(catalog_csv_path)
    if max_tasks is not None:
        tasks = tasks[: max(0, max_tasks)]
    if not tasks:
        print("no valid train tasks found.")
        return

    print(f"catalog: {catalog_csv_path}")
    print(f"tasks: {len(tasks)}")
    print(f"output dir: {output_dir}")

    failed_tasks: list[dict[str, str]] = []
    success_count = 0
    skipped_count = 0
    start_ts = time.time()

    # 单连接 + 低频请求，显著降低封禁风险。
    with httpx.Client(
        limits=httpx.Limits(max_connections=5, max_keepalive_connections=2),
        timeout=20.0,
    ) as client:
        for index, (train_no, train_date) in enumerate(tasks, start=1):
            output_csv = default_output_path(
                output_dir=output_dir,
                train_no=train_no,
                train_date=train_date,
            )
            if skip_existing and output_csv.exists():
                skipped_count += 1
                print(f"[{index}/{len(tasks)}] skip existing: {output_csv.name}")
                continue

            print(f"[{index}/{len(tasks)}] crawl train_no={train_no} date={train_date}")
            try:
                payload = fetch_train_stops_payload(
                    client=client,
                    train_no=train_no,
                    train_date=train_date,
                    rand_code=rand_code,
                    max_retries=max(1, max_retries),
                    retry_sleep_sec=max(0.0, retry_sleep_sec),
                    block_pause_sec=max(5.0, block_pause_sec),
                )
                raw_rows = extract_stop_rows(payload)
                rows = [
                    normalize_stop_row(row=row, train_no=train_no, train_date=train_date)
                    for row in raw_rows
                ]
                dump_csv(rows, output_csv)
                success_count += 1
                print(f"  -> saved {len(rows)} stops: {output_csv.name}")
            except Exception as exc:
                error_text = f"{exc.__class__.__name__}: {exc}"
                failed_tasks.append(
                    {
                        "train_no": train_no,
                        "train_date": train_date,
                        "error": error_text,
                    }
                )
                print(f"  -> failed: {error_text}")

            # 请求间随机抖动，降低固定频率触发风控的概率。
            if cooldown_every > 0 and index % cooldown_every == 0:
                cooldown = cooldown_sec + random.uniform(0.0, max(1.0, cooldown_sec * 0.3))
                print(f"cooldown after {index} requests: sleep {cooldown:.1f}s")
                time.sleep(cooldown)
            else:
                jitter = random.uniform(request_sleep_min_sec, request_sleep_max_sec)
                time.sleep(jitter)

    elapsed_sec = time.time() - start_ts
    print("crawl done.")
    print(f"success: {success_count}")
    print(f"skipped: {skipped_count}")
    print(f"failed: {len(failed_tasks)}")
    print(f"elapsed: {elapsed_sec:.1f}s")

    if failed_tasks:
        failed_csv = output_dir / f"train_stops_failed_{catalog_csv_path.stem}.csv"
        dump_failed_tasks(failed_tasks, failed_csv)
        print(f"failed tasks csv: {failed_csv}")


if __name__ == "__main__":
    main()
