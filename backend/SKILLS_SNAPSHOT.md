<available_skills>
  <skill>
    <name>ai-news-daily</name>
    <description>获取当日最新 AI 领域资讯、前沿研究动态与行业新闻。当用户询问"今天 AI 有什么新动向"、"最新的 AI 新闻"、"AI 领域最近发生了什么"、"帮我整理今日 AI 资讯"、"大模型有什么新进展"、"AI 公司最新动态"等相关问题时，务必使用此 skill。即使用户只是随口提到想了解 AI 动态、科技前沿、大模型进展，也应积极触发此 skill。适用于晨报整理、行业研究、竞品追踪、学术跟进等多种场景。</description>
    <location>./skills/ai-news-daily/SKILL.md</location>
  </skill>
  <skill>
    <name>get_weather</name>
    <description>获取指定城市的实时天气信息</description>
    <location>./skills/get_weather/SKILL.md</location>
  </skill>
  <skill>
    <name>scheduled_tasks</name>
    <description>用于创建、查看、取消定时任务。用户提到“每天提醒我”“定时提醒”“每天早上/晚上做某事”“每天获取天气发给我”“帮我设一个定时任务”等情况时使用。</description>
    <location>./skills/scheduled_tasks/SKILL.md</location>
  </skill>
  <skill>
    <name>self-evolution</name>
    <description>当一个任务首次执行失败，但在重试其他工具、接口、参数或流程后成功时，使用此技能总结可复用经验，并将经验同时写入当前正在使用的 SKILL.md 与 memory/MEMORY.md。适用于 API 失败后切换备用 API、命令失败后改用其他命令、抓取失败后改用其他数据源、解析失败后改用其他流程等场景。</description>
    <location>./skills/self-evolution/SKILL.md</location>
  </skill>
  <skill>
    <name>web_search</name>
    <description>使用 Tavily 联网搜索最新网页信息、新闻、资料和事实。用户提到“搜索”“联网查一下”“帮我查最新”“看看网上怎么说”或需要实时网页结果时使用。</description>
    <location>./skills/web_search/SKILL.md</location>
  </skill>
</available_skills>
