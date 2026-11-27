"""Watcher for the Ao Ying heartbeat dead-man switch.

Runs in GitHub Actions every 10 minutes (see heartbeat-watch.yml).
Reads heartbeat.json from the repo root, compares each instance's last
fresh-poll timestamp against now; stale = missing/unparseable OR age > 600s.
  - stale + no open issue  -> create one `[心跳告警] <实例>轮询已停`
                             (label heartbeat-stale)
  - stale + open issue    -> do nothing (one alert per outage, no spam)
  - fresh + open issue    -> close it with a recovery comment
  - heartbeat.json missing/unreadable -> BOTH instances stale
Uses only the built-in GITHUB_TOKEN via the `gh` CLI.
"""

import datetime
import json
import subprocess

STALE_SECS = 600
REPO = "hyh120942-lang/aoying-heartbeat"
UTC = datetime.timezone.utc
CST = datetime.timezone(datetime.timedelta(hours=8))
INSTANCES = {
    "aoying_user": "熬鹰阿海",
    "aoying_friend": "熬鹰阿斌",
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_ts(raw):
    try:
        dt = datetime.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
        return dt.replace(tzinfo=UTC)
    except Exception:
        return None


def fmt_both(dt):
    return (
        f"{dt.strftime('%Y-%m-%d %H:%M:%S')} UTC / "
        f"{dt.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')} CST"
    )


def main():
    now = datetime.datetime.now(UTC)
    try:
        with open("heartbeat.json") as f:
            hb = json.load(f)
    except Exception as e:
        print(f"heartbeat.json unreadable ({e}); treating BOTH as stale")
        hb = {}

    # Ensure the label exists (no-op if it already does).
    run(["gh", "label", "create", "heartbeat-stale", "--repo", REPO,
         "--color", "B60205",
         "--description", "Robot polling stopped (external heartbeat)"])

    open_issues = run(["gh", "issue", "list", "--repo", REPO, "--label", "heartbeat-stale",
                       "--state", "open", "--json", "number,title"])
    try:
        issues = json.loads(open_issues.stdout or "[]")
    except Exception:
        issues = []
    by_display = {}
    for it in issues:
        for key, display in INSTANCES.items():
            if display in it.get("title", ""):
                by_display[key] = it["number"]

    for key, display in INSTANCES.items():
        ts = parse_ts(str(hb.get(key, "")))
        age = (now - ts).total_seconds() if ts else None
        stale = ts is None or age > STALE_SECS
        n = by_display.get(key)
        if stale:
            age_min = f"{age / 60:.1f}" if age is not None else "未知（无时间戳）"
            last = fmt_both(ts) if ts else "无（未收到过心跳）"
            if n:
                print(f"{key} STALE age={age_min}min, issue #{n} already open, skip")
            else:
                title = f"[心跳告警] {display}轮询已停"
                body = (
                    f"【熬鹰机器人机外心跳告警】\n\n"
                    f"实例：{display} ({key})\n"
                    f"最后心跳：{last}\n"
                    f"已停：约 {age_min} 分钟\n\n"
                    f"含义：机器人轮询已停止，或整台虚拟机已死。"
                    f"本机看门狗无法发现整机死亡，这条告警是唯一的机外信号。"
                    f"请检查虚拟机 / sing-box / 轮询状态。\n\n"
                    f"恢复后本 issue 会由 watcher 自动关闭。"
                )
                r = run(["gh", "issue", "create", "--repo", REPO, "--title", title,
                         "--body", body, "--label", "heartbeat-stale"])
                if r.returncode == 0:
                    print(f"{key} STALE age={age_min}min, created issue: {r.stdout.strip()}")
                else:
                    print(f"{key} STALE but issue create FAILED: {r.stdout} {r.stderr}")
        else:
            if n:
                comment = f"已恢复：轮询恢复，最后心跳 {fmt_both(ts)}。"
                r = run(["gh", "issue", "close", str(n), "--repo", REPO, "--comment", comment])
                print(f"{key} fresh age={age:.0f}s, closed issue #{n} (rc={r.returncode})")
            else:
                print(f"{key} fresh age={age:.0f}s, no open issue")


if __name__ == "__main__":
    main()
