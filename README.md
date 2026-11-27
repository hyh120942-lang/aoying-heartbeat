# 熬鹰跟单机器人 · 机外心跳监控（GitHub 版）

> 为什么不用 Healthchecks：2026-11-27 注册时魔法链接邮件 25 分钟以上未送达
> hyh120942@gmail.com（收件箱/垃圾邮件均无），改走 GitHub Actions。

## 这是什么

一个死人开关（dead-man switch）。虚拟机上的机器人每 2 分钟向本仓库推一次
`heartbeat.json`；GitHub Actions 每 10 分钟检查一次，任一实例的心跳超过
10 分钟未更新就开一个告警 issue，轮询恢复后自动关闭。

- **告警延迟**：最后一次新鲜心跳后约 10–20 分钟（含 Actions 定时调度延迟）。
- **不 spam**：同一实例的告警 issue 已存在时不再重复创建。
- **恢复通知**：轮询恢复后 watcher 自动关闭 issue 并留言最后心跳时间。

## 仓库里有什么

| 文件 | 说明 |
| --- | --- |
| `heartbeat.json` | 两个实例最后一次新鲜轮询的时间戳（UTC），每 2 分钟更新 |
| `.github/workflows/heartbeat-watch.yml` | 每 10 分钟检查心跳、管理告警 issue |
| `README.md` | 本文件 |

## 仓库里没有什么

**没有密钥、没有钱包、没有持仓、没有交易数据。**只有时间戳。
仓库是公开的（Actions 免费分钟数：私有仓库每月 2000 分钟免费额度不够
10 分钟一轮的调度，公开仓库不限量）。

## 告警去向（与原计划的偏差）

告警以 GitHub issue 形式发出，GitHub 通知邮件发到 GitHub 账号邮箱
hyh120942@gmail.com，**不是**原来的故障告警邮箱 2472737098@qq.com。
要改发 QQ 邮箱需另配 Gmail SMTP 应用专用密码作仓库 secret，那是后续事项，
本次未做。

## 推送端

虚拟机上的推送脚本：`github_heartbeat_push.py`（每 2 分钟 cron 运行）。
只推新鲜的心跳（last_poll 年龄 ≤ 300 秒）；过期/读不到的实例直接省略，
绝不把旧时间戳当新鲜推。认证走本机已登录的 `gh` CLI，不存 token。

## 测试

- 手动跑一次 watcher：Actions 页 → heartbeat-watch → Run workflow。
- 告警测试：推一份旧时间戳的 heartbeat.json → 手动跑 watcher → 应开 issue；
  再推新鲜时间戳 → 再跑 watcher → issue 应自动关闭。
