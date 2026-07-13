import fs from "node:fs";
import path from "node:path";

const outDir = path.resolve("docs");

const sharedStyle = `
  :root {
    --ink: #172033;
    --muted: #40506a;
    --blue: #2563eb;
    --teal: #0f8a79;
    --green: #2f7d4f;
    --amber: #b7791f;
    --rose: #be3a5d;
    --violet: #6d5bd0;
    --line: #d4deee;
    --paper: #fffdf8;
  }

  * { box-sizing: border-box; }

  html, body {
    margin: 0;
    min-height: 100%;
    background: #ebeef5;
    color: var(--ink);
    font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  }

  body {
    display: grid;
    place-items: center;
    padding: 16px;
  }

  .deck {
    width: min(100vw - 32px, 1120px);
    aspect-ratio: 4 / 3;
    position: relative;
    background: var(--paper);
    border: 1px solid #cfd7e6;
    border-radius: 8px;
    box-shadow: 0 24px 70px rgba(15, 23, 42, .15);
    overflow: hidden;
  }

  .deck::before {
    content: "";
    position: absolute;
    inset: 0 0 auto 0;
    height: 10px;
    background: linear-gradient(90deg, #2563eb, #0f8a79, #d97706, #be3a5d, #6d5bd0);
    z-index: 4;
  }

  .slide {
    position: absolute;
    inset: 0;
    display: none;
    padding: 46px 42px 48px;
    background: var(--paper);
  }

  .slide.active { display: block; }

  .slide-inner {
    height: 100%;
    display: grid;
    align-content: start;
    gap: 12px;
  }

  .eyebrow {
    color: var(--blue);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-size: 15px;
    font-weight: 900;
  }

  h1, h2, h3, p { margin: 0; }

  h1 {
    max-width: 920px;
    font-size: 52px;
    line-height: 1.05;
    letter-spacing: 0;
  }

  h2 {
    max-width: 980px;
    font-size: 40px;
    line-height: 1.1;
    letter-spacing: 0;
  }

  h3 {
    margin-bottom: 8px;
    font-size: 22px;
    line-height: 1.18;
  }

  .lead {
    max-width: 980px;
    color: var(--muted);
    font-size: 21px;
    line-height: 1.45;
  }

  .subtitle {
    max-width: 820px;
    color: var(--muted);
    font-size: 24px;
    line-height: 1.42;
  }

  .grid {
    display: grid;
    gap: 14px;
  }

  .two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .four { grid-template-columns: repeat(4, minmax(0, 1fr)); }

  .panel {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    padding: 17px 18px;
    min-width: 0;
  }

  .panel.blue { background: #eff6ff; border-color: #bfdbfe; }
  .panel.teal { background: #ecfdf5; border-color: #99f6e4; }
  .panel.green { background: #f0fdf4; border-color: #bbf7d0; }
  .panel.amber { background: #fffbeb; border-color: #fde68a; }
  .panel.rose { background: #fff1f2; border-color: #fecdd3; }
  .panel.violet { background: #f5f3ff; border-color: #ddd6fe; }

  .panel p, .panel li {
    color: var(--muted);
    font-size: 16px;
    line-height: 1.45;
  }

  ul {
    margin: 8px 0 0;
    padding-left: 20px;
  }

  li + li { margin-top: 6px; }

  .tag {
    display: inline-block;
    margin-bottom: 12px;
    padding: 5px 10px;
    border-radius: 999px;
    background: var(--blue);
    color: white;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .8px;
    text-transform: uppercase;
  }

  .tag.teal { background: var(--teal); }
  .tag.green { background: var(--green); }
  .tag.amber { background: var(--amber); }
  .tag.rose { background: var(--rose); }
  .tag.violet { background: var(--violet); }

  .flow {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
    align-items: stretch;
  }

  .flow.six { grid-template-columns: repeat(6, minmax(0, 1fr)); }

  .step {
    position: relative;
    min-height: 138px;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    padding: 14px;
  }

  .step::after {
    content: "";
    position: absolute;
    top: 50%;
    right: -10px;
    width: 10px;
    border-top: 2px solid #a8b5c8;
  }

  .step:last-child::after { display: none; }

  .num {
    display: inline-grid;
    place-items: center;
    width: 26px;
    height: 26px;
    margin-bottom: 10px;
    border-radius: 50%;
    background: var(--blue);
    color: white;
    font-weight: 900;
  }

  .num.teal { background: var(--teal); }
  .num.green { background: var(--green); }
  .num.amber { background: var(--amber); }
  .num.rose { background: var(--rose); }
  .num.violet { background: var(--violet); }

  .step b {
    display: block;
    margin-bottom: 8px;
    font-size: 17px;
    line-height: 1.22;
  }

  .step small {
    display: block;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.38;
  }

  .example {
    display: block;
    border: 1px solid #29364b;
    border-radius: 8px;
    background: #111827;
    color: #e5edf8;
    padding: 14px 16px;
    font-family: "Cascadia Mono", Consolas, monospace;
    font-size: 14px;
    line-height: 1.55;
    min-height: 96px;
    white-space: pre-wrap;
  }

  .script {
    display: grid;
    gap: 10px;
  }

  .script-row {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 12px;
    align-items: start;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    padding: 14px 16px;
    min-height: 66px;
  }

  .script-row b {
    color: var(--blue);
    font-size: 15px;
  }

  .script-row span {
    color: var(--muted);
    font-size: 15px;
    line-height: 1.42;
  }

  .matrix {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: #ffffff;
    font-size: 15px;
  }

  .matrix th,
  .matrix td {
    padding: 9px 11px;
    border-right: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
    vertical-align: top;
    line-height: 1.38;
  }

  .matrix th {
    background: #eaf0f8;
    text-align: left;
  }

  .matrix tr:last-child td { border-bottom: 0; }
  .matrix th:last-child, .matrix td:last-child { border-right: 0; }

  .note {
    border-left: 5px solid var(--blue);
    background: #f8fbff;
    padding: 15px 18px;
    border-radius: 8px;
    color: var(--muted);
    font-size: 18px;
    line-height: 1.45;
  }

  .classroom {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-top: 0;
  }

  .classroom div {
    border: 1px solid #d8e2f2;
    border-radius: 8px;
    background: #fbfdff;
    padding: 10px 12px;
    min-height: 78px;
    min-width: 0;
  }

  .classroom b {
    display: block;
    margin-bottom: 4px;
    color: #1d4ed8;
    font-size: 13.5px;
  }

  .classroom span {
    display: block;
    color: #40506a;
    font-size: 12.5px;
    line-height: 1.34;
  }

  .case-lab {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 0;
  }

  .case-lab div {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    padding: 11px 13px;
    min-height: 84px;
  }

  .case-lab b {
    display: block;
    margin-bottom: 4px;
    color: #172033;
    font-size: 14px;
  }

  .case-lab span {
    display: block;
    color: #40506a;
    font-size: 12.5px;
    line-height: 1.38;
  }

  .mini-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .mini-row.three {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .mini-card {
    border: 1px solid #d8e2f2;
    border-radius: 8px;
    background: #ffffff;
    padding: 10px 12px;
    min-height: 72px;
  }

  .mini-card b {
    display: block;
    margin-bottom: 4px;
    color: #172033;
    font-size: 14px;
  }

  .mini-card span {
    display: block;
    color: #40506a;
    font-size: 12.5px;
    line-height: 1.36;
  }

  .mini-card a {
    color: #1d4ed8;
    font-weight: 800;
    text-decoration: none;
  }

  .mini-card code {
    display: block;
    margin-top: 4px;
    color: #64748b;
    font-size: 11px;
    white-space: normal;
  }

  .slide:not(.cover) .grid.three > .panel {
    min-height: 154px;
    padding: 22px;
  }

  .slide:not(.cover) .grid.four > .panel {
    min-height: 166px;
    padding: 20px;
  }

  .slide:not(.cover) .grid.two > .panel {
    min-height: 176px;
    padding: 24px;
  }

  .slide:not(.cover) .panel p,
  .slide:not(.cover) .panel li {
    font-size: 17px;
    line-height: 1.52;
  }

  .slide:not(.cover) .flow .step {
    min-height: 174px;
    padding: 18px 15px;
  }

  .slide:not(.cover) .step small {
    font-size: 14px;
    line-height: 1.48;
  }

  .slide:not(.cover) .matrix th,
  .slide:not(.cover) .matrix td {
    padding: 13px 14px;
    font-size: 16px;
    line-height: 1.46;
  }

  .bottom {
    position: absolute;
    left: 42px;
    right: 42px;
    bottom: 28px;
    display: flex;
    justify-content: space-between;
    color: #9aa7bb;
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
  }

  .controls {
    position: fixed;
    left: 50%;
    bottom: 18px;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 10px;
    border: 1px solid #d7deea;
    border-radius: 999px;
    background: rgba(255, 255, 255, .92);
    box-shadow: 0 8px 28px rgba(15, 23, 42, .12);
    z-index: 20;
  }

  .nav-button {
    width: 34px;
    height: 34px;
    border: 0;
    border-radius: 50%;
    background: #172033;
    color: #ffffff;
    cursor: pointer;
    font-size: 24px;
    line-height: 1;
  }

  .counter {
    min-width: 58px;
    color: #40506a;
    font-size: 13px;
    text-align: center;
    font-weight: 800;
  }

  @media print {
    @page { size: 10in 7.5in; margin: 0; }
    body { display: block; padding: 0; background: white; }
    .deck { width: 10in; height: 7.5in; aspect-ratio: auto; border: 0; border-radius: 0; box-shadow: none; overflow: visible; }
    .slide { position: relative; display: block !important; width: 10in; height: 7.5in; page-break-after: always; break-after: page; }
    .slide:last-child { page-break-after: auto; break-after: auto; }
    .controls { display: none; }
  }
`;

const decks = [
  {
    file: "ai-coding-finance-course-01-ai-assistant-basics.html",
    code: "Course 01",
    title: "第 1 期：从豆包开始，把 AI 当成协作同事",
    subtitle: "面向金融中队的 AI Coding 入门系列。先不讲代码，先学会把日常问题说清楚、让 AI 给出可检查的产物。",
    slides: [
      {
        eyebrow: "AI Basics",
        title: "从日常问答，到可协作的 AI 助手",
        lead: "大家已经会用豆包问日常问题。第一期的目标，是把“随便问问”升级成“让 AI 帮我完成一个可检查的小任务”。",
        html: `<div class="grid three">
          <div class="panel blue"><span class="tag">今天不讲</span><h3>代码和 Git</h3><p>先不讲仓库、分支、PR、测试这些研发术语。</p></div>
          <div class="panel teal"><span class="tag teal">今天要学</span><h3>如何提清楚问题</h3><p>让 AI 知道背景、目标、限制和输出格式。</p></div>
          <div class="panel green"><span class="tag green">今天产出</span><h3>一份问题单草稿</h3><p>把一句模糊想法整理成别人能继续处理的文字。</p></div>
        </div>`
      },
      {
        eyebrow: "Watch First",
        title: "课前观看：先熟悉豆包能做什么",
        lead: "不用一次看完。重点看“如何提问、如何改写、如何让 AI 输出结构化结果”。",
        html: `<div class="grid two">
          <div class="panel blue"><h3>豆包官方入口</h3><p>先打开豆包或安装桌面端，确认自己能登录、能输入、能复制输出。</p><p><a href="https://www.doubao.com/">doubao.com</a></p></div>
          <div class="panel green"><h3>观看目标</h3><p>看完后能回答：豆包能帮我整理什么？我怎样让它少猜？输出不好时怎样追问？</p></div>
        </div>
        <div class="mini-row">
          <div class="mini-card"><b>视频 1：豆包 AI 使用指南</b><span><a href="https://www.bilibili.com/video/BV158kKBLErq/">B站视频：超全豆包 AI 使用指南</a><code>https://www.bilibili.com/video/BV158kKBLErq/</code></span></div>
          <div class="mini-card"><b>视频 2：豆包电脑版操作</b><span><a href="https://www.bilibili.com/video/BV14dUTYbEdM/">B站视频：豆包 AI 干货教程</a><code>https://www.bilibili.com/video/BV14dUTYbEdM/</code></span></div>
        </div>`
      },
      {
        eyebrow: "Starting Point",
        title: "为什么从豆包开始，而不是直接讲 AI Coding",
        lead: "如果不会把问题讲清楚，AI Coding 只会更快地产生错误代码。AI 编程的第一步，其实是表达能力。",
        html: `<div class="grid two">
          <div class="panel rose"><span class="tag rose">常见用法</span><h3>问日常问题</h3><ul><li>“帮我写个总结”</li><li>“这个概念是什么意思”</li><li>“帮我润色一下话术”</li></ul></div>
          <div class="panel green"><span class="tag green">升级用法</span><h3>给 AI 一个可执行任务</h3><ul><li>说明背景和目标</li><li>告诉它不能假设什么</li><li>要求输出结构化结果</li><li>让它列出不确定点</li></ul></div>
        </div>
        <div class="note">这期课的关键句：AI 不是搜索框，它更像一个需要你交代上下文的协作同事。</div>`
      },
      {
        eyebrow: "Prompt Pattern",
        title: "一个好问题，至少包含四件事",
        html: `<div class="flow">
          <div class="step"><span class="num">1</span><b>背景</b><small>这件事发生在什么场景里，谁受到影响。</small></div>
          <div class="step"><span class="num teal">2</span><b>目标</b><small>你希望最后拿到什么结果。</small></div>
          <div class="step"><span class="num green">3</span><b>限制</b><small>不能编造、不能泄露、不能越过哪些边界。</small></div>
          <div class="step"><span class="num amber">4</span><b>输出格式</b><small>要表格、清单、草稿，还是下一步问题。</small></div>
          <div class="step"><span class="num rose">5</span><b>自检</b><small>要求 AI 标出假设、不确定点和需要人确认的地方。</small></div>
        </div>
        <code class="example">请基于以下背景帮我整理一份问题单草稿。
背景：管理员反馈大文件上传后经常失败，但不知道原因。
目标：让研发同事能判断是否需要修复。
限制：不要编造系统细节，不要写代码。
输出：现象、影响、已知信息、待确认问题、建议下一步。</code>`
      },
      {
        eyebrow: "Bad vs Good",
        title: "同一个问题，问法不同，结果会差很多",
        html: `<table class="matrix">
          <thead><tr><th>问法</th><th>AI 可能怎么答</th><th>问题在哪里</th></tr></thead>
          <tbody>
            <tr><td>“上传失败怎么办？”</td><td>给一堆通用建议。</td><td>不知道系统、用户、现象和目标。</td></tr>
            <tr><td>“管理员反馈大文件上传失败，请整理问题单草稿。”</td><td>输出可交给研发的结构化问题。</td><td>更接近团队协作产物。</td></tr>
            <tr><td>“如果信息不足，请先问我。”</td><td>列出缺失信息。</td><td>避免 AI 编造原因。</td></tr>
          </tbody>
        </table>
        <div class="note">第一期先练“让 AI 不乱猜”。这会直接决定后面 AI Coding 是否安全。</div>`
      },
      {
        eyebrow: "Video Demo",
        title: "课堂视频：5 分钟看懂一句话如何变成问题单",
        html: `<div class="script">
          <div class="script-row"><b>片段 1</b><span>模糊问法：“大文件上传失败，帮我看看。”观察 AI 为什么只能给通用建议。</span></div>
          <div class="script-row"><b>片段 2</b><span>四段式问法：背景、目标、限制、输出格式。观察输出如何变得更可交接。</span></div>
          <div class="script-row"><b>片段 3</b><span>追加一句：“请标出哪些内容是你假设的，哪些需要我确认。”观察 AI 如何自检。</span></div>
          <div class="script-row"><b>片段 4</b><span>把结果整理成问题单草稿：现象、影响、已知信息、待确认问题、建议下一步。</span></div>
        </div>`
      },
      {
        eyebrow: "Safety",
        title: "最早就要建立的安全边界",
        html: `<div class="grid four">
          <div class="panel rose"><h3>不要输入</h3><p>客户姓名、账号、身份证、交易明细、密钥、内部地址。</p></div>
          <div class="panel amber"><h3>不要让 AI 猜</h3><p>不知道系统细节时，让它列待确认问题。</p></div>
          <div class="panel blue"><h3>不要直接照抄</h3><p>重要结论要回到原资料或负责人处确认。</p></div>
          <div class="panel green"><h3>要留下来源</h3><p>记录输入背景、AI 输出和人工修改点。</p></div>
        </div>
        <code class="example">安全补充句：
不要使用任何真实客户信息。如果需要示例，请使用虚构数据。你不确定的地方请写“待确认”，不要自行补全。</code>`
      },
      {
        eyebrow: "Hands On",
        title: "课堂练习：把一个日常问题变成协作材料",
        html: `<div class="grid two">
          <div class="panel blue"><span class="tag">输入</span><h3>任选一个真实但脱敏的问题</h3><p>例如：“客户经理说报表看不懂”，“上传附件失败”，“流程审批太慢”。</p></div>
          <div class="panel green"><span class="tag green">输出</span><h3>一份问题单草稿</h3><ul><li>现象</li><li>影响对象</li><li>期望结果</li><li>待确认问题</li><li>建议下一步</li></ul></div>
        </div>
        <div class="note">这份草稿不是最终答案，而是让别人能接着协作的起点。</div>`
      },
      {
        eyebrow: "After Class",
        title: "课后任务和下期预告",
        html: `<div class="grid three">
          <div class="panel teal"><h3>课后 10 分钟</h3><p>用豆包整理一个工作问题，要求它输出“问题单草稿”。</p></div>
          <div class="panel amber"><h3>自检 3 问</h3><p>AI 有没有编造？有没有待确认问题？别人能不能接着处理？</p></div>
          <div class="panel violet"><h3>下期预告</h3><p>我们会把“问题单草稿”交给 AI Coding 工具，看它如何进入一个项目。</p></div>
        </div>`
      }
    ]
  },
  {
    file: "ai-coding-finance-course-02-ai-coding-first-task.html",
    code: "Course 02",
    title: "第 2 期：AI Coding 入门，一句话到一次小改动",
    subtitle: "不用先懂 Git 和 PR。先理解 AI Coding 在做什么，以及怎样让它先读、先计划、再小步修改。",
    slides: [
      {
        eyebrow: "AI Coding",
        title: "AI Coding 不是让 AI 自由写代码",
        lead: "它更像把第 1 期的问题单草稿交给一个会读项目文件、会改代码、会运行检查的助手。",
        html: `<div class="grid three">
          <div class="panel blue"><h3>它能帮你</h3><p>读项目、找相关文件、解释代码、提出修改方案。</p></div>
          <div class="panel amber"><h3>它不能替你</h3><p>决定业务边界、承担风险、确认上线质量。</p></div>
          <div class="panel green"><h3>你要学会</h3><p>让它先读清楚、说计划、列风险，再允许它动手。</p></div>
        </div>`
      },
      {
        eyebrow: "Watch First",
        title: "课前观看：先看一次 Codex 如何参与开发",
        lead: "重点不是记命令，而是观察 AI Coding 工具如何读项目、提出计划、执行修改、汇报证据。",
        html: `<div class="grid two">
          <div class="panel blue"><h3>Codex 官方入门</h3><p>了解 Codex 的定位、安装和基本使用方式。</p><p><a href="https://openai.com/codex/get-started/">OpenAI Codex Get Started</a></p></div>
          <div class="panel teal"><h3>Codex CLI 文档</h3><p>作为课后查阅材料：常用命令、运行方式、配置位置。</p><p><a href="https://developers.openai.com/codex/cli">Codex CLI Docs</a></p></div>
        </div>
        <div class="mini-row three">
          <div class="mini-card"><b>视频 1：Getting started with Codex</b><span><a href="https://www.youtube.com/watch?v=px7XlbYgk7I">OpenAI 官方 YouTube 入门视频</a><code>youtube.com/watch?v=px7XlbYgk7I</code></span></div>
          <div class="mini-card"><b>视频 2：OpenAI Codex CLI</b><span><a href="https://www.youtube.com/watch?v=FUq9qRwrDrI">Codex CLI 演示视频</a><code>youtube.com/watch?v=FUq9qRwrDrI</code></span></div>
          <div class="mini-card"><b>备用：B站搜索</b><span><a href="https://search.bilibili.com/all?keyword=OpenAI%20Codex%20%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B">OpenAI Codex 使用教程</a><code>search.bilibili.com</code></span></div>
        </div>`
      },
      {
        eyebrow: "Plain Terms",
        title: "先把研发词翻译成人话",
        html: `<table class="matrix">
          <thead><tr><th>研发词</th><th>先这样理解</th><th>你需要做什么</th></tr></thead>
          <tbody>
            <tr><td>代码仓</td><td>项目文件夹，里面放系统代码和说明。</td><td>告诉 AI 目标项目在哪里。</td></tr>
            <tr><td>Issue</td><td>问题单，记录要解决什么。</td><td>让 AI 先整理或关联问题单。</td></tr>
            <tr><td>测试</td><td>自检，证明改动没有只靠感觉。</td><td>要求 AI 说清跑了什么检查。</td></tr>
            <tr><td>PR</td><td>提交审核，让负责人看改动。</td><td>不要绕过审核直接合入。</td></tr>
          </tbody>
        </table>
        <div class="note">这一页不是让大家背术语，而是让大家知道：以后跟 AI 说话时，可以把“问题单、审核、自检”当作团队协作动作来理解。</div>`
      },
      {
        eyebrow: "Minimum Path",
        title: "最小安全链路：先读，后想，再改，最后证明",
        html: `<div class="flow">
          <div class="step"><span class="num">1</span><b>说目标</b><small>管理员要看到上传失败原因。</small></div>
          <div class="step"><span class="num teal">2</span><b>让 AI 读项目</b><small>先找入口、模块和已有能力。</small></div>
          <div class="step"><span class="num green">3</span><b>让 AI 出计划</b><small>说明要改哪里、风险是什么。</small></div>
          <div class="step"><span class="num amber">4</span><b>小步修改</b><small>只改必要范围，不顺手重写。</small></div>
          <div class="step"><span class="num rose">5</span><b>自检汇报</b><small>给出命令、结果、没覆盖的地方。</small></div>
        </div>
        <div class="note">这一期只追求“看懂一次小改动如何发生”，不追求大家立刻独立合代码。</div>`
      },
      {
        eyebrow: "Prompt 01",
        title: "操作口令：让 AI 先问清楚，而不是马上改",
        html: `<code class="example">我们要处理一个问题：管理员希望知道大文件上传失败的原因。
请先不要改代码。
请先做三件事：
1. 用通俗语言复述你理解的目标；
2. 列出你需要查看哪些项目文件或文档；
3. 列出你需要我确认的问题。</code>
        <div class="grid two">
          <div class="panel blue"><h3>好处</h3><p>避免 AI 一上来就改错方向。</p></div>
          <div class="panel amber"><h3>观察点</h3><p>它是否承认不知道，是否会先问问题。</p></div>
        </div>`
      },
      {
        eyebrow: "Prompt 02",
        title: "操作口令：让 AI 给计划，但仍然先不动手",
        html: `<code class="example">请基于你已经读取到的项目结构，给出一个最小修改计划。
要求：
1. 说明可能涉及哪些文件；
2. 说明哪些地方不能随便改；
3. 说明需要哪些自检；
4. 暂时不要编辑文件，等我确认。</code>
        <div class="grid three">
          <div class="panel blue"><h3>文件范围</h3><p>AI 应该列出它认为要看的文件，而不是含糊说“改后端”。</p></div>
          <div class="panel amber"><h3>边界提醒</h3><p>如果涉及公共接口、配置或数据库，需要停下来确认。</p></div>
          <div class="panel green"><h3>自检计划</h3><p>计划里要先写清楚后面准备用什么证明改动有效。</p></div>
        </div>`
      },
      {
        eyebrow: "Prompt 03",
        title: "操作口令：允许小步修改，并要求它汇报证据",
        html: `<code class="example">可以按照上面的最小计划进行修改。
限制：
1. 只改你计划中列出的文件；
2. 不要新增不必要的依赖；
3. 改完后说明改了什么；
4. 运行能运行的自检；
5. 明确说明没有覆盖的风险。</code>
        <div class="grid three">
          <div class="panel green"><h3>改动范围</h3><p>有没有超出计划。</p></div>
          <div class="panel teal"><h3>自检结果</h3><p>有没有命令和结果。</p></div>
          <div class="panel rose"><h3>剩余风险</h3><p>有没有说没测到什么。</p></div>
        </div>`
      },
      {
        eyebrow: "Video Demo",
        title: "课堂视频：一次“先不改代码”的 AI Coding 演示",
        html: `<div class="script">
          <div class="script-row"><b>片段 1</b><span>输入问题，并明确写上“先不要改代码”。观察 AI 是否愿意先分析。</span></div>
          <div class="script-row"><b>片段 2</b><span>让 AI 读取项目结构。观察它能否说清入口、相关文件和不确定点。</span></div>
          <div class="script-row"><b>片段 3</b><span>让 AI 输出最小计划。观察计划里有没有文件范围、边界提醒和自检方式。</span></div>
          <div class="script-row"><b>片段 4</b><span>允许小步修改。观察它最后是否汇报改动、自检、未覆盖风险。</span></div>
        </div>`
      },
      {
        eyebrow: "Practice",
        title: "课堂练习：只读演练，不要求真的改代码",
        html: `<div class="grid two">
          <div class="panel blue"><h3>练习目标</h3><p>让 AI 解释一个项目：入口在哪里、模块大概做什么、它不确定什么。</p></div>
          <div class="panel green"><h3>提交产物</h3><ul><li>AI 的目标复述</li><li>它建议查看的文件</li><li>它列出的待确认问题</li><li>你觉得它哪里可能猜错</li></ul></div>
        </div>
        <div class="note">这期结束，大家应该知道：AI Coding 的第一步不是写代码，而是让 AI 看懂问题和项目。</div>`
      }
    ]
  },
  {
    file: "ai-coding-finance-course-03-team-risk-and-quality.html",
    code: "Course 03",
    title: "第 3 期：为什么团队不能让 AI 各写各的",
    subtitle: "当每个人都能让 AI 写代码，实现功能的成本变低，但架构腐化、范围失控和验证不足会变得更隐蔽。",
    slides: [
      {
        eyebrow: "Team Risk",
        title: "AI Coding 的问题，不是“写不出来”，而是“太容易写出来”",
        html: `<div class="grid three">
          <div class="panel blue"><h3>以前</h3><p>实现成本高，很多想法停在讨论阶段。</p></div>
          <div class="panel amber"><h3>现在</h3><p>AI 很快能写出一版看似可用的代码。</p></div>
          <div class="panel rose"><h3>风险</h3><p>如果没有团队规则，大家会各自理解需求，各自改边界。</p></div>
        </div>
        <div class="note">第三期的目标，是让大家先看见风险，而不是背术语。</div>`
      },
      {
        eyebrow: "Case 01",
        title: "视频案例 A：重复造轮子",
        html: `<div class="grid two">
          <div class="panel rose"><span class="tag rose">错误演示</span><h3>AI 没看全项目</h3><p>项目里已有“上传失败原因查询”能力，但 AI 又新写了一套类似逻辑。</p></div>
          <div class="panel green"><span class="tag green">正确做法</span><h3>先让 AI 找复用候选</h3><p>要求它先回答：项目里是否已有相似能力，能否复用。</p></div>
        </div>
        <code class="example">请先查找项目里是否已有“上传失败原因”“上传状态”“错误码解释”相关能力。
在确认没有复用路径前，不要新增一套实现。</code>`
      },
      {
        eyebrow: "Case 02",
        title: "视频案例 B：改错边界",
        html: `<div class="grid two">
          <div class="panel rose"><span class="tag rose">错误演示</span><h3>为了修一个页面，改了公共接口</h3><p>短期功能好了，但其他模块调用语义被改变。</p></div>
          <div class="panel green"><span class="tag green">正确做法</span><h3>先判断是否跨边界</h3><p>如果涉及公共 API、配置语义、数据库结构，需要人确认。</p></div>
        </div>
        <div class="note">对非研发同学来说，只要记住一句话：AI 不能借一个小需求，偷偷搬动系统承重墙。</div>`
      },
      {
        eyebrow: "Case 03",
        title: "视频案例 C：只跑 happy path",
        html: `<div class="grid two">
          <div class="panel rose"><span class="tag rose">错误演示</span><h3>AI 只证明“正常情况能跑”</h3><p>没有覆盖超时、权限、空数据、异常码、回滚。</p></div>
          <div class="panel green"><span class="tag green">正确做法</span><h3>要求证据板</h3><p>写清楚测了什么、没测什么、失败后怎么恢复。</p></div>
        </div>
        <code class="example">请不要只说“测试通过”。
请列出：执行命令、覆盖场景、未覆盖场景、失败路径、回滚方案。</code>`
      },
      {
        eyebrow: "Guardrails",
        title: "四个团队护栏，用普通话理解",
        html: `<div class="grid four">
          <div class="panel blue"><h3>Work Context</h3><p>工作记录。让中断后知道做到哪、下一步是什么。</p></div>
          <div class="panel teal"><h3>Code Graph</h3><p>影响地图。让 AI 先看调用链和模块关系。</p></div>
          <div class="panel amber"><h3>Human Gate</h3><p>人工确认点。关键边界不能由 AI 自己批准。</p></div>
          <div class="panel green"><h3>Evidence Board</h3><p>证据板。用测试、风险和回滚说明完成。</p></div>
        </div>
        <div class="note">这四个护栏会在第 4 期进入正式团队流程。</div>`
      },
      {
        eyebrow: "Responsibility",
        title: "AI 不是责任边界，人仍然要负责",
        html: `<table class="matrix">
          <thead><tr><th>角色</th><th>负责什么</th><th>不能甩给 AI 的事</th></tr></thead>
          <tbody>
            <tr><td>提出需求的人</td><td>说清目标、场景和影响。</td><td>不能让 AI 代替确认真实业务目标。</td></tr>
            <tr><td>维护者/负责人</td><td>确认要不要做、边界和优先级。</td><td>不能让 AI 自己批准范围扩大。</td></tr>
            <tr><td>开发/测试</td><td>实现、自检、证据和回滚。</td><td>不能只看 AI 说“完成”。</td></tr>
          </tbody>
        </table>`
      },
      {
        eyebrow: "Video Demo",
        title: "课堂视频：同一个需求，两种 AI Coding 方式",
        html: `<div class="script">
          <div class="script-row"><b>错误路线</b><span>直接说“帮我实现上传失败原因展示”，让 AI 快速改代码，展示它可能扩大范围。</span></div>
          <div class="script-row"><b>风险提示</b><span>对照结果看三个缺口：没有确认复用、没有边界判断、没有证据。</span></div>
          <div class="script-row"><b>正确路线</b><span>让 AI 先做 Work Context、Code Graph、Human Gate、Evidence Board。</span></div>
          <div class="script-row"><b>对比结果</b><span>强调正确路线慢一点，但能被团队接住和审核。</span></div>
        </div>`
      },
      {
        eyebrow: "Practice",
        title: "课堂练习：让 AI 先做风险评估",
        html: `<code class="example">请基于下面需求，先不要写代码。
需求：管理员希望看到大文件上传失败原因。
请输出：
1. 可能复用的已有能力；
2. 可能影响的模块；
3. 需要人工确认的边界；
4. 需要哪些自检证据；
5. 如果信息不足，请列待确认问题。</code>
        <div class="note">这期结束，大家应该能识别：什么时候 AI 正在“太快地动手”。</div>`
      }
    ]
  },
  {
    file: "ai-coding-finance-course-04-ai-team-sdd-workflow.html",
    code: "Course 04",
    title: "第 4 期：AI Team SDD，把个人 AI 能力接入团队研发流程",
    subtitle: "前三期建立认知，第四期进入完整方法：从问题单到 spec、plan、tasks、实现、证据和提交审核。",
    slides: [
      {
        eyebrow: "AI Team SDD",
        title: "最终目标：让大家能参与主流研发流程",
        html: `<div class="grid three">
          <div class="panel blue"><h3>不是让每个人变成专家</h3><p>而是让大家知道如何提出问题、跟 AI 协作、交付可审核材料。</p></div>
          <div class="panel teal"><h3>不是绕过研发流程</h3><p>而是让 AI 帮你进入 issue、spec、plan、tasks 和 evidence。</p></div>
          <div class="panel green"><h3>不是 AI 自己负责</h3><p>每个阶段都有人的确认点和责任边界。</p></div>
        </div>
        <table class="matrix">
          <thead><tr><th>你说的一句话</th><th>AI 帮你整理成</th><th>团队看到的是</th></tr></thead>
          <tbody>
            <tr><td>“上传失败能不能看原因？”</td><td>问题单：用户、现象、目标、待确认问题。</td><td>可以讨论是否要做、谁负责、什么时候做。</td></tr>
            <tr><td>“这个线上问题很急。”</td><td>Bug issue：影响范围、复现信息、日志线索。</td><td>可以判断优先级、修复边界和回滚方式。</td></tr>
          </tbody>
        </table>`
      },
      {
        eyebrow: "Full Chain",
        title: "完整链路：一句话如何进入团队研发",
        html: `<div class="flow">
          <div class="step"><span class="num">1</span><b>原始需求</b><small>自然语言描述目标或现象。</small></div>
          <div class="step"><span class="num teal">2</span><b>Issue</b><small>沉淀为问题单，方便团队跟踪。</small></div>
          <div class="step"><span class="num green">3</span><b>Spec / Plan</b><small>产品角色和架构角色用文档交接。</small></div>
          <div class="step"><span class="num amber">4</span><b>Tasks / Code</b><small>开发角色按任务小步实现。</small></div>
          <div class="step"><span class="num rose">5</span><b>Evidence / PR</b><small>提交证据，进入审核。</small></div>
        </div>
        <div class="note">这就是 AI Team SDD：不是更自由地写代码，而是更可靠地协作。</div>`
      },
      {
        eyebrow: "Feature Path",
        title: "新特性怎么走：管理员查看上传失败原因",
        html: `<div class="flow six">
          <div class="step"><span class="num">1</span><b>提出目标</b><small>业务说清用户和期望结果。</small></div>
          <div class="step"><span class="num teal">2</span><b>问题单</b><small>维护者确认是否接受。</small></div>
          <div class="step"><span class="num green">3</span><b>Spec</b><small>产品角色 AI 写用户场景和验收点。</small></div>
          <div class="step"><span class="num amber">4</span><b>Plan</b><small>架构角色 AI 做影响分析。</small></div>
          <div class="step"><span class="num rose">5</span><b>Tasks</b><small>拆成接口、页面、自测任务。</small></div>
          <div class="step"><span class="num violet">6</span><b>Evidence</b><small>实现后提交证据。</small></div>
        </div>`
      },
      {
        eyebrow: "Bugfix Path",
        title: "Bugfix 怎么走：大文件上传经常超时",
        html: `<div class="flow six">
          <div class="step"><span class="num">1</span><b>现象</b><small>客服/运维记录用户影响。</small></div>
          <div class="step"><span class="num teal">2</span><b>Bug Issue</b><small>AI 补齐复现和日志问题。</small></div>
          <div class="step"><span class="num green">3</span><b>Impact</b><small>看是否跨模块或改公共接口。</small></div>
          <div class="step"><span class="num amber">4</span><b>Root Cause</b><small>形成根因假设。</small></div>
          <div class="step"><span class="num rose">5</span><b>Fix</b><small>聚焦修复，不扩大范围。</small></div>
          <div class="step"><span class="num violet">6</span><b>Evidence</b><small>复现前后对比和回滚。</small></div>
        </div>`
      },
      {
        eyebrow: "Resume",
        title: "中断后怎么接上：不要靠聊天记忆",
        html: `<div class="grid two">
          <div class="panel blue"><span class="tag">Work Context</span><h3>记录任务状态</h3><ul><li>这次任务是谁</li><li>现在停在哪一步</li><li>下一步读什么</li><li>哪些边界不能碰</li></ul></div>
          <div class="panel green"><span class="tag green">恢复方式</span><h3>下一次直接给 AI 链接</h3><p>让 AI 先读取 issue、spec、plan、tasks、context 和 evidence，再继续。</p></div>
        </div>
        <code class="example">请继续这个任务：<问题单链接或任务链接>
先读取已有 spec、plan、tasks、Work Context 和 Evidence。
不要依赖上一轮聊天记忆。</code>`
      },
      {
        eyebrow: "Role Isolation",
        title: "三个 AI 角色：上下文隔离，用文档交接",
        html: `<table class="matrix">
          <thead><tr><th>角色</th><th>负责阶段</th><th>输出给下一阶段什么</th></tr></thead>
          <tbody>
            <tr><td>产品/客户经理 AI</td><td>Specify</td><td>spec：用户、场景、目标、验收点。</td></tr>
            <tr><td>架构师 AI</td><td>Plan</td><td>plan：影响范围、边界、复用、风险。</td></tr>
            <tr><td>开发 AI</td><td>Tasks + Implement</td><td>tasks、代码改动、自测和 Evidence Board。</td></tr>
          </tbody>
        </table>
        <div class="note">这不是“一个 AI 从头聊到尾”，而是每个角色只继承文档和 issue，不继承聊天上下文。</div>`
      },
      {
        eyebrow: "Evidence",
        title: "证据板怎么写：不要只说完成",
        html: `<div class="grid two">
          <div class="panel green"><h3>必须写</h3><ul><li>改了哪些地方</li><li>为什么这样改</li><li>跑了哪些自检</li><li>哪些路径没有覆盖</li><li>出问题怎么回滚</li></ul></div>
          <div class="panel rose"><h3>不能只写</h3><ul><li>“已完成”</li><li>“测试通过”</li><li>“应该没问题”</li><li>“AI 说可以”</li></ul></div>
        </div>
        <code class="example">Evidence Board 摘要：
Scope: 上传失败原因展示。
Checks: 运行上传服务单元测试，手工验证超时错误展示。
Not covered: 真实外部存储故障未覆盖。
Rollback: 关闭展示开关，恢复旧页面。</code>`
      },
      {
        eyebrow: "Private Demand",
        title: "企业私有需求：原文不进公开代码仓",
        html: `<div class="grid three">
          <div class="panel rose"><h3>私有源头</h3><p>客户原始需求、审批讨论和敏感动机留在内部需求仓。</p></div>
          <div class="panel amber"><h3>计划输入</h3><p>进入 plan 前生成公开安全的摘要或本地 override。</p></div>
          <div class="panel green"><h3>代码仓边界</h3><p>代码仓只保留 public-safe 的 spec、plan、tasks 和 evidence。</p></div>
        </div>
        <div class="note">金融场景里，保护需求原文和客户信息，是 AI Coding 流程的一部分。</div>`
      },
      {
        eyebrow: "Video Demo",
        title: "课堂视频：完整走一遍 AI Team SDD",
        html: `<div class="script">
          <div class="script-row"><b>片段 1</b><span>从一句自然语言开始：“我想让系统支持查看大文件上传失败原因。”</span></div>
          <div class="script-row"><b>片段 2</b><span>AI 先判断类型，生成或关联问题单，不直接改代码。</span></div>
          <div class="script-row"><b>片段 3</b><span>产品角色生成 spec，架构角色生成 plan，开发角色生成 tasks，强调上下文隔离。</span></div>
          <div class="script-row"><b>片段 4</b><span>展示 Work Context、Code Graph、Human Gate、Evidence Board 如何在流程中出现。</span></div>
          <div class="script-row"><b>片段 5</b><span>最后展示证据板和 PR 摘要，说明团队如何审核而不是只相信 AI。</span></div>
        </div>`
      },
      {
        eyebrow: "Graduation Practice",
        title: "毕业练习：用一句话启动合规流程",
        html: `<code class="example">我想让系统支持查看大文件上传失败原因。
请按 AI Team SDD 流程处理：
1. 先判断这是新特性、bugfix，还是需要补充信息；
2. 如果没有问题单，先帮我起草问题单；
3. 不要直接改代码；
4. 先说明需要哪些确认、影响分析和证据。</code>
        <div class="grid three">
          <div class="panel blue"><h3>你能做到</h3><p>提出一个可进入研发流程的问题。</p></div>
          <div class="panel teal"><h3>AI 能做到</h3><p>整理、分析、计划、小步执行。</p></div>
          <div class="panel green"><h3>团队能做到</h3><p>审核边界、验证质量、沉淀经验。</p></div>
        </div>`
      }
    ]
  }
];

function panels(items, columns = 3) {
  const colors = ["blue", "teal", "green", "amber", "rose", "violet"];
  return `<div class="grid ${columns === 2 ? "two" : columns === 4 ? "four" : "three"}">
    ${items.map((item, index) => `<div class="panel ${item.color ?? colors[index % colors.length]}"><h3>${item.title}</h3><p>${item.body}</p></div>`).join("")}
  </div>`;
}

function steps(items, columns = 5) {
  const colors = ["", "teal", "green", "amber", "rose", "violet"];
  return `<div class="flow${columns === 6 ? " six" : ""}">
    ${items.map((item, index) => `<div class="step"><span class="num ${colors[index % colors.length]}">${index + 1}</span><b>${item.title}</b><small>${item.body}</small></div>`).join("")}
  </div>`;
}

function comparison(rows, headers = ["做法", "会发生什么", "判断标准"]) {
  return `<table class="matrix"><thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}

const enhancedDecks = [
  {
    file: "ai-coding-finance-course-01-ai-assistant-basics.html",
    code: "Course 01",
    title: "第 1 期：从日常问答到可靠的 AI 协作",
    subtitle: "先学会把问题说清楚、给出可靠来源，并留下下一次还能继续使用的工作记录。",
    coverCards: [
      ["本期起点", "会用豆包或类似工具回答日常问题。"],
      ["本期能力", "把模糊想法整理成别人可以继续处理的材料。"],
      ["为后面埋线", "可靠知识从哪里来，聊天结束后什么应该留下。"]
    ],
    agenda: [
      ["认识", "通用一句话助手、AI Coding 和 AI Team Coding 有什么不同。"],
      ["方法", "背景、目标、边界、输出和自检五要素。"],
      ["可靠性", "区分来源、推断和待确认信息。"],
      ["练习", "把上传失败的一句话变成可交接的问题材料。"]
    ],
    prep: ["打开豆包、WorkBuddy 或常用聊天工具；准备一个已经脱敏的工作问题。", "先认识三类使用方式，再练习可靠表达和可接续记录；本期不写代码。"],
    slides: [
      {
        eyebrow: "Why AI",
        title: "AI 的价值，不只是更快得到一段答案",
        lead: "真正有用的变化，是把整理、比较、起草和检查交给 AI，人把精力留给判断。但当 AI 从回答问题走到修改项目，影响范围和责任也会改变。",
        html: panels([
          { title: "整理", body: "把零散描述整理成清单、表格、问题单或操作步骤。" },
          { title: "比较", body: "根据明确标准比较多个方案，并标出差异和未知项。" },
          { title: "起草", body: "快速形成初稿，再由人补充事实、边界和责任。" },
          { title: "检查", body: "检查遗漏、矛盾、风险和仍需确认的信息。" }
        ], 4)
      },
      {
        eyebrow: "Assistant Mindset",
        title: "无论使用哪种工具，都先把 AI 当成刚加入的协作同事",
        lead: "它很能干，但不知道你的现场情况，也不会自动知道哪些资料可信。先学会正确协作，再决定让它接触多少项目能力。",
        html: comparison([
          ["只说：帮我看看上传失败", "AI 只能猜系统、用户和原因", "答案可能流畅，但无法交给研发继续处理"],
          ["补充场景、目标和已知事实", "AI 可以整理现象和缺失信息", "输出开始具备协作价值"],
          ["指定资料来源并要求标注推断", "AI 能区分事实、推断和待确认项", "别人知道哪些内容可以相信"]
        ])
      },
      {
        eyebrow: "Three Ways To Use AI",
        title: "一句话助手、AI Coding、AI Team Coding 不是同一种用法",
        lead: "协作方法相同，但工具能看到的上下文、能执行的动作和承担的风险不同。这里比较常见使用方式，而不是给豆包、WorkBuddy 等产品贴固定标签。",
        html: comparison([
          ["上下文", "当前对话与手工上传材料", "IDE、仓库文件、搜索结果和命令输出", "任务上下文、项目知识、Code Graph 和历史决定"],
          ["主要动作", "问答、整理、总结和起草", "读代码、改文件、运行命令和查看差异", "按角色和阶段完成需求、计划、开发、审核与归档"],
          ["规则", "主要依靠用户在对话中说明", "读取仓库入口规则和工具配置", "团队规范自动进入每次任务，并设置停下条件"],
          ["记忆", "通常围绕个人对话和手工保存结果", "可保留本地任务状态，但不天然等于团队记忆", "共享决定、失败经验和三级记忆由团队治理"],
          ["权限", "决定可上传什么、可访问哪些企业能力", "控制可读目录、可写文件、命令执行和网络访问", "再叠加模块责任、人工 Gate 和合入权限"]
        ], ["比较项", "通用一句话助手", "AI Coding 工具", "AI Team Coding"])
      },
      {
        eyebrow: "Team Layer",
        title: "AI Team Coding 是在编程工具外，再加一层团队协作系统",
        lead: "AI Coding 能读取和修改真实项目，所以仅靠个人提示词不够。团队层用代码仓、规则、流程和服务把它的能力放进共同边界。",
        html: panels([
          { title: "IDE / 仓库上下文", body: "让 AI 看到当前项目、相关源码、测试、配置和真实差异，不只依赖你复制的一段文字。" },
          { title: "团队规范", body: "明确模块边界、公共接口、验证要求和遇到什么情况必须停下来找人。" },
          { title: "项目知识", body: "通过源码、Code Graph、README、术语和历史决定帮助 AI 理解项目，而不是重新猜设计。" },
          { title: "团队记忆", body: "保存已做决定、失败尝试、bug 根因和成熟经验，让后续任务少走重复弯路。" },
          { title: "权限与 Gate", body: "限制可读、可写、可执行范围；架构、模块和合入决定仍由相应责任人确认。" },
          { title: "证据与追踪", body: "把 issue、计划、代码差异、测试、风险和审核连接起来，发生问题时可以定位和回滚。" }
        ], 3)
      },
      {
        eyebrow: "Prompt Pattern",
        title: "进入任何 AI 工具前，先把任务说成五件事",
        lead: "团队层约束工具可以做什么；清楚的任务约束这一轮要做什么。两者共同决定 AI 是否会沿着正确方向工作。",
        html: `${steps([
          { title: "背景", body: "事情发生在哪里，谁受到影响。" },
          { title: "目标", body: "希望最终获得什么结果。" },
          { title: "边界", body: "不能泄露、不能假设、不能越过什么。" },
          { title: "输出", body: "需要清单、草稿、表格还是步骤。" },
          { title: "自检", body: "标出推断、遗漏和需要人确认的地方。" }
        ])}
        <code class="example">请把“大文件上传失败”整理成问题单草稿。\n背景：管理员反馈 500MB 以上附件偶发失败。\n目标：让研发能判断是否需要修复。\n边界：不要猜系统原因，不使用真实客户信息。\n输出：现象、影响、已知事实、待确认问题、建议下一步。\n自检：标出所有推断和缺失信息。</code>`
      },
      {
        eyebrow: "Reliable Knowledge",
        title: "AI 的回答要能说清楚：依据来自哪里",
        lead: "五要素解决“要做什么”，可靠来源解决“凭什么这样判断”。后面课程会把这些来源进一步整理成项目知识层。",
        html: panels([
          { title: "你提供的材料", body: "业务说明、操作记录、截图文字和经过脱敏的日志，是本轮最直接的依据。" },
          { title: "团队已有资料", body: "制度、术语表、项目说明和历史问题，可以减少重复解释。" },
          { title: "AI 的推断", body: "可以作为调查方向，但必须显式标记，不能冒充事实。" }
        ]) + `<div class="note">可靠输出的最低要求：事实有来源，推断有标签，未知项有人确认。</div>`
      },
      {
        eyebrow: "Knowledge Practice",
        title: "同一个问题，先给资料再提问",
        lead: "知道来源类型之后，再看输入资料如何改变 AI 的输出：材料越贴近现场，推断越少，协作价值越高。",
        html: comparison([
          ["没有资料", "列出十几个常见上传失败原因", "信息很多，但未必与当前系统有关"],
          ["提供操作记录和错误时间", "先整理可确认事实，再列调查方向", "研发可以按线索继续检查"],
          ["再补团队术语和约束", "输出使用统一名称并避开敏感信息", "材料更容易在团队中复用"]
        ], ["输入条件", "AI 的输出变化", "协作价值"]) + `<code class="example">只使用我提供的操作记录回答。资料里没有的信息写“未知”，不要用常见原因补全。</code>`
      },
      {
        eyebrow: "Memory Seed",
        title: "聊天会结束，工作记录应该留下",
        lead: "有依据的结论仍会随着对话结束而消失，所以还要留下可接续记录。这就是后面“记忆层”的起点。",
        html: panels([
          { title: "留下目标", body: "我们正在解决什么问题，完成标准是什么。" },
          { title: "留下事实", body: "已经确认了什么，使用了哪些资料。" },
          { title: "留下决定", body: "为什么选择当前方向，哪些方案被排除。" },
          { title: "留下下一步", body: "谁需要确认什么，下一次从哪里继续。" }
        ], 4) + `<code class="example">工作记录：目标 / 已确认事实 / 未确认问题 / 已做决定 / 下一步 / 资料来源</code>`
      },
      {
        eyebrow: "Safety",
        title: "上下文和记忆越多，越要先管好权限与信息",
        lead: "工作记录应该可接续，但不等于把所有对话、客户资料和项目文件都保存或上传。能力扩大时，边界也要同步加强。",
        html: panels([
          { title: "先脱敏", body: "客户姓名、账号、交易明细、密钥和内部地址不能直接输入。" },
          { title: "少上传", body: "只提供完成任务必需的片段，不把整个文件夹一次性交给工具。" },
          { title: "不照抄", body: "重要结论回到原始资料或责任人处核对。" },
          { title: "留边界", body: "不确定时让 AI 停下来提问，不让它自行补全事实。" }
        ], 4)
      },
      {
        eyebrow: "Video Walkthrough",
        title: "操作演示：把一句话整理成可交接材料",
        lead: "现在把前面的五要素、可靠资料、工作记录和安全边界串成一次完整操作。",
        html: `${steps([
          { title: "第一次输入", body: "只说“上传失败，帮我看看”。" },
          { title: "观察缺口", body: "找出 AI 猜测的系统、原因和目标。" },
          { title: "补五要素", body: "加入背景、目标、边界、输出、自检。" },
          { title: "加入资料", body: "粘贴脱敏后的操作记录。" },
          { title: "留下记录", body: "生成可供下一次继续的工作摘要。" }
        ])}
        <div class="mini-row"><div class="mini-card"><b>豆包入口</b><span><a href="https://www.doubao.com/">doubao.com</a></span></div><div class="mini-card"><b>观看重点</b><span>不要只看按钮，重点观察输入如何改变输出质量。</span></div></div>`
      },
      {
        eyebrow: "Hands On",
        title: "课堂练习：完成一份问题材料和工作记录",
        lead: "看完完整操作后，换成自己的脱敏问题，走一遍相同链路，并检查另一位同事能否继续。",
        html: panels([
          { title: "选择问题", body: "使用一个真实但已脱敏的问题，例如报表难懂、附件上传失败或审批缓慢。" },
          { title: "生成问题材料", body: "使用五要素提示词，要求 AI 区分事实、推断和待确认项。" },
          { title: "生成工作记录", body: "让 AI 再输出目标、事实、决定、下一步和资料来源。" }
        ]) + `<div class="note">完成标准：另一位同事只看这两份材料，也知道发生了什么、还缺什么、下一步做什么。</div>`
      },
      {
        eyebrow: "Bridge",
        title: "下一期：当 AI 可以读取项目，规则会更重要",
        lead: "第一期已经把问题、依据、记录和安全边界准备好。第二期让 AI 进入真实项目时，这些基础会升级成任务上下文、项目知识、分支和验证证据。",
        html: panels([
          { title: "今天已经有", body: "清楚的问题、可靠来源、可接续的工作记录。" },
          { title: "下一期增加", body: "项目目录、源代码、修改计划、分支和自测证据。" },
          { title: "继续保留", body: "不知道就提问，重要边界由人确认，做完必须给证据。" }
        ])
      }
    ]
  },
  {
    file: "ai-coding-finance-course-02-ai-coding-first-task.html",
    code: "Course 02",
    title: "第 2 期：让 AI 完成第一次可检查的小改动",
    subtitle: "认识研发协作词汇，学会让 AI 先读项目、留下任务上下文，再小步修改并提供证据。",
    coverCards: [
      ["本期起点", "已经能把一个问题整理成可靠的协作材料。"],
      ["本期能力", "在 AI Coding 工具里完成一次受控的小改动。"],
      ["为后面埋线", "项目知识地图、任务上下文和人工确认点。"]
    ],
    agenda: [
      ["认识工具", "Codex、Claude Code、Cursor Agent、Trae 能做什么。"],
      ["理解项目", "先读源码、说明和项目结构，再提出计划。"],
      ["小步修改", "基于分支执行最小改动，遇到边界停下来。"],
      ["证明结果", "用测试、差异和未验证项说明完成情况。"]
    ],
    prep: ["准备一个可练习的小项目；安装团队支持的任一 AI Coding 工具。", "练习任务只选文字、校验或小逻辑，不碰公共接口和数据库。"],
    slides: [
      {
        eyebrow: "AI Coding",
        title: "聊天工具回答问题，AI Coding 工具还能读取和修改项目",
        html: comparison([
          ["豆包等聊天工具", "根据你提供的文字和文件生成回答", "适合整理、理解和起草"],
          ["AI Coding 工具", "读取目录、搜索代码、运行命令、修改文件", "适合在真实项目中完成研发任务"],
          ["团队研发平台", "记录 issue、分支、PR、审核和测试", "让改动可追踪、可审核、可回滚"]
        ], ["工具", "主要能力", "在流程中的位置"])
      },
      {
        eyebrow: "Common Words",
        title: "先把常见研发词翻译成人话",
        html: panels([
          { title: "Repository 仓库", body: "项目所有文件及其修改历史所在的地方。" },
          { title: "Issue 问题单", body: "记录为什么要改、现象是什么、希望得到什么。" },
          { title: "Branch 分支", body: "为本次修改建立的独立工作副本。" },
          { title: "PR 合并申请", body: "把改动、证据和风险交给负责人审核。" },
          { title: "Test 测试", body: "用可重复方式证明功能符合预期。" },
          { title: "Owner 负责人", body: "对模块边界、质量和是否接受改动负责的人。" }
        ], 3)
      },
      {
        eyebrow: "Safe Loop",
        title: "第一次改代码，只走这条最小闭环",
        html: steps([
          { title: "理解", body: "复述目标，读取相关项目资料。" },
          { title: "计划", body: "说明要改哪里、为什么、风险是什么。" },
          { title: "确认", body: "人确认范围和基础分支。" },
          { title: "修改", body: "只做实现目标所需的最小变化。" },
          { title: "验证", body: "运行测试并汇报差异、结果和缺口。" }
        ])
      },
      {
        eyebrow: "Project Knowledge",
        title: "AI 理解项目时，需要一张可靠的知识地图",
        lead: "第一期讲“回答要有来源”；进入代码仓后，来源变成源码、结构投影和项目说明。",
        html: panels([
          { title: "源码是第一事实", body: "真实类、函数、配置和测试决定系统当前如何运行。" },
          { title: "Code Graph 是结构投影", body: "帮助快速看到类、接口、调用和模块依赖，定位影响范围。" },
          { title: "文档解释意图", body: "README、架构说明和历史决定解释为什么这样设计。" },
          { title: "Issue 提供任务背景", body: "说明本轮为什么改、期望结果和已知限制。" }
        ], 4)
      },
      {
        eyebrow: "Task Context",
        title: "每次任务先建立一份可接续的上下文",
        lead: "这份记录连接第一期的工作摘要与后面的团队 Work Context Package。",
        html: comparison([
          ["任务", "issue 地址、目标、完成标准", "避免改着改着忘记为什么做"],
          ["项目", "基础分支、相关模块、关键资料", "避免读错仓库或改错目录"],
          ["边界", "允许修改、禁止修改、需要谁确认", "避免小需求演变成架构改造"],
          ["状态", "已完成、待确认、下一步、证据", "中断后可以继续"]
        ], ["记录部分", "至少包含", "解决的问题"])
      },
      {
        eyebrow: "Read First",
        title: "第一条操作口令：只理解项目，暂时不要改",
        html: `<code class="example">请先不要修改任何文件。\n1. 复述“大文件上传失败”问题和完成标准；\n2. 读取仓库入口规则、相关模块 README、源码和测试；\n3. 如有 Code Graph，给出相关类和调用链；\n4. 列出已有能力、可复用实现、未知项和可能影响的模块；\n5. 生成本轮任务上下文摘要，等我确认后再继续。</code>
        <div class="note">合格结果不是“我已理解”，而是能指出依据文件、相关模块、可复用实现和未知项。</div>`
      },
      {
        eyebrow: "Plan",
        title: "第二条操作口令：给出最小计划和停下条件",
        html: `<code class="example">基于已确认的任务上下文，提出最小修改计划。\n请写明：修改文件、复用点、测试、风险、回滚方式。\n如果涉及公共接口、跨模块、配置含义或数据库，请停止实现并要求负责人确认。</code>
        ${panels([
          { title: "计划要具体", body: "能看出修改位置、顺序和验证方法。" },
          { title: "范围要小", body: "不包含顺手重构、无关清理和另起一套实现。" },
          { title: "停下条件要明确", body: "遇到公共边界时把决定交回给人。" }
        ])}
        <div class="note">后续课程会介绍已经提供的 Compact 模式：低风险小改动可以用一句话启动 Plan 与 Tasks 的联合审核，但仍要分清“技术决定”和“执行步骤”，并由人确认是否适用。</div>`
      },
      {
        eyebrow: "Human Gate",
        title: "真正修改前，人至少确认三件事",
        html: panels([
          { title: "从哪个分支开始", body: "确认基础版本，避免在过期代码上开发。" },
          { title: "范围是否正确", body: "确认 AI 找对模块，没有扩大任务。" },
          { title: "是否触碰架构边界", body: "公共接口、跨模块和数据归属变化必须升级审核。" }
        ]) + `<div class="note">AI 可以给建议，但“允许改什么”和“是否接受架构变化”是人的决定。</div>`
      },
      {
        eyebrow: "Implement",
        title: "第三条操作口令：只做计划内的最小改动",
        html: `<code class="example">计划已确认。请创建本次任务分支，只修改计划中列出的文件。\n优先复用已有上传状态和错误处理；不要新增公共参数或改其他模块数据库。\n完成后逐个检查改动文件，并说明任何偏离计划的地方。</code>
        ${comparison([
          ["新增一套上传状态", "重复已有能力，后续维护两套逻辑", "先搜索和复用"],
          ["顺手重构多个模块", "范围扩大，审核和回滚困难", "拆成独立任务"],
          ["只修改定位到的处理逻辑", "差异可读、风险可控", "符合最小变更"]
        ])}`
      },
      {
        eyebrow: "Evidence",
        title: "完成不是一句话，而是一组可检查证据",
        html: panels([
          { title: "改了什么", body: "列出文件和行为变化，并说明为什么需要。" },
          { title: "怎么验证", body: "给出真实运行过的命令、测试结果和关键输出。" },
          { title: "还没验证什么", body: "明确环境缺口、跳过项和剩余风险。" },
          { title: "怎么撤回", body: "说明关闭功能、回滚提交或恢复配置的方法。" }
        ], 4) + `<code class="example">证据摘要：修改文件 / 测试命令 / 通过结果 / 未执行项 / 风险 / 回滚方式</code>`
      },
      {
        eyebrow: "Hands On",
        title: "课堂练习：完成一次只读分析和最小计划",
        html: steps([
          { title: "选择任务", body: "挑一个文字、校验或小逻辑问题。" },
          { title: "建立上下文", body: "记录目标、仓库、分支、边界和状态。" },
          { title: "只读分析", body: "让 AI 指出源码、测试和复用点。" },
          { title: "审核计划", body: "检查范围和停下条件。" },
          { title: "保存结果", body: "把上下文和计划留给下一次继续。" }
        ]) + `<div class="note">下一期会解释：为什么多人使用不同 AI 工具时，仅靠每个人自觉还不够。</div>`
      }
    ]
  },
  {
    file: "ai-coding-finance-course-03-team-risk-and-quality.html",
    code: "Course 03",
    title: "第 3 期：让不同 AI 工具在同一套团队规则下工作",
    subtitle: "理解重复造轮子、架构越界和验证不足从哪里来，以及知识、记忆、证据和人工审核如何共同控制风险。",
    coverCards: [
      ["本期起点", "已经能完成一次受控的小改动。"],
      ["本期能力", "识别团队级风险，并要求 AI 给出影响分析和证据。"],
      ["为后面埋线", "共享知识、失败经验和可晋升的团队记忆。"]
    ],
    agenda: [
      ["看见风险", "代码很容易生成，但架构和验证可能持续变差。"],
      ["统一入口", "不同工具都读取同一套项目规则和任务上下文。"],
      ["积累能力", "把项目知识和失败经验变成团队可复用资产。"],
      ["人类负责", "范围、边界、证据和合入由责任人判断。"]
    ],
    prep: ["准备第二期的任务上下文和修改计划。", "本期使用同一上传案例观察三类常见失败。"],
    slides: [
      {
        eyebrow: "The New Risk",
        title: "功能实现成本下降，团队风险反而更容易被放大",
        html: panels([
          { title: "改得太快", body: "没有充分理解项目，就直接生成大量差异。" },
          { title: "看得不全", body: "只读局部文件，错过已有能力和真实边界。" },
          { title: "做法不一", body: "不同工具按各自理解实现同一需求。" },
          { title: "证据不足", body: "能运行一次就宣布完成，失败路径无人验证。" }
        ], 4)
      },
      {
        eyebrow: "Failure 01",
        title: "重复造轮子：没有先找到项目已有能力",
        html: comparison([
          ["直接新增上传状态服务", "形成两套状态语义和两套维护入口", "先查源码、Code Graph、历史 PR 和模块说明"],
          ["复用现有状态能力", "改动集中，调用方保持一致", "说明复用了哪个类、接口或配置"],
          ["现有能力确实不够", "提出接口需求并由负责人评审", "不要绕开边界修改别的模块内部"]
        ])
      },
      {
        eyebrow: "Failure 02",
        title: "架构越界：为了局部功能移动了公共边界",
        html: panels([
          { title: "公共接口", body: "新增模糊参数、改变含义或破坏兼容性，会影响所有调用方。" },
          { title: "跨模块", body: "直接改其他模块内部或访问其数据库，会打破责任边界。" },
          { title: "配置", body: "新增配置默认行为与上一版不同，会让升级用户意外改变行为。" },
          { title: "停下信号", body: "出现以上变化时，AI 必须给出影响范围并等待人类决策。" }
        ], 4)
      },
      {
        eyebrow: "Failure 03",
        title: "验证不足：只证明正常路径，不证明真实场景",
        html: comparison([
          ["小文件上传成功", "只证明最简单路径", "仍缺大文件、超时和外部存储异常"],
          ["单元测试通过", "证明局部逻辑", "仍缺模块契约和真实环境差异"],
          ["完整证据包", "正常、失败、边界和未覆盖项都清楚", "审核人可以判断剩余风险"]
        ], ["验证", "能证明什么", "还需要追问什么"])
      },
      {
        eyebrow: "Unified Entry",
        title: "工具可以不同，但进入项目后看到的规则必须一致",
        lead: "Codex、Claude Code、Cursor Agent、Trae 的界面不同，项目规则、任务上下文和停下条件应由仓库统一提供。",
        html: `${panels([
          { title: "统一规则", body: "模块边界、公共接口、测试和提交要求进入工具可读取的入口。" },
          { title: "统一任务", body: "同一个 issue、上下文包和计划，不因换工具而重新解释。" },
          { title: "统一证据", body: "不管谁生成代码，都用相同测试与审核标准判断。" }
        ])}
        <div class="note">目标不是让所有人使用同一种 AI，而是让不同 AI 在同一个真实项目约束下协作。</div>`
      },
      {
        eyebrow: "Knowledge Layer",
        title: "共享知识让 AI 少猜、少重复、少另起炉灶",
        html: panels([
          { title: "源代码", body: "当前系统行为的第一事实。" },
          { title: "Code Graph", body: "类、接口、调用和模块依赖的快速投影。" },
          { title: "项目说明", body: "目录用途、模块职责、运行方法和架构原则。" },
          { title: "历史决定", body: "解释为什么选择当前设计，避免反复讨论已定事项。" },
          { title: "问题与变更", body: "issue 和 PR 记录需求、讨论、证据和责任。" },
          { title: "术语与规范", body: "统一团队对同一个业务词和技术边界的理解。" }
        ], 3)
      },
      {
        eyebrow: "Memory Layer",
        title: "一次失败只有被整理和复用，才会变成团队经验",
        lead: "不是把聊天记录全部上传，而是从失败中提炼以后能直接帮助判断的内容。",
        html: steps([
          { title: "发生", body: "测试失败、评审退回、线上事故或重复返工。" },
          { title: "复盘", body: "区分事实、根因、误判和环境因素。" },
          { title: "提炼", body: "形成判断条件、检查项、样例或反例。" },
          { title: "审核", body: "去除敏感信息，确认适用范围。" },
          { title: "复用", body: "进入后续任务的规则、知识、测试或记忆检索。" }
        ])
      },
      {
        eyebrow: "Memory Preview",
        title: "个人记录、团队经验和正式指导不是同一种东西",
        html: comparison([
          ["个人工作记录", "本轮尝试、临时线索、未验证想法", "先留在本地，不自动上传"],
          ["部门共享经验", "已脱敏、可供同类任务检索的经验", "可以上传，但不是正式制度"],
          ["企业长期指导", "反复验证、经过审核的稳定结论", "进入正式文档并随版本长期保留"]
        ], ["层次", "适合保存什么", "基本边界"]) + `<div class="note">第四期会正式讲清三层记忆如何晋升，以及谁决定何时归档。</div>`
      },
      {
        eyebrow: "Evidence Board",
        title: "证据板让审核人看到事实，而不是相信一句“已经完成”",
        html: panels([
          { title: "任务目标", body: "本轮承诺解决什么，不解决什么。" },
          { title: "影响范围", body: "改了哪些模块、接口、配置和数据。" },
          { title: "测试结果", body: "命令、环境、通过与失败数量、关键输出。" },
          { title: "代码差异", body: "新增、删除、复用和偏离计划的内容。" },
          { title: "剩余风险", body: "未验证场景、环境缺口和回滚方式。" },
          { title: "人工确认", body: "谁确认了范围、架构、测试和合入。" }
        ], 3)
      },
      {
        eyebrow: "Human Accountability",
        title: "AI 可以执行，责任仍然由人承担",
        html: comparison([
          ["需求提出者", "确认现象、目标和业务优先级", "AI 不替业务决定做不做"],
          ["模块负责人", "确认模块边界、实现质量和兼容性", "AI 不替负责人批准越界"],
          ["贡献者", "检查每个改动文件和真实测试结果", "AI 生成不等于可以直接提交"],
          ["审核者", "根据差异和证据判断是否合入", "不能只看 AI 摘要"]
        ], ["角色", "人的决定", "不能交给 AI 的责任"])
      },
      {
        eyebrow: "Risk Prompt",
        title: "动手前，先让 AI 完成一次团队风险评估",
        html: `<code class="example">先不要修改代码。请基于源码、Code Graph、项目文档和历史问题评估：\n1. 已有能力和复用候选；\n2. 可能影响的模块、接口、配置和数据；\n3. 是否需要负责人或架构审核；\n4. 需要哪些正常、失败和边界测试；\n5. 本轮结束后哪些经验只留本地，哪些值得脱敏后共享。</code>
        <div class="note">合格输出必须同时说明依据、未知项、人类决策点和验证缺口。</div>`
      },
      {
        eyebrow: "Bridge",
        title: "下一期：把这些护栏串成一条可重复的 SDD 流程",
        html: panels([
          { title: "已经学会", body: "可靠表达、项目理解、最小修改、风险识别和证据。" },
          { title: "还需要", body: "让多人、多角色、多次中断仍按同一顺序协作。" },
          { title: "最终答案", body: "用 Spec Driven Development 把需求、计划、任务、实现、证据和记忆连起来。" }
        ])
      }
    ]
  },
  {
    file: "ai-coding-finance-course-04-ai-team-sdd-workflow.html",
    code: "Course 04",
    title: "第 4 期：用 AI Team SDD 完成一次团队级研发任务",
    subtitle: "把需求、架构、开发、验证和经验沉淀连成可中断、可审核、可复用的完整闭环。",
    coverCards: [
      ["本期起点", "已经理解个人 AI Coding 和团队风险控制。"],
      ["本期能力", "从一句自然语言启动并接续完整 SDD 流程。"],
      ["最终闭环", "Skill 执行流程，Knowledge 提供依据，Memory 积累经验。"]
    ],
    agenda: [
      ["进入流程", "判断 bug、新特性或从零项目，并建立工作项。"],
      ["角色交接", "产品、架构和开发上下文隔离，通过文档或 issue 交接。"],
      ["受控实施", "Work Context、Code Graph、Gate 和 Evidence 贯穿任务。"],
      ["沉淀经验", "三级记忆按价值和敏感程度保存、晋升和归档。"]
    ],
    prep: ["准备一个脱敏需求或 bug 现象；选择一个练习仓库。", "可以直接在 AI Coding 聊天框说一句话启动，不要求记命令。"],
    slides: [
      {
        eyebrow: "SDD",
        title: "Spec Driven Development：先形成共同理解，再生成代码",
        html: steps([
          { title: "原始需求", body: "一句自然语言、业务现象或客户目标。" },
          { title: "Specify", body: "明确用户场景、目标、边界和验收标准。" },
          { title: "Plan", body: "基于项目结构决定实现方案和影响范围。" },
          { title: "Tasks", body: "把计划拆成有顺序、可验证的小任务。" },
          { title: "Implement", body: "最小修改、运行验证、形成证据。" }
        ]) + `<div class="note">文档不是额外负担，而是不同角色、不同 AI 会话之间的交接接口。</div>`
      },
      {
        eyebrow: "Natural Language Entry",
        title: "用户只需要从一句真实问题开始",
        html: `<code class="example">我们的大文件上传经常超时，请帮我按团队流程处理。\n\n或者：\n我希望管理员可以查看每次上传失败的原因，请帮我启动新特性流程。</code>
        ${panels([
          { title: "AI 先分类", body: "判断是 bug、公开新特性、私有需求还是从零项目。" },
          { title: "信息不足先追问", body: "不凭一句话直接修改代码。" },
          { title: "生成工作入口", body: "起草 issue、spec 或任务上下文，交给人确认。" }
        ])}`
      },
      {
        eyebrow: "Bug Flow",
        title: "Bugfix：从现象和 coding issue 开始",
        html: steps([
          { title: "报告现象", body: "业务人员描述发生了什么，不要求判断根因。" },
          { title: "创建 issue", body: "记录复现、影响、期望和缺失信息。" },
          { title: "评估影响", body: "定位相关模块和架构风险，由人确认范围。" },
          { title: "修复验证", body: "最小修复并补回归、失败路径证据。" },
          { title: "沉淀经验", body: "保留根因、误判线索和预防检查项。" }
        ])
      },
      {
        eyebrow: "Feature Flow",
        title: "公开新特性：从 coding issue 进入完整 SDD",
        html: steps([
          { title: "提出目标", body: "说明用户场景、价值和非目标。" },
          { title: "确认是否做", body: "技术委员会或相应决策组织确认方向。" },
          { title: "Specify", body: "形成场景、边界和验收标准。" },
          { title: "Plan 与 Tasks", body: "架构师规划，开发拆分任务。" },
          { title: "实现与证据", body: "代码 PR 关联原始 issue。" }
        ])
      },
      {
        eyebrow: "Planning Modes",
        title: "小改动可以少一道流程，但不能少掉思考",
        lead: "团队已经提供 Compact 扩展模式。使用者只需在聊天中明确说出 Compact，AI 就会启动对应流程；它不是让 AI 直接编码，而是把 Plan 和 Tasks 放进一次操作和一次联合审核中。",
        html: comparison([
          ["标准流程", "Plan 单独审核，再生成 Tasks 并审核", "新特性、跨模块、公共接口、数据库、安全权限、发布风险"],
          ["Compact 模式（已支持）", "一句话启动；架构和开发仍隔离上下文；最后联合审核", "需求清楚、单模块、路径唯一、失败成本低、容易回滚"]
        ], ["选择", "怎么运行", "适用情况"]) +
        `<code class="example">例子：给已有 UserValidator 补充空邮箱校验。

Plan：复用现有校验入口，不改变公共接口。
Tasks：补失败测试 → 修改校验 → 运行用户模块自测。

如果分析发现要改公共 API 或数据库，就停止 Compact，回到标准流程。</code>
        <div class="grid three">
          <div class="panel blue"><h3>不是按文件数判断</h3><p>一个文件也可能是高风险 SPI；多个本地测试文件也可能仍是低风险。</p></div>
          <div class="panel amber"><h3>AI 只能建议</h3><p>先看影响分析，再由负责人确认是否允许使用 Compact。</p></div>
          <div class="panel green"><h3>发现范围扩大就退出</h3><p>保留已有证据，回到独立 Plan 和 Tasks，不在快捷清单上继续打补丁。</p></div>
        </div>`
      },
      {
        eyebrow: "New Project",
        title: "从零项目：先把地基建好，再开始堆功能",
        lead: "它与新特性共享 SDD 主流程，但要额外明确产品边界、架构骨架和第一条可运行链路。",
        html: panels([
          { title: "产品基线", body: "服务谁、解决什么、不解决什么、第一版成功标准。" },
          { title: "架构基线", body: "模块职责、公共接口、数据归属、依赖最小集。" },
          { title: "工程基线", body: "目录、构建、测试、日志、配置和发布方式。" },
          { title: "运行主干", body: "先完成一条端到端可运行的小链路，再扩展能力。" }
        ], 4)
      },
      {
        eyebrow: "Role Isolation",
        title: "三个 AI 角色隔离上下文，用文档或 issue 交接",
        html: comparison([
          ["产品/客户经理角色", "specify：用户场景、目标、边界、验收", "不带入实现偏好"],
          ["架构师角色", "plan：模块、接口、复用、风险和验证策略", "基于 spec 和项目知识判断"],
          ["开发角色", "tasks + implement：拆任务、编码、自测和证据", "不擅自改写需求和架构决定"]
        ], ["角色", "交付物", "上下文边界"]) + `<div class="note">上下文隔离让责任更清楚，也减少同一个 AI 为自己早先的假设辩护。</div>`
      },
      {
        eyebrow: "Work Context",
        title: "Work Context Package 让任务可以中断和继续",
        html: comparison([
          ["context-pack.md", "面向下一位协作者的任务摘要", "目标、来源、模块、边界、证据要求"],
          ["work-context.yml", "机器可读的当前状态", "工作标识、状态、URL、下一步和停下条件"],
          ["evidence/", "本轮验证材料索引", "命令、结果、环境、失败和未验证项"],
          ["state.json", "工作流引擎的执行进度", "用于从暂停的步骤继续运行"]
        ], ["文件", "作用", "下次打开时先看什么"]) + `<div class="note">这些文件是否进入 Git 按项目策略决定；本地敏感内容和临时运行状态默认不上传。</div>`
      },
      {
        eyebrow: "Code Graph",
        title: "Code Graph 在计划前帮助 AI 看清影响范围",
        html: `<code class="example">上传页面 → UploadController → UploadService → StorageAdapter\n                         ↘ UploadEvent → AuditService\n\n计划问题：新增“失败原因”会影响返回对象、事件结构、审计记录和哪些测试？</code>
        ${panels([
          { title: "先定位", body: "找出相关类、接口、调用链和数据流。" },
          { title: "再复用", body: "识别已有能力和扩展点，避免重复实现。" },
          { title: "控制半径", body: "优先单模块修改；跨模块时明确接口需求和负责人。" }
        ])}`
      },
      {
        eyebrow: "Three Support Layers",
        title: "Skill、Knowledge、Memory 分别解决三类问题",
        html: comparison([
          ["Skill", "这一步怎么做", "启动任务、影响分析、审核、验证、提交和复盘流程"],
          ["Knowledge", "当前项目是什么", "源码、Code Graph、术语、架构、接口和历史决定"],
          ["Memory", "过去发生过什么", "已做决定、失败尝试、bug 根因和可复用经验"]
        ], ["外围支撑", "回答的问题", "典型内容"]) + `<div class="note">三层共同作用：Skill 决定动作，Knowledge 提供事实，Memory 提醒历史经验和已知风险。</div>`
      },
      {
        eyebrow: "Three Memory Tiers",
        title: "三级记忆按敏感度、成熟度和长期价值管理",
        html: comparison([
          ["本地记忆", "个人尝试、临时线索、未验证判断", "不上传；可随任务清理"],
          ["部门记忆", "脱敏后的案例、排障经验、可检索模式", "上传内部空间；不进入正式 docs 和版本记录"],
          ["企业记忆", "稳定架构原则、成熟实践、长期兼容与运维经验", "审核后进入 docs；随正式版本长期保留"]
        ], ["记忆层", "保存内容", "Git 与发布边界"])
      },
      {
        eyebrow: "Memory Consolidation",
        title: "经验归档不必等发布，由贡献者和维护者按价值触发",
        html: steps([
          { title: "选择来源", body: "完成的 feature、bugfix、事故、迁移或评审意见。" },
          { title: "提炼经验", body: "保留问题、判断条件、做法、证据和适用范围。" },
          { title: "隐私处理", body: "删除客户、账号、内部地址和不可公开实现细节。" },
          { title: "选择层级", body: "本地、部门或企业；不默认全部晋升。" },
          { title: "审核与复用", body: "进入检索、规则、测试或正式文档。" }
        ]) + `<div class="note">发布归档是批量整理的一种场景，不是每次发布前必须完成的硬 Gate。</div>`
      },
      {
        eyebrow: "Human Gates",
        title: "关键节点由人做决定，Evidence Board 提供依据",
        html: comparison([
          ["Spec Gate", "目标、边界和验收是否正确", "需求提出者或相应负责人"],
          ["Plan Gate", "架构、复用、影响半径和验证策略是否合理", "架构师、模块负责人"],
          ["Task Gate", "任务是否可执行、顺序正确、没有遗漏验证", "维护者、贡献者"],
          ["PR Gate", "差异与证据是否足以合入", "代码审核者、测试和运维责任人"]
        ], ["人工确认点", "主要判断", "典型责任人"])
      },
      {
        eyebrow: "Private Requirement Extension",
        title: "扩展场景：私有客户需求只把可公开的交接信息带入代码仓",
        html: steps([
          { title: "内部留痕", body: "原始企业需求记录在严格权限的内部需求仓。" },
          { title: "审核脱敏", body: "形成可供研发使用的安全摘要和验收边界。" },
          { title: "URL 交接", body: "代码仓通过需求 URL 关联来源，不复制原始私密内容。" },
          { title: "Plan 融合", body: "计划阶段获取内容，生成本地忽略的 spec.override.md。" },
          { title: "公开实现", body: "代码、测试和 PR 只保留实现所需的公开安全信息。" }
        ])
      },
      {
        eyebrow: "Final Practice",
        title: "毕业练习：用一句话启动，并在任意 Gate 继续",
        html: `<code class="example">我们的大文件上传经常超时，请按团队 bugfix 流程处理。\n如果信息不足，先帮我起草 issue 并列出待确认项；不要猜根因。\n\n继续任务时：\n请恢复“bug-upload-timeout-123”的 Work Context，先告诉我当前阶段、已有决定、失败尝试、证据缺口和下一步，等我确认后继续。</code>
        ${panels([
          { title: "你负责目标", body: "确认真实问题、业务边界和是否继续。" },
          { title: "AI 负责执行", body: "读取知识、遵循 Skill、记录上下文、生成改动和证据。" },
          { title: "团队负责质量", body: "审核架构、验证结果、合入代码并沉淀经验。" }
        ])}`
      }
    ]
  }
];

function miniRow(cards, columns = 2) {
  return `<div class="mini-row${columns === 3 ? " three" : ""}">
    ${cards.map((card) => `<div class="mini-card"><b>${card.title}</b><span>${card.body}</span></div>`).join("")}
  </div>`;
}

function lessonEnrichmentFor(deck, slide) {
  const title = `${slide.eyebrow ?? ""} ${slide.title}`;
  const course = deck.code;

  if (course === "Course 01") {
    if (title.includes("从日常问答")) {
      return miniRow([
        { title: "示例对比", body: "原句：“帮我看看上传失败”。改写：“请整理问题单草稿：现象、影响、已知信息、待确认问题、建议下一步”。" },
        { title: "你要观察", body: "改写后的提示词给出了输出格式，也要求保留待确认问题，所以 AI 更不容易凭空猜原因。" }
      ]);
    }
    if (title.includes("课堂视频")) {
      return miniRow([
        { title: "观看重点", body: "每次 AI 输出后看三件事：它知道什么、它不知道什么、它有没有把未知内容说成事实。" },
        { title: "你要带走", body: "保留三样东西：原始一句话、四段式提示词、最终问题单草稿。" }
      ]);
    }
    if (title.includes("课堂练习")) {
      return miniRow([
        { title: "三步操作", body: "1. 写一句模糊问题；2. 改成四段式；3. 要求 AI 标出假设和待确认项。" },
        { title: "合格样子", body: "产物里必须能看到：谁受影响、希望得到什么、还缺什么信息、下一步找谁确认。" }
      ]);
    }
    if (title.includes("课后任务")) {
      return miniRow([
        { title: "提交方式", body: "每人提交一页：原始问题、提示词、AI 输出、自己删改了哪些内容。" },
        { title: "下期衔接", body: "第二期会把这份问题单交给 AI Coding 工具，让它先读项目、先出计划。" }
      ]);
    }
  }

  if (course === "Course 02") {
    if (title.includes("AI Coding 不是")) {
      return miniRow([
        { title: "你会看到", body: "AI 先解释项目结构，再列可能修改点。这个阶段暂时不允许它编辑文件。" },
        { title: "你要观察", body: "AI 是否先读文件、是否承认不确定、是否主动说“这里需要你确认”。" }
      ]);
    }
    if (title.includes("最小安全链路")) {
      return miniRow([
        { title: "AI 应该输出", body: "读项目时说“我找到这些入口”；出计划时说“我只建议改这些”；自检时说“我跑了这些检查”。" },
        { title: "先不要继续的信号", body: "没有问题单、没有计划、没有边界说明、没有证据计划时，不允许进入改代码。" }
      ]);
    }
    if (title.includes("课堂视频")) {
      return miniRow([
        { title: "观看重点", body: "当 AI 想直接改代码时，要先看它是否已经完成项目理解和边界确认。" },
        { title: "对比内容", body: "对比“直接改”的错误路线和“先读、先计划”的安全路线。" }
      ]);
    }
    if (title.includes("只读演练")) {
      return miniRow([
        { title: "报告结构", body: "目标复述、已读文件、相关模块、待确认问题、建议下一步、暂不修改理由。" },
        { title: "评分标准", body: "不是看它懂了多少代码，而是看它有没有把未知点和风险讲清楚。" }
      ]);
    }
  }

  if (course === "Course 03") {
    if (title.includes("太容易写出来")) {
      return miniRow([
        { title: "开场案例", body: "同一个“上传失败原因展示”，三个人分别让不同 AI 写，最后出现三套入口、两套状态、没有统一证据。" },
        { title: "本期问题", body: "当实现成本降低后，团队更需要统一入口、边界、复用和证据，而不是更少流程。" }
      ]);
    }
    if (title.includes("重复造轮子")) {
      return miniRow([
        { title: "观察点", body: "AI 有没有先搜索已有上传状态、错误码、日志能力？有没有解释为什么不能复用？" },
        { title: "判断题", body: "如果已有能力只差一个字段，优先考虑扩展已有能力；是否新增一套实现，需要负责人确认。" }
      ]);
    }
    if (title.includes("改错边界")) {
      return miniRow([
        { title: "观察点", body: "AI 是否为了一个页面展示改了公共接口、配置含义或数据库字段。" },
        { title: "停下信号", body: "只要出现公共接口、跨模块调用、数据结构变化，就需要负责人或架构确认。" }
      ]);
    }
    if (title.includes("happy path")) {
      return miniRow([
        { title: "观察点", body: "AI 是否只验证了“上传成功/正常失败”，却没有验证超时、权限、空文件、外部存储异常。" },
        { title: "补救动作", body: "要求 AI 把未覆盖场景写进证据板，不能用“应该没问题”代替检查。" }
      ]);
    }
    if (title.includes("AI 不是责任边界")) {
      return miniRow([
        { title: "角色错位", body: "需求人让 AI 决定业务优先级，开发让 AI 决定架构边界，评审人只看 AI 总结，都会出问题。" },
        { title: "正确分工", body: "AI 可以整理和建议，人负责确认目标、边界、证据和是否合入。" }
      ]);
    }
    if (title.includes("课堂视频")) {
      return miniRow([
        { title: "对比重点", body: "错误路线看起来更快；正确路线更容易审核、回滚和复用。" },
        { title: "观看任务", body: "看视频时标出三处缺口：缺复用检查、缺人工 Gate、缺证据。" }
      ]);
    }
    if (title.includes("风险评估")) {
      return miniRow([
        { title: "合格输出", body: "至少包含复用候选、影响模块、人工确认点、自检证据、剩余风险五项。" },
        { title: "不合格输出", body: "只说“我会修改上传逻辑并测试通过”，没有影响范围和未覆盖说明。" }
      ]);
    }
  }

  return "";
}

function classroomFor(deck, slide) {
  if (slide.classroom === false) return "";

  const title = `${slide.eyebrow ?? ""} ${slide.title}`;
  let goal = "理解本页概念，并把它套到“大文件上传失败”这个贯穿样例。";
  let action = "用自己的业务问题替换样例，再让 AI 按同样结构输出。";
  let output = "得到一个可复制的提示词、清单或判断标准。";

  if (title.includes("课前观看")) {
    goal = "知道本节课推荐先看哪些资料，以及观看时重点观察什么。";
    action = "打开其中一个链接，先看前 5-8 分钟，记录一个自己能复用的操作。";
    output = "带着一个具体问题进入课堂，例如：我怎样让 AI 少猜、先问问题、输出表格。";
  } else if (title.includes("课堂视频")) {
    goal = "通过一段短演示，看清错误做法和正确做法的差别。";
    action = "按片段记录：AI 做对了什么、缺了什么、下一步是否可以继续。";
    output = "得到一份自己的观察记录，而不是只记住视频里的操作。";
  } else if (title.includes("练习") || title.includes("毕业")) {
    goal = "把前面学到的方法用在自己的脱敏问题上。";
    action = "复制模板，替换成自己的场景，完成一版 AI 输出后再人工修改。";
    output = "完成一份可交给别人继续处理的草稿或检查清单。";
  } else if (title.includes("操作口令") || title.includes("Prompt")) {
    goal = "学会一条可以直接复制的 AI 指令，并知道每句话的作用。";
    action = "把口令中的业务场景换成自己的脱敏问题，保留“先不要改代码”等限制句。";
    output = "得到一条能直接放进豆包或 AI Coding 工具的提示词。";
  } else if (title.includes("风险") || title.includes("错误") || title.includes("不能让 AI")) {
    goal = "识别 AI 看似完成、实际越界或缺少证据的信号。";
    action = "在案例中标出：哪里开始猜测、哪里改过边界、哪里没有验证。";
    output = "形成一张“看到这些信号就要停下”的风险清单。";
  } else if (title.includes("Git") || title.includes("Issue") || title.includes("PR") || title.includes("研发词")) {
    goal = "先把研发术语理解成日常协作动作。";
    action = "用自己的话复述：问题单、审核、自检分别对应什么。";
    output = "建立一份后续课程会反复使用的术语小抄。";
  } else if (title.includes("护栏") || title.includes("Work Context") || title.includes("Code Graph") || title.includes("Evidence") || title.includes("Gate")) {
    goal = "理解团队为什么要用工作记录、影响地图、人工确认和证据板。";
    action = "判断当前步骤需要哪一种护栏：记录、影响分析、人工确认还是证据。";
    output = "产出一份四护栏检查表。";
  } else if (deck.code === "Course 01") {
    goal = "把豆包从“日常问答工具”升级成“协作材料助手”。";
    action = "把一句模糊问题改成四段式提示词。";
    output = "得到一份问题单草稿。";
  } else if (deck.code === "Course 02") {
    goal = "理解 AI Coding 的第一步是读项目和出计划，不是马上写代码。";
    action = "观察 AI 是否承认不知道、是否先问问题、是否列边界。";
    output = "得到一次“只读不改”的项目理解报告。";
  } else if (deck.code === "Course 03") {
    goal = "通过失败案例看见团队护栏的必要性。";
    action = "指出错误路线中缺了哪个团队护栏。";
    output = "得到一份风险识别清单。";
  } else if (deck.code === "Course 04") {
    goal = "把前三期的个人能力接入团队 SDD 流程。";
    action = "判断当前任务属于新特性、bugfix 还是需要补充信息。";
    output = "得到一份可进入团队流程的问题单或 spec 草稿。";
  }

  return `<div class="classroom">
    <div><b>本页要会</b><span>${goal}</span></div>
    <div><b>你要操作</b><span>${action}</span></div>
    <div><b>完成标准</b><span>${output}</span></div>
  </div>`;
}

function caseLabFor(deck, slide) {
  if (slide.caseLab === false) return "";
  const title = `${slide.eyebrow ?? ""} ${slide.title}`;
  if (title.includes("课前观看") || title.includes("课堂视频") || title.includes("练习") || title.includes("毕业")) {
    return "";
  }

  let example = "管理员反馈“大文件上传失败”，不要直接问“怎么办”，先整理成背景、目标、限制和输出。";
  let check = "如果 AI 输出里没有待确认问题、没有边界、没有证据要求，就说明还不能进入下一步。";

  if (deck.code === "Course 01") {
    example = "把“帮我看看上传失败”改成“请整理问题单草稿：现象、影响、已知信息、待确认问题”。";
    check = "好输出应该能交给别人继续处理，而不是只给你一段泛泛建议。";
  }
  if (deck.code === "Course 02") {
    example = "让 AI 先说明要看哪些文件，再说修改计划；演示时故意阻止它马上编辑。";
    check = "合格表现是：先复述目标、列待确认问题、说明可能影响文件。";
  }
  if (deck.code === "Course 03") {
    example = "同一个上传需求，错误路线是新增一套逻辑；正确路线是先找已有上传状态能力。";
    check = "判断标准：有没有复用检查、边界判断、失败路径和回滚说明。";
  }
  if (deck.code === "Course 04") {
    example = "从一句话进入 issue，再进入 spec、plan、tasks，最后形成 evidence 和 PR 摘要。";
    check = "合格流程是：每一步都有文档交接，关键边界有人确认。";
  }

  if (title.includes("操作口令") || title.includes("Prompt")) {
    example = "把口令粘给 AI 后，合格回应应该先复述目标、承认缺失信息、列出要看的文件或要问的问题。";
    check = "如果 AI 马上开始改文件、没有列边界、没有说需要你确认什么，就先停下并要求它重答。";
  } else if (title.includes("研发词") || title.includes("Git") || title.includes("Issue") || title.includes("PR")) {
    example = "可以把 issue 讲成“问题单”，把 PR 讲成“把改动拿给负责人审核”。";
    check = "你能用自己的话复述这些术语，就可以继续进入工具操作。";
  } else if (title.includes("护栏") || title.includes("Work Context") || title.includes("Code Graph") || title.includes("Evidence") || title.includes("Gate")) {
    example = "上传失败样例里：Work Context 记任务状态，Code Graph 看上传链路，Gate 决定能否改接口，Evidence 证明结果。";
    check = "四个护栏都能对应到一次真实操作，才算不是空概念。";
  } else if (title.includes("风险") || title.includes("不能让 AI")) {
    example = "让 AI 快速写出代码后，反问它：你复用了什么？影响了谁？怎么证明？";
    check = "如果回答不上来，就是团队流程必须介入的时刻。";
  }

  return `<div class="case-lab">
    <div><b>本页案例</b><span>${example}</span></div>
    <div><b>判断标准</b><span>${check}</span></div>
  </div>`;
}

function slideHtml(deck, slide, index, total) {
  return `
    <section class="slide${index === 0 ? " active" : ""}">
      <div class="slide-inner">
        <div>
          <div class="eyebrow">${slide.eyebrow ?? deck.code}</div>
          <h2>${slide.title}</h2>
          ${slide.lead ? `<p class="lead">${slide.lead}</p>` : ""}
        </div>
        ${slide.html}
        ${slide.legacyEnrichment ? lessonEnrichmentFor(deck, slide) : ""}
        ${slide.caseLab ? caseLabFor(deck, slide) : ""}
        ${slide.classroom ? classroomFor(deck, slide) : ""}
      </div>
      <div class="bottom"><span>${deck.code}</span><span>${index + 1} / ${total}</span></div>
    </section>`;
}

function coverAgendaFor(deck) {
  if (deck.agenda) {
    return `<table class="matrix">
      <thead><tr><th>学习路径</th><th>这一段解决什么问题</th></tr></thead>
      <tbody>${deck.agenda.map(([step, body]) => `<tr><td>${step}</td><td>${body}</td></tr>`).join("")}</tbody>
    </table>`;
  }
  const agendas = {
    "Course 01": [
      ["1. 认知", "AI 不是搜索框，而是需要上下文的协作同事。"],
      ["2. 演示", "把一句模糊问题改成四段式提示词。"],
      ["3. 练习", "用豆包生成一份可交接的问题单草稿。"],
      ["4. 产物", "原始问题、改写提示词、AI 输出、人工修订点。"]
    ],
    "Course 02": [
      ["1. 认知", "AI Coding 的第一步是读项目和出计划。"],
      ["2. 演示", "让 AI 先解释项目、列疑问、列边界，不直接改代码。"],
      ["3. 练习", "完成一次“只读不改”的项目理解报告。"],
      ["4. 产物", "目标复述、相关文件、待确认问题、最小计划。"]
    ],
    "Course 03": [
      ["1. 认知", "AI 很容易写出代码，所以团队更需要边界和证据。"],
      ["2. 演示", "对比重复造轮子、改错边界、只测正常路径三个失败案例。"],
      ["3. 练习", "让 AI 先做风险评估，而不是马上实现。"],
      ["4. 产物", "复用候选、影响范围、人工确认点、自检证据。"]
    ],
    "Course 04": [
      ["1. 认知", "把个人 AI 能力接入团队 SDD 流程。"],
      ["2. 演示", "从一句话进入 issue、spec、plan、tasks、evidence。"],
      ["3. 练习", "用一句自然语言启动合规流程。"],
      ["4. 产物", "可审核的问题单、spec 草稿、计划和证据摘要。"]
    ]
  };
  const rows = agendas[deck.code] ?? agendas["Course 04"];
  return `<table class="matrix">
    <thead><tr><th>课堂路线</th><th>这一段讲什么</th></tr></thead>
    <tbody>${rows.map(([step, body]) => `<tr><td>${step}</td><td>${body}</td></tr>`).join("")}</tbody>
  </table>`;
}

function coverPrepFor(deck) {
  if (deck.prep) {
    return miniRow([
      { title: "课前准备", body: deck.prep[0] },
      { title: "本期操作", body: deck.prep[1] }
    ]);
  }
  const prep = {
    "Course 01": ["打开豆包或同类聊天工具；准备 2 个脱敏日常问题。", "你会看到“模糊问法 vs 四段式问法”的对比。"],
    "Course 02": ["准备一个小型示例项目；AI Coding 工具需要能读取项目文件。", "你会看到“先不要改代码”的只读项目理解演示。"],
    "Course 03": ["准备一个上传失败样例；对照三种错误路线。", "你会看到“直接实现 vs 带护栏实现”的风险对比。"],
    "Course 04": ["准备 issue/spec/plan/tasks/evidence 的样例文件。", "你会看到从一句话进入 SDD 流程的完整演示。"]
  };
  const [before, video] = prep[deck.code] ?? prep["Course 04"];
  return miniRow([
    { title: "课前准备", body: before },
    { title: "课堂会看", body: video }
  ]);
}

function deckHtml(deck) {
  const total = deck.slides.length + 1;
  const cover = `
    <section class="slide active cover">
      <div class="slide-inner" style="align-content:start; gap:16px">
        <div class="eyebrow">金融中队 AI Coding 入门系列</div>
        <h1 style="font-size:46px">${deck.title}</h1>
        <p class="subtitle">${deck.subtitle}</p>
        <div class="grid three">
          ${(deck.coverCards ?? []).map(([title, body], index) => `<div class="panel ${["blue", "teal", "green"][index]}"><h3>${title}</h3><p>${body}</p></div>`).join("")}
        </div>
        ${coverAgendaFor(deck)}
        ${coverPrepFor(deck)}
      </div>
      <div class="bottom"><span>${deck.code}</span><span>1 / ${total}</span></div>
    </section>`;
  const slides = deck.slides.map((slide, i) => slideHtml(deck, slide, i + 1, total)).join("\n");
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${deck.title}</title>
  <style>${sharedStyle}</style>
</head>
<body>
  <main class="deck">
${cover}
${slides}
  </main>
  <div class="controls" aria-label="Slide controls">
    <button class="nav-button" id="prev" type="button" aria-label="上一页">‹</button>
    <div class="counter" id="counter">1 / ${total}</div>
    <button class="nav-button" id="next" type="button" aria-label="下一页">›</button>
  </div>
  <script>
    const slides = Array.from(document.querySelectorAll(".slide"));
    const prev = document.getElementById("prev");
    const next = document.getElementById("next");
    const counter = document.getElementById("counter");
    let current = 0;
    const hash = window.location.hash.match(/^#slide-(\\d+)$/);
    if (hash) current = Math.min(Math.max(Number(hash[1]) - 1, 0), slides.length - 1);
    function show(index, updateHash = true) {
      current = Math.min(Math.max(index, 0), slides.length - 1);
      slides.forEach((slide, i) => slide.classList.toggle("active", i === current));
      prev.disabled = current === 0;
      next.disabled = current === slides.length - 1;
      counter.textContent = \`\${current + 1} / \${slides.length}\`;
      if (updateHash) history.replaceState(null, "", \`#slide-\${current + 1}\`);
    }
    prev.addEventListener("click", () => show(current - 1));
    next.addEventListener("click", () => show(current + 1));
    window.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") show(current - 1);
      if (event.key === "ArrowRight" || event.key === " ") show(current + 1);
      if (event.key === "Home") show(0);
      if (event.key === "End") show(slides.length - 1);
    });
    show(current, false);
  </script>
</body>
</html>
`;
}

fs.mkdirSync(outDir, { recursive: true });

for (const deck of enhancedDecks) {
  const filePath = path.join(outDir, deck.file);
  const html = deckHtml(deck).replace(/[ \t]+$/gm, "");
  fs.writeFileSync(filePath, html, "utf8");
  console.log(`wrote ${filePath}`);
}
