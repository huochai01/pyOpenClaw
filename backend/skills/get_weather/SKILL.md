---
name: get_weather
description: 获取指定城市的实时天气信息
---

## 步骤
1. 使用 `fetch_url` 工具访问 `https://wttr.in/{城市名}?format=j1`
2. 从返回的 JSON 中提取当前天气、体感温度、湿度和风速
3. 用简洁自然的中文回复用户
