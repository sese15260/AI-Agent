from collections import defaultdict
from statistics import mean


def summarize(rows):
    rows = sorted(rows, key=lambda x: x["date"])
    if not rows:
        return {"symbol": "005930", "name": "삼성전자", "unit": "KRW", "period": None, "count": 0, "metrics": None, "trend": "데이터 없음", "trend_method": "비교 불가", "monthly": [], "recent": []}
    values = [float(row["value"]) for row in rows]
    recent = values[-20:]
    up_days = 0
    down_days = 0
    flat_days = 0

    for i in range(1, len(recent)):
        if recent[i] > recent[i - 1]:
            up_days += 1
        elif recent[i] < recent[i - 1]:
            down_days += 1
        else:
            flat_days += 1
    change = (recent[-1] / recent[0] - 1) * 100 if len(recent) > 1 else 0
    direction = "상승" if change > 1 else "하락" if change < -1 else "보합"
    max_row = max(rows, key=lambda x: float(x["value"]))
    min_row = min(rows, key=lambda x: float(x["value"]))
    months = defaultdict(list)
    for row in rows:
        months[row["date"][:7]].append(float(row["value"]))
    return {
        "symbol": "005930", "name": "삼성전자", "unit": "KRW",
        "period": {"start": rows[0]["date"], "end": rows[-1]["date"]},
        "count": len(rows),
        "metrics": {"average": round(mean(values), 2), "max": max(values), "max_date": max_row["date"], "min": min(values), "min_date": min_row["date"], "latest": values[-1], "latest_date": rows[-1]["date"], "first": values[0], "total_change_percent": round((values[-1] / values[0] - 1) * 100, 2), "recent_change_percent": round(change, 2)},
        "recent_daily_counts": {
            "up": up_days,
            "down": down_days,
            "flat": flat_days
        },
        "trend": f"최근 {len(recent)}거래일 {direction} ({change:+.2f}%)",
        "trend_method": "최근 거래일 구간의 첫 종가와 마지막 종가 비교",
        "monthly": [{"month": month, "average": round(mean(items), 2)} for month, items in sorted(months.items())],
        "recent": [{"date": row["date"], "value": float(row["value"])} for row in rows[-20:]],
    }
