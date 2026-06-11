# Epic 免费游戏提醒 🎮

[English](README.md) | [简体中文](README_zh.md)

通过 [Server酱](https://sct.ftqq.com/) 获取 Epic Games Store 免费游戏的自动通知，直接发送到你的微信。

![示例通知](https://github.com/user-attachments/assets/1a82c313-7407-4679-9abd-8da7d51c068d)
*（示例通知显示当前和即将免费的游戏）*

## 功能特性 ✨
- ✅ **智能持续检查** - 全天候 24/7 运行，具有智能睡眠调度
- 🔍 清晰区分**当前可领取**和**即将免费**的游戏
- 💾 自动缓存防止重复提醒
- 🎮 完美支持 **Pterodactyl/Jexactyl** 游戏面板托管
- 🏃 完全独立 - 无需外部依赖

## 工作原理 🔄

提醒器持续运行并智能调度：
1. **检查免费游戏** - 每次唤醒时都会检查
2. **智能通知**：
   - 仅当**新的当前免费游戏**出现时发送提醒（与缓存对比）
   - 始终显示**即将免费**的游戏供参考
   - 当检测到新的当前游戏时自动更新缓存
3. **智能睡眠**调度：
   - 如果存在即将推出的游戏：睡眠到最早的即将游戏开始时间 + 10 分钟
   - 如果没有即将推出的游戏：睡眠到下一个 11:10（可配置）
4. **永久运行** - 完美适配 Pterodactyl/Jexactyl 等 Always-On 托管

## Pterodactyl/Jexactyl 设置 🚀

### 第 1️⃣ 步：获取 Server酱 Key
1. 访问 [Server酱](https://sct.ftqq.com/)（使用 GitHub 登录）
2. 复制你的 `SendKey`（格式类似 `SCT123456...`）

### 第 2️⃣ 步：配置提醒器
在 `app.py` 中，将占位符密钥替换为你的实际密钥：
```python
SERVER_CHAN_KEY = "你的实际SendKey"
```

可选地，调整时区和每日检查时间：
```python
TIME_ZONE = "UTC"  # 改为你的时区
sleep_until(11, 10)             # 每天 11:10 进行检查（基于你的时区）
```

### 第 3️⃣ 步：在游戏面板上部署

**对于 Pterodactyl/Jexactyl：**
1. 在游戏面板中创建一个新的"服务器"
2. 上传以下文件到服务器：
   - `app.py`
   - `requirements.txt`
3. 确保启动命令和设置指向正确的文件
4. 启动服务器 - 它将持续运行

### 第 4️⃣ 步：验证是否正常工作
- 在面板中检查**控制台输出**
- 你应该看到类似的日志：
  ```
  2026-06-07 11:10:00 EST - New games found
  Sleeping until 2026-06-12 12:34:56 EST (432000 seconds)
  ```

## 故障排查 🛠️

| 问题症状 | 解决方法 |
|---------|--------|
| 没有收到通知 | 1. 手动测试 Server酱 密钥：<br>`curl -X POST "https://sctapi.ftqq.com/YOUR_KEY.send" -d "title=Test&desp=Hello"`<br>2. 检查服务器控制台输出 |
| 导入错误：找不到 'requests' | 运行：`pip install requests`（或让面板从 requirements.txt 自动安装） |
| 显示的游戏错误 | 删除服务器存储中的 `games_cache.json`，然后重启 |
| API 错误 | 等待 1 小时（Epic 有时会有速率限制） |

## 高级配置 ⚙️

**更改每日检查时间：**
编辑 `app.py` 中的最后一个 `sleep_until()` 调用：
```python
sleep_until(16, 30)  # 从 11:10 改为 16:30（基于你的时区）
```

**更改时区：**
```python
TIME_ZONE = "Europe/London"  # 时区列表: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

**增加检查延迟：**
修改最早即将推出游戏的偏移量：
```python
target_time = earliest_upcoming + timedelta(minutes=20)  # 从 10 改为 20 分钟
```

## 系统要求 📦

- Python 3.9+
- `requests` 库（见 `requirements.txt`）
- 网络连接
- 有效的 Server酱 账户

---

享受你的免费游戏！🎁  
*如果你觉得这个项目有用，请考虑给它一个 Star！*
