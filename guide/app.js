/* 时序特征工程 · 学习指引 —— 页面逻辑
   数据来自 build_guide.py 注入的 <script id="guide-data">。 */

(function () {
  "use strict";

  var DATA = (function () {
    var node = document.getElementById("guide-data");
    if (!node) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (err) {
      return null;
    }
  })();

  if (!DATA) {
    document.getElementById("view").innerHTML =
      '<div class="panel"><h1 class="panel-title">页面数据没有读到</h1>' +
      '<p class="muted">请在项目根目录重新运行：<code>python guide\\build_guide.py</code></p></div>';
    return;
  }

  var OFFLINE = DATA.offline || null;
  var OFFLINE_FILES = OFFLINE && OFFLINE.files ? OFFLINE.files : {};

  var DOC_BY_ID = {};
  DATA.docs.forEach(function (item) { DOC_BY_ID[item.id] = item; });

  var SCRIPT_BY_ID = {};
  DATA.scripts.forEach(function (item) { SCRIPT_BY_ID[item.id] = item; });

  var COPY_SOURCES = new WeakMap();
  var PROGRESS_KEY = "tsfe-progress-v1";
  var currentRunText = "";
  var lastView = null;

  /* ------------------------------------------------------------ 小工具 */

  function $(id) { return document.getElementById(id); }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function icon(name, cls) {
    return '<i data-lucide="' + name + '"' + (cls ? ' class="' + cls + '"' : "") + "></i>";
  }

  function refreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }

  function toast(message) {
    var node = $("toast");
    node.textContent = message;
    node.classList.add("show");
    window.clearTimeout(toast._timer);
    toast._timer = window.setTimeout(function () { node.classList.remove("show"); }, 1800);
  }

  function copyFallback(text, done) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.top = "-1000px";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
    document.body.removeChild(area);
    if (ok) { done(); } else { toast("复制失败，请手动选中后按 Ctrl+C"); }
  }

  function copyText(text, message) {
    var done = function () { toast(message || "已复制"); };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { copyFallback(text, done); });
    } else {
      copyFallback(text, done);
    }
  }

  function openDialog(title, html) {
    $("dialogTitle").textContent = title;
    $("dialogBody").innerHTML = html;
    $("dialogBackdrop").classList.remove("hidden");
    refreshIcons();
  }

  function closeDialog() {
    $("dialogBackdrop").classList.add("hidden");
    $("dialogBody").innerHTML = "";
  }

  function loadProgress() {
    try { return JSON.parse(window.localStorage.getItem(PROGRESS_KEY)) || {}; }
    catch (err) { return {}; }
  }

  function saveProgress(value) {
    try { window.localStorage.setItem(PROGRESS_KEY, JSON.stringify(value)); } catch (err) { /* 忽略 */ }
  }

  function runBlock(command) {
    if (OFFLINE) return command;
    var slash = "\\";
    return 'cd "' + DATA.projectRoot + '"\n.' + slash + '.venv' + slash + 'Scripts' + slash + 'Activate.ps1\n' + command;
  }

  function codeBlock(code, lang) {
    return '<div class="code-block"><div class="code-head">' +
      '<span class="code-lang">' + esc(lang || "text") + "</span>" +
      '<button class="code-copy" type="button">' + icon("copy") + "<span>复制</span></button>" +
      "</div><pre><code>" + esc(code) + "</code></pre></div>";
  }

  /* ------------------------------------------------------------ 装饰渲染结果 */

  function detectLang(codeEl) {
    var cls = codeEl.className || "";
    var match = cls.match(/language-([a-z0-9+#-]+)/i);
    if (match) return match[1];
    if (codeEl.closest(".cmd-line")) return "powershell";
    return "code";
  }

  function decorate(scope) {
    scope.querySelectorAll("pre > code").forEach(function (codeEl) {
      var pre = codeEl.parentElement;
      if (pre.closest(".code-block")) return;

      var wrap = document.createElement("div");
      wrap.className = "code-block";

      var head = document.createElement("div");
      head.className = "code-head";
      head.innerHTML = '<span class="code-lang">' + esc(detectLang(codeEl)) + "</span>";

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "code-copy";
      btn.innerHTML = icon("copy") + "<span>复制</span>";
      head.appendChild(btn);

      pre.parentNode.insertBefore(wrap, pre);
      wrap.appendChild(head);
      wrap.appendChild(pre);
      COPY_SOURCES.set(btn, codeEl.textContent);
    });

    scope.querySelectorAll("table").forEach(function (table) {
      table.classList.add("data-table");
      if (table.parentElement && table.parentElement.classList.contains("table-wrap")) return;
      var box = document.createElement("div");
      box.className = "table-wrap";
      table.parentNode.insertBefore(box, table);
      box.appendChild(table);
    });
  }

  /* ------------------------------------------------------------ 侧边导航 */

  function navItem(route, iconName, label) {
    return '<a class="nav-item" data-nav="' + esc(route) + '" href="#' + esc(route) + '">' +
      icon(iconName) + '<span class="nav-label">' + esc(label) + "</span></a>";
  }

  function buildNav() {
    var groups = [];
    var order = [];
    DATA.docs.forEach(function (doc) {
      if (order.indexOf(doc.group) === -1) order.push(doc.group);
    });

    groups.push(
      '<div class="nav-group"><div class="nav-group-title">总览</div>' +
      navItem("home", "layout-dashboard", "首页") +
      "</div>"
    );

    order.forEach(function (groupName) {
      var items = DATA.docs.filter(function (doc) { return doc.group === groupName; });
      groups.push(
        '<div class="nav-group"><div class="nav-group-title">' + esc(groupName) + "</div>" +
        items.map(function (doc) { return navItem("doc-" + doc.id, doc.icon, doc.title); }).join("") +
        "</div>"
      );
    });

    groups.push(
      '<div class="nav-group"><div class="nav-group-title">项目内容</div>' +
      navItem("files", "folder-open", "项目文件") +
      navItem("figures", "image", "实验图表") +
      navItem("tables", "table-2", "数据表格") +
      navItem("roadmap", "route", "学习路线") +
      navItem("requirements", "list-checks", "导师要求对照") +
      "</div>"
    );

    groups.push(
      '<div class="nav-group"><div class="nav-group-title">脚本源码</div>' +
      DATA.scripts.map(function (script) {
        return navItem("script-" + script.id, "code-xml", script.title);
      }).join("") +
      "</div>"
    );

    $("nav").innerHTML = groups.join("");
  }

  function markActiveNav(route) {
    document.querySelectorAll("[data-nav]").forEach(function (node) {
      node.classList.toggle("is-active", node.getAttribute("data-nav") === route);
    });
  }

  /* ------------------------------------------------------------ 搜索 */

  function setupSearch() {
    var input = $("searchInput");
    var box = input.closest(".search-box");
    var panel = null;
    var items = [];
    var active = -1;

    function close() {
      if (panel) { panel.remove(); panel = null; }
      items = [];
      active = -1;
    }

    function score(entry, query) {
      var title = entry.title.toLowerCase();
      var text = (entry.text || "").toLowerCase();
      if (title.indexOf(query) === 0) return 0;
      if (title.indexOf(query) >= 0) return 1;
      if (text.indexOf(query) >= 0) return 2;
      return -1;
    }

    function open(query) {
      var q = query.trim().toLowerCase();
      if (q.length < 1) { close(); return; }

      var matches = DATA.search
        .map(function (entry) { return { entry: entry, rank: score(entry, q) }; })
        .filter(function (row) { return row.rank >= 0; })
        .sort(function (a, b) { return a.rank - b.rank; })
        .slice(0, 12)
        .map(function (row) { return row.entry; });

      items = matches;
      active = matches.length ? 0 : -1;

      if (!panel) {
        panel = document.createElement("div");
        panel.className = "search-results";
        box.appendChild(panel);
      }

      if (!matches.length) {
        panel.innerHTML = '<div class="sr-empty">没有找到，换个词试试（比如“滑动窗口”“MAE”“星期”）。</div>';
        return;
      }

      panel.innerHTML = matches.map(function (entry, index) {
        return '<button class="sr-item' + (index === active ? " is-active" : "") + '" type="button" data-route="' +
          esc(entry.route) + '"><span class="sr-title">' + esc(entry.title) + '</span>' +
          '<span class="sr-meta">' + esc(entry.type) + "</span></button>";
      }).join("");
    }

    function move(delta) {
      if (!items.length || !panel) return;
      active = (active + delta + items.length) % items.length;
      Array.prototype.forEach.call(panel.children, function (node, index) {
        node.classList.toggle("is-active", index === active);
      });
    }

    function go(index) {
      if (!items.length) return;
      var target = items[index < 0 ? 0 : index];
      input.value = "";
      close();
      window.location.hash = target.route.replace(/^#/, "");
      input.blur();
    }

    input.addEventListener("input", function () { open(input.value); });
    input.addEventListener("focus", function () { if (input.value.trim()) open(input.value); });
    input.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") { event.preventDefault(); move(1); }
      else if (event.key === "ArrowUp") { event.preventDefault(); move(-1); }
      else if (event.key === "Enter") { event.preventDefault(); go(active); }
      else if (event.key === "Escape") { input.value = ""; close(); input.blur(); }
    });

    document.addEventListener("click", function (event) {
      if (panel) {
        var button = event.target.closest(".sr-item");
        if (button) {
          event.preventDefault();
          var route = button.getAttribute("data-route").replace(/^#/, "");
          input.value = "";
          close();
          window.location.hash = route;
          return;
        }
      }
      if (!box.contains(event.target)) close();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "/") return;
      var tag = (document.activeElement && document.activeElement.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      event.preventDefault();
      input.focus();
    });
  }

  /* ------------------------------------------------------------ 页面：首页 */

  function viewHome() {
    var allCommand = ".\\run_all.ps1";
    currentRunText = runBlock(allCommand);

    var steps = [
      {
        no: "1",
        title: "运行一键脚本",
        text: "在项目文件夹里打开 PowerShell，先激活虚拟环境，再运行全部课程脚本。",
        action: "复制命令",
        copy: allCommand,
        message: "已复制，粘贴到 PowerShell 里运行"
      },
      {
        no: "2",
        title: "看结果文件",
        text: "脚本会生成图片和表格，点左边“实验图表”“数据表格”就能直接看。",
        action: "打开图表",
        route: "#figures"
      },
      {
        no: "3",
        title: "照着路线学",
        text: "7 天走完：先 Python 基础，再特征工程，最后建模对比与画图。",
        action: "打开学习路线",
        route: "#roadmap"
      }
    ];

    var stepsHtml = steps.map(function (step) {
      var action = step.route
        ? '<a class="link-btn" href="' + esc(step.route) + '">' + icon("arrow-right") + esc(step.action) + "</a>"
        : '<button class="link-btn" type="button" data-copy-text="' + esc(step.copy) + '" data-copy-message="' +
          esc(step.message) + '">' + icon("copy") + esc(step.action) + "</button>";
      return '<div class="step"><span class="step-no">' + step.no + "</span><strong>" + esc(step.title) +
        "</strong><p>" + esc(step.text) + "</p>" + action + "</div>";
    }).join("");

    var concepts = DATA.concepts.map(function (item) {
      return '<a class="concept-card" href="' + esc(item.route) + '">' +
        '<span class="concept-head">' + icon(item.icon) + "<strong>" + esc(item.title) + "</strong></span>" +
        "<p>" + esc(item.text) + "</p></a>";
    }).join("");

    var progress = loadProgress();
    var doneCount = DATA.roadmap.filter(function (day) { return progress[day.key]; }).length;

    var roadmapMini = DATA.roadmap.map(function (day) {
      return '<div class="roadmap-item' + (progress[day.key] ? " is-done" : "") + '">' +
        '<div class="roadmap-body"><span class="day">' + esc(day.day) + "</span><strong>" + esc(day.title) +
        "</strong><p>" + esc(day.desc) + "</p>" +
        '<a class="link-btn" href="' + esc(day.route) + '">' + icon("arrow-right") + "打开</a></div></div>";
    }).join("");

    var stat = [
      { value: DATA.docs.length, label: "篇中文教程" },
      { value: DATA.scripts.length, label: "个可运行脚本" },
      { value: Object.keys(DATA.tables).length, label: "张实验表格" },
      { value: DATA.figures.length, label: "张观察图片" }
    ].map(function (item) {
      return '<div class="stat"><b>' + item.value + "</b><span>" + esc(item.label) + "</span></div>";
    }).join("");

    var html =
      '<div class="page-head">' +
      "<h1>时序数据特征工程 · 学习指引</h1>" +
      '<p class="summary">教程、代码、实验结果都放在这一个网页里。左边点一下就能看，不用再翻文件夹找文件。</p>' +
      '<div class="meta-row">' +
      '<span class="chip">' + icon("folder") + esc(DATA.projectRoot) + "</span>" +
      '<span class="chip">' + icon("clock") + "生成于 " + esc(DATA.generatedAt) + "</span>" +
      '<span class="chip accent">' + icon("target") + "对照导师要求逐条完成</span>" +
      (OFFLINE ? '<span class="chip accent">' + icon("hard-drive") + "离线分享版</span>" : "") +
      "</div></div>" +

      '<section class="panel"><h2 class="panel-title">' + icon("rocket") + "三步开始</h2>" +
      '<div class="quick-steps">' + stepsHtml + "</div>" +
      '<div class="note">' + icon("info") +
      "<div>所有命令都要在项目文件夹里运行。第一次使用请先按《环境与工具》创建虚拟环境并安装依赖，" +
      '否则脚本会提示找不到 pandas。</div></div></section>' +

      '<h2 class="section-title">' + icon("layout-grid") + "六个核心概念</h2>" +
      '<div class="concept-grid">' + concepts + "</div>" +

      '<h2 class="section-title">' + icon("route") + "7 天学习路线</h2>" +
      '<div class="progress-line"><span>已完成 ' + doneCount + " / " + DATA.roadmap.length + "</span>" +
      '<div class="progress-track"><div class="progress-fill" style="width:' +
      Math.round((doneCount / DATA.roadmap.length) * 100) + '%"></div></div>' +
      '<a class="link-btn" href="#roadmap">' + icon("list-todo") + "去勾选</a></div>" +
      '<div class="roadmap-list">' + roadmapMini + "</div>" +

      '<h2 class="section-title">' + icon("bar-chart-3") + "项目里有什么</h2>" +
      '<div class="stat-row">' + stat + "</div>";

    paint("首页", html);
  }

  /* ------------------------------------------------------------ 页面：教程 */

  function viewDoc(doc) {
    currentRunText = runBlock(".\\run_all.ps1");
    var html =
      '<div class="page-head">' +
      "<h1>" + esc(doc.title) + "</h1>" +
      '<p class="summary">' + esc(doc.summary) + "</p>" +
      '<div class="meta-row">' +
      '<span class="chip accent">' + icon(doc.icon) + esc(doc.group) + "</span>" +
      '<span class="chip">' + icon("file-text") + esc(doc.file) + "</span>" +
      '<span class="chip">' + icon("book-open") + "中文教程" + "</span>" +
      "</div></div>" +
      '<article class="md">' + doc.html + "</article>";
    paint(doc.title, html);
  }

  /* ------------------------------------------------------------ 页面：脚本 */

  function viewScript(script) {
    var runnable = script.cmd.indexOf("python") === 0;
    currentRunText = runnable ? runBlock(script.cmd) : runBlock(".\\run_all.ps1");

    var html =
      '<div class="page-head">' +
      "<h1>" + esc(script.title) + "</h1>" +
      '<p class="summary">' + esc(script.summary) + "</p>" +
      '<div class="meta-row">' +
      '<span class="chip">' + icon("file-code-2") + esc(script.file) + "</span>" +
      '<span class="chip accent">' + icon("layers") + esc(script.group) + "</span>" +
      "</div></div>";

    if (runnable) {
      html +=
        '<section class="panel"><h2 class="panel-title">' + icon("terminal") + "怎么运行</h2>" +
        '<p class="muted">在项目根目录打开 PowerShell，依次执行下面三行（第一行可以直接复制整段命令）。</p>' +
        '<div class="cmd-line"><span class="cmd-text"><code>' +
        esc(runBlock(script.cmd)) + "</code></span>" +
        '<button class="link-btn" type="button" data-copy-text="' + esc(runBlock(script.cmd)) +
        '" data-copy-message="已复制，粘贴到 PowerShell 里运行">' + icon("copy") + "复制命令</button></div>" +
        "</section>";
    } else {
      html += '<div class="note">' + icon("info") +
        "<div>这个文件不用单独运行，它被其他脚本 import，用来提供公共函数。</div></div>";
    }

    html += '<h2 class="section-title">' + icon("code-xml") + "完整代码</h2>" +
      codeBlock(script.code, script.file.split(".").pop());

    paint(script.title, html);
  }

  /* ------------------------------------------------------------ 页面：图表 */

  function viewFigures() {
    currentRunText = runBlock(".\\run_all.ps1");

    var cards = DATA.figures.map(function (item, index) {
      var body = item.exists
        ? '<img src="' + esc(item.href) + '" alt="' + esc(item.title) + '" loading="lazy" data-zoom="' +
          esc(item.href) + '" data-zoom-title="' + esc(item.title) + '">'
        : '<div class="note danger">' + icon("circle-alert") + "<div>图片还没生成，请先运行 10_plots.py</div></div>";
      return '<figure class="figure-card"><div class="fig-head"><strong>' + esc(item.title) + "</strong>" +
        '<span class="chip">图 ' + (index + 1) + "</span></div>" + body +
        "<figcaption><p>" + esc(item.caption) + '</p><span class="fig-path">' + esc(item.file) +
        "</span></figcaption></figure>";
    }).join("");

    var html =
      '<div class="page-head">' +
      "<h1>实验图表</h1>" +
      '<p class="summary">六张图都来自同一份北京 PM2.5 数据。先看图建立直觉，再看数字。点图片可以放大。</p>' +
      '<div class="meta-row"><span class="chip accent">' + icon("image") + "可视化" + "</span>" +
      '<span class="chip">' + icon("folder") + "outputs/figures" + "</span></div></div>" +
      '<div class="note">' + icon("lightbulb") +
      "<div>看点：原始序列看趋势，滑动平均看“降噪后”的形状，差分看突变，" +
      "预测对比图看完整特征是不是真的更贴近真实值。</div></div>" +
      '<div class="figure-grid">' + cards + "</div>";

    paint("实验图表", html);
  }

  /* ------------------------------------------------------------ 页面：表格 */

  function viewTables(focusId) {
    currentRunText = runBlock(".\\run_all.ps1");

    var ids = Object.keys(DATA.tables);
    var cards = ids.map(function (id) {
      var table = DATA.tables[id];
      return '<section class="table-card" id="table-' + esc(id) + '">' +
        "<h2>" + esc(table.title) + "</h2>" +
        '<p class="muted">' + esc(table.description) + "</p>" +
        '<p class="file-path">' + esc(table.file) + "</p>" +
        table.html + "</section>";
    }).join('<hr style="margin:26px 0;border:0;border-top:1px dashed var(--border-strong)">');

    var html =
      '<div class="page-head">' +
      "<h1>数据表格</h1>" +
      '<p class="summary">这些 CSV 是脚本跑出来的实验记录。写报告时可以直接把表格里的数字抄进笔记。</p>' +
      '<div class="meta-row"><span class="chip accent">' + icon("table-2") + "实验数据" + "</span>" +
      '<span class="chip">' + icon("folder") + "outputs/tables" + "</span></div></div>" +
      cards +
      '<section class="table-card" id="table-cleaning"><h2>数据清洗报告</h2>' +
      '<p class="muted">记录缺失值、重复值、最终保留了多少行。</p>' +
      '<p class="file-path">outputs/tables/04_cleaning_report.txt</p>' +
      DATA.cleaningReport + "</section>";

    paint("数据表格", html, { focus: focusId ? "table-" + focusId : null });
  }

  /* ------------------------------------------------------------ 页面：学习路线 */

  function viewRoadmap() {
    currentRunText = runBlock(".\\run_all.ps1");
    var progress = loadProgress();
    var doneCount = DATA.roadmap.filter(function (day) { return progress[day.key]; }).length;

    var items = DATA.roadmap.map(function (day) {
      var done = !!progress[day.key];
      return '<div class="roadmap-item' + (done ? " is-done" : "") + '">' +
        '<input class="roadmap-check" type="checkbox" data-day="' + esc(day.key) + '"' +
        (done ? " checked" : "") + ' aria-label="标记' + esc(day.day) + '完成">' +
        '<div class="roadmap-body"><span class="day">' + esc(day.day) + "</span><strong>" + esc(day.title) +
        "</strong><p>" + esc(day.desc) + "</p>" +
        '<a class="link-btn" href="' + esc(day.route) + '">' + icon("arrow-right") + "打开对应内容</a>" +
        "</div></div>";
    }).join("");

    var html =
      '<div class="page-head">' +
      "<h1>7 天学习路线</h1>" +
      '<p class="summary">按顺序走，每天 1 到 2 小时。勾选框只保存在你自己的浏览器里，用于记录进度。</p>' +
      '<div class="meta-row"><span class="chip accent">' + icon("route") + "路线" + "</span>" +
      '<span class="chip">' + icon("clock") + "每天 1–2 小时" + "</span></div></div>" +
      '<div class="progress-line"><span>已完成 ' + doneCount + " / " + DATA.roadmap.length + "</span>" +
      '<div class="progress-track"><div class="progress-fill" style="width:' +
      Math.round((doneCount / DATA.roadmap.length) * 100) + '%"></div></div>' +
      '<button class="link-btn" type="button" id="resetProgress">' + icon("rotate-ccw") + "清空进度</button></div>" +
      '<div class="roadmap-list">' + items + "</div>";

    paint("学习路线", html);
  }

  /* ------------------------------------------------------------ 页面：导师要求 */

  function viewRequirements() {
    currentRunText = runBlock(".\\run_all.ps1");

    var rows = DATA.requirements.map(function (row) {
      return '<div class="req-item"><span class="req-no">' + esc(row.requirement.split(" ")[0]) + "</span>" +
        '<div class="req-body"><strong>' + esc(row.requirement) + "</strong><span>" + esc(row.task) + "</span></div>" +
        '<a class="link-btn" href="' + esc(row.route) + '">' + icon("arrow-right") + "去做" + "</a></div>";
    }).join("");

    var html =
      '<div class="page-head">' +
      "<h1>导师要求对照表</h1>" +
      '<p class="summary">左边是导师原文的编号和标题，右边是“具体要做什么”，点“去做”直接跳到对应教程或脚本。</p>' +
      '<div class="meta-row"><span class="chip accent">' + icon("list-checks") + "共 " + DATA.requirements.length +
      " 条" + "</span></div></div>" +
      '<div class="note ok">' + icon("circle-check") +
      "<div>交作业前把这张表过一遍：代码能跑、笔记有记录、报告有结论，就基本齐全了。</div></div>" +
      '<div class="req-list">' + rows + "</div>";

    paint("导师要求对照", html);
  }

  /* ------------------------------------------------------------ 统一的渲染入口 */
  /* ------------------------------------------------------------ 页面：项目文件 */

  var fileState = {
    source: OFFLINE ? "offline" : "none",
    rootName: OFFLINE ? (OFFLINE.rootName || "离线分享包") : "",
    rootPath: OFFLINE ? (OFFLINE.rootPath || "") : "",
    tree: [],
    files: {},
    urls: {},
    currentPath: null
  };

  var PICK_KINDS = {
    image: [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"],
    text: [".py", ".md", ".txt", ".json", ".csv", ".js", ".css", ".html", ".ps1", ".yml", ".yaml", ".toml", ".sql"]
  };
  var SKIP_NAMES = ["node_modules", ".git", ".venv", "venv", "__pycache__"];

  function safeDecode(value) {
    try { return decodeURIComponent(value); } catch (err) { return value; }
  }

  function formatSize(bytes) {
    if (typeof bytes !== "number") return "";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1024 / 1024).toFixed(1) + " MB";
  }

  function countFiles(nodes) {
    return (nodes || []).reduce(function (total, node) {
      return total + (node.type === "dir" ? countFiles(node.children) : 1);
    }, 0);
  }

  function findFileNode(nodes, path) {
    var list = nodes || [];
    for (var i = 0; i < list.length; i += 1) {
      var node = list[i];
      if (node.type === "file" && node.path === path) return node;
      if (node.type === "dir") {
        var found = findFileNode(node.children, path);
        if (found) return found;
      }
    }
    return null;
  }

  function nodeIcon(node) {
    if (node.type === "dir") return "folder";
    if (node.kind === "image") return "file-image";
    if (node.kind === "csv") return "table-2";
    if ([".py", ".ps1", ".js", ".css", ".html"].indexOf(node.ext) >= 0) return "file-code-2";
    return "file-text";
  }

  function treeHtml(nodes, depth) {
    return (nodes || []).map(function (node) {
      var indent = ' style="--depth:' + depth + '"';
      if (node.type === "dir") {
        return '<details class="tree-dir" open><summary class="tree-item"' + indent + ">" +
          icon("folder") + '<span class="tree-name">' + esc(node.name) + "</span>" +
          '<span class="tree-size">' + countFiles(node.children) + "</span></summary>" +
          '<div class="tree-children">' + treeHtml(node.children, depth + 1) + "</div></details>";
      }
      return '<button class="tree-item tree-file" type="button" data-open-file="' + esc(node.path) + '"' + indent + ">" +
        icon(nodeIcon(node)) + '<span class="tree-name">' + esc(node.name) + "</span>" +
        '<span class="tree-size">' + formatSize(node.size) + "</span></button>";
    }).join("");
  }

  function releaseUrls() {
    Object.keys(fileState.urls).forEach(function (key) { URL.revokeObjectURL(fileState.urls[key]); });
    fileState.urls = {};
  }

  function fileUrl(path) {
    if (fileState.source === "picker") {
      var file = fileState.files[path];
      if (!file) return "";
      if (!fileState.urls[path]) fileState.urls[path] = URL.createObjectURL(file);
      return fileState.urls[path];
    }
    if (fileState.source === "offline") {
      var offlineItem = OFFLINE_FILES[path];
      return offlineItem && offlineItem.href ? offlineItem.href : "";
    }
    return "../" + path.split("/").map(encodeURIComponent).join("/");
  }

  function serverHintHtml() {
    return '<div class="note">' + icon("circle-alert") +
      "<div><strong>现在读不到项目文件夹</strong><br>出于安全，浏览器不允许网页直接读电脑上的文件夹，需要一个本地服务。" +
      "在项目根目录运行 <code>powershell -ExecutionPolicy Bypass -File .\\guide\\start-server.ps1</code>，" +
      "再打开 <code>http://127.0.0.1:8765/guide/index.html</code> 就可以了。</div></div>" +
      '<p class="muted">也可以点上面的“选择其他文件夹”，手动挑一个文件夹来读（Chrome / Edge 支持）。</p>';
  }

  function viewFiles(options) {
    options = options || {};
    currentRunText = runBlock(".\\run_all.ps1");
    fileState.currentPath = options.file || null;

    var offlineMode = !!OFFLINE;
    var fileSummary = offlineMode
      ? "离线分享包里已经内置教程、脚本、图表、实验表格和速查 PDF。左边选文件，右边直接看；打包后新增的文件需要重新打包才会出现。"
      : "这里是项目文件夹的真实内容：左边选文件，右边直接看。改了代码或笔记，点“重新读取”就能看到最新的。";
    var sourceChip = offlineMode
      ? icon("hard-drive") + "离线文件清单"
      : icon("link") + "http://127.0.0.1:8765/guide/index.html";
    var statusText = offlineMode ? "正在读取离线文件清单…" : "正在连接本地服务…";

    var html =
      '<div class="page-head">' +
      "<h1>项目文件</h1>" +
      '<p class="summary">' + esc(fileSummary) + "</p>" +
      '<div class="meta-row">' +
      '<span class="chip accent">' + icon("folder-open") + (offlineMode ? "离线内置文件" : "读取文件夹") + "</span>" +
      '<span class="chip" id="fileRootChip">' + icon("hard-drive") + "正在读取…" + "</span>" +
      '<span class="chip">' + sourceChip + "</span>" +
      "</div></div>" +
      '<div class="files-toolbar">' +
      '<button class="link-btn" type="button" id="reloadTree">' + icon("refresh-cw") + (offlineMode ? "重新读取清单" : "重新读取") + "</button>" +
      '<button class="link-btn" type="button" id="pickFolder">' + icon("folder-open") + "选择其他文件夹" + "</button>" +
      '<span class="muted" id="filesStatus">' + statusText + "</span>" +
      "</div>" +
      '<div class="files-layout">' +
      '<div class="file-tree" id="fileTree"><p class="muted">正在读取…</p></div>' +
      '<div class="file-preview" id="filePreview"></div>' +
      "</div>";

    paint("项目文件", html, {
      onReady: function () {
        bindFilesEvents();
        loadProjectTree();
      }
    });
  }

  function markActiveTreeItem(path) {
    document.querySelectorAll("[data-open-file]").forEach(function (node) {
      node.classList.toggle("is-active", node.getAttribute("data-open-file") === path);
    });
  }

  function loadProjectTree() {
    var treeBox = $("fileTree");
    var status = $("filesStatus");
    var rootChip = $("fileRootChip");
    if (!treeBox) return;

    if (OFFLINE) {
      fileState.source = "offline";
      fileState.rootName = OFFLINE.rootName || "离线分享包";
      fileState.rootPath = OFFLINE.rootPath || "";
      fileState.tree = OFFLINE.tree || [];
      rootChip.innerHTML = icon("hard-drive") + esc(fileState.rootName);
      status.textContent = "已读取 " + countFiles(fileState.tree) + " 个离线文件（打包时快照）";
      treeBox.innerHTML = treeHtml(fileState.tree, 0) || '<p class="muted">离线清单是空的。</p>';
      refreshIcons();
      markActiveTreeItem(fileState.currentPath);
      openFilePreview(fileState.currentPath);
      return;
    }

    fetch("/api/tree", { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (data) {
        fileState.source = "server";
        fileState.rootName = data.name;
        fileState.rootPath = data.root;
        fileState.tree = data.entries || [];
        rootChip.innerHTML = icon("hard-drive") + esc(data.name);
        status.textContent = "已读取 " + countFiles(fileState.tree) + " 个文件（" + data.time + "）";
        treeBox.innerHTML = treeHtml(fileState.tree, 0) || '<p class="muted">这个文件夹是空的。</p>';
        refreshIcons();
        markActiveTreeItem(fileState.currentPath);
        openFilePreview(fileState.currentPath);
      })
      .catch(function () {
        fileState.source = "none";
        fileState.tree = [];
        rootChip.innerHTML = icon("hard-drive") + "未连接本地服务";
        status.textContent = "没有连上本地服务，暂时读不到文件夹。";
        treeBox.innerHTML = serverHintHtml();
        refreshIcons();
        openFilePreview(null);
      });
  }

  function readFileText(path) {
    if (fileState.source === "picker") {
      var file = fileState.files[path];
      if (!file) return Promise.resolve({ error: "找不到这个文件，请重新读取文件夹。" });
      if (file.size > 512 * 1024) {
        return Promise.resolve({ error: "这个文件比较大（" + formatSize(file.size) + "），点“新标签打开”看原文件吧。" });
      }
      return file.text().then(function (text) {
        return { text: text, ext: "." + path.split(".").pop() };
      });
    }

    if (fileState.source === "offline") {
      var offlineItem = OFFLINE_FILES[path];
      if (!offlineItem) return Promise.resolve({ error: "离线清单里没有这个文件，请重新打包。" });
      if (typeof offlineItem.text === "string") {
        return Promise.resolve({ text: offlineItem.text, ext: offlineItem.ext });
      }
      return Promise.resolve({ error: "这个文件比较大或不是纯文本，点右上角“新标签打开”查看原文件。" });
    }

    return fetch("/api/file?path=" + encodeURIComponent(path), { cache: "no-store" })
      .then(function (response) {
        return response.json().then(function (data) { return { data: data }; });
      })
      .then(function (result) {
        if (result.data && typeof result.data.text === "string") {
          return { text: result.data.text, ext: result.data.ext };
        }
        return { error: (result.data && result.data.error) || "读取失败。" };
      })
      .catch(function () {
        return { error: "读取失败，请确认本地服务还在运行。" };
      });
  }

  function openFilePreview(path) {
    var box = $("filePreview");
    if (!box) return;

    if (!path) {
      box.innerHTML = '<div class="preview-empty">' + icon("mouse-pointer-click") +
        "<p>左边点一个文件，这里就会显示它的内容。</p></div>";
      refreshIcons();
      return;
    }

    var node = findFileNode(fileState.tree, path);
    var url = fileUrl(path);
    var meta = node ? formatSize(node.size) + " · " + esc(node.mtime || "") : "";
    box.innerHTML =
      '<div class="preview-head"><div class="preview-title"><strong>' + esc(path) + "</strong>" +
      (meta ? '<span class="muted">' + meta + "</span>" : "") + "</div>" +
      (url ? '<a class="link-btn" href="' + esc(url) + '" target="_blank" rel="noopener">' + icon("external-link") + "新标签打开</a>" : "") +
      "</div>" +
      '<div class="preview-body" id="previewBody"><p class="muted">正在读取…</p></div>';
    refreshIcons();

    if (node && node.kind === "image" && url) {
      $("previewBody").innerHTML = '<img src="' + esc(url) + '" alt="' + esc(node.name) +
        '" data-zoom="' + esc(url) + '" data-zoom-title="' + esc(node.name) + '">';
      return;
    }

    readFileText(path).then(function (result) {
      var body = $("previewBody");
      if (!body) return;
      if (result.error) {
        body.innerHTML = '<div class="note danger">' + icon("circle-alert") + "<div>" + esc(result.error) + "</div></div>";
      } else {
        body.innerHTML = codeBlock(result.text, (result.ext || "").replace(".", "") || "text");
      }
      refreshIcons();
    });
  }

  function bindFilesEvents() {
    var reload = $("reloadTree");
    if (reload) {
      reload.addEventListener("click", function () {
        if (fileState.source === "picker") { refreshPickerTree(); toast("已重新读取你选择的文件夹"); }
        else if (fileState.source === "offline") { loadProjectTree(); toast("已重新读取离线文件清单"); }
        else { loadProjectTree(); toast("正在重新读取项目文件夹…"); }
      });
    }
    var pick = $("pickFolder");
    if (pick) pick.addEventListener("click", pickFolder);
  }

  function refreshPickerTree() {
    if (!$("fileTree")) return;
    $("fileTree").innerHTML = treeHtml(fileState.tree, 0);
    refreshIcons();
    markActiveTreeItem(fileState.currentPath);
  }

  function pickKind(name) {
    var ext = ("." + name.split(".").pop()).toLowerCase();
    if (PICK_KINDS.image.indexOf(ext) >= 0) return "image";
    if (ext === ".csv") return "csv";
    if (PICK_KINDS.text.indexOf(ext) >= 0) return "text";
    return "binary";
  }

  function walkDirectory(handle, prefix, depth) {
    var nodes = [];
    var MAX_ENTRIES = 300;
    return new Promise(function (resolve) {
      var iterator = handle.values();
      (function next() {
        iterator.next().then(function (result) {
          if (result.done || nodes.length >= MAX_ENTRIES) { resolve(nodes); return; }
          var entry = result.value;
          if (entry.name.charAt(0) === "." || SKIP_NAMES.indexOf(entry.name) >= 0) { next(); return; }
          var path = prefix ? prefix + "/" + entry.name : entry.name;
          if (entry.kind === "directory") {
            if (depth >= 3) { next(); return; }
            walkDirectory(entry, path, depth + 1).then(function (children) {
              nodes.push({ type: "dir", name: entry.name, path: path, children: children });
              next();
            });
          } else {
            entry.getFile().then(function (file) {
              fileState.files[path] = file;
              nodes.push({
                type: "file", name: entry.name, path: path, size: file.size,
                mtime: new Date(file.lastModified).toLocaleString(),
                ext: ("." + entry.name.split(".").pop()).toLowerCase(),
                kind: pickKind(entry.name)
              });
              next();
            });
          }
        });
      })();
    });
  }

  function pickFolder() {
    if (!window.showDirectoryPicker) {
      toast("这个浏览器不支持“选择文件夹”，请改用 Chrome 或 Edge");
      return;
    }
    window.showDirectoryPicker().then(function (handle) {
      releaseUrls();
      fileState.source = "picker";
      fileState.rootName = handle.name;
      fileState.rootPath = handle.name;
      fileState.files = {};
      $("filesStatus").textContent = "正在读取 " + handle.name + " …";
      return walkDirectory(handle, "", 0);
    }).then(function (entries) {
      if (!entries) return;
      fileState.tree = entries;
      $("fileRootChip").innerHTML = icon("hard-drive") + esc(fileState.rootName);
      $("filesStatus").textContent = "已读取 " + countFiles(entries) + " 个文件（来自你选择的文件夹）";
      $("fileTree").innerHTML = treeHtml(entries, 0) || '<p class="muted">这个文件夹是空的。</p>';
      refreshIcons();
      markActiveTreeItem(null);
      openFilePreview(null);
      toast("已读取文件夹：" + fileState.rootName);
    }).catch(function () { /* 用户取消选择 */ });
  }


  function paint(title, html, options) {
    options = options || {};
    $("crumb").textContent = title;
    document.title = title + " · 时序特征工程学习指引";

    var view = $("view");
    view.innerHTML = html;
    decorate(view);
    refreshIcons();

    if (!options.keepScroll) window.scrollTo(0, 0);
    if (options.focus) {
      var target = document.getElementById(options.focus);
      if (target) target.scrollIntoView({ block: "start" });
    }
    if (options.onReady) options.onReady();
  }

  function parseRoute() {
    var raw = (window.location.hash || "").replace(/^#/, "").trim();
    if (!raw) return { name: "home", raw: "home" };
    if (raw.indexOf("doc-") === 0) return { name: "doc", id: raw.slice(4), raw: raw };
    if (raw.indexOf("script-") === 0) return { name: "script", id: raw.slice(7), raw: raw };
    if (raw.indexOf("file-") === 0) return { name: "files", file: safeDecode(raw.slice(5)), raw: raw };
    if (raw === "files") return { name: "files", raw: raw };
    if (raw.indexOf("table-") === 0) return { name: "tables", focus: raw.slice(6), raw: raw };
    if (raw === "figures") return { name: "figures", raw: raw };
    if (raw === "tables") return { name: "tables", raw: raw };
    if (raw === "roadmap") return { name: "roadmap", raw: raw };
    if (raw === "requirements") return { name: "requirements", raw: raw };
    return { name: "home", raw: "home" };
  }

  function render() {
    var route = parseRoute();
    markActiveNav(route.raw);

    if (route.name === "files") {
      if (lastView === "files" && fileState.tree.length) {
        fileState.currentPath = route.file || null;
        markActiveTreeItem(fileState.currentPath);
        openFilePreview(fileState.currentPath);
        return;
      }
      lastView = "files";
      viewFiles(route);
      return;
    }

    lastView = route.name;

    if (route.name === "doc") {
      var doc = DOC_BY_ID[route.id];
      if (doc) { viewDoc(doc); return; }
    }
    if (route.name === "script") {
      var script = SCRIPT_BY_ID[route.id];
      if (script) { viewScript(script); return; }
    }
    if (route.name === "figures") { viewFigures(); return; }
    if (route.name === "tables") { viewTables(route.focus); return; }
    if (route.name === "roadmap") { viewRoadmap(); return; }
    if (route.name === "requirements") { viewRequirements(); return; }
    viewHome();
  }

  /* ------------------------------------------------------------ 事件绑定 */

  function closeNav() {
    document.querySelector(".app").classList.remove("nav-open");
  }

  function bindEvents() {
    var app = document.querySelector(".app");

    var scrim = document.createElement("div");
    scrim.className = "nav-scrim";
    app.appendChild(scrim);
    scrim.addEventListener("click", closeNav);

    $("menuBtn").addEventListener("click", function () {
      app.classList.toggle("nav-open");
    });

    $("copyPathBtn").addEventListener("click", function () {
      copyText(DATA.projectRoot, "已复制项目路径");
    });

    $("runBtn").addEventListener("click", function () {
      copyText(currentRunText || runBlock(".\\run_all.ps1"), "已复制运行命令，粘贴到 PowerShell 里执行");
    });

    $("dialogClose").addEventListener("click", closeDialog);
    $("dialogBackdrop").addEventListener("click", function (event) {
      if (event.target === $("dialogBackdrop")) closeDialog();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") { closeDialog(); closeNav(); }
    });

    document.addEventListener("click", function (event) {
      var fileButton = event.target.closest("[data-open-file]");
      if (fileButton) {
        event.preventDefault();
        window.location.hash = "file-" + encodeURIComponent(fileButton.getAttribute("data-open-file"));
        return;
      }

      var copyButton = event.target.closest("[data-copy-text]");
      if (copyButton) {
        event.preventDefault();
        copyText(copyButton.getAttribute("data-copy-text"),
          copyButton.getAttribute("data-copy-message") || "已复制");
        return;
      }

      var codeButton = event.target.closest(".code-copy");
      if (codeButton) {
        event.preventDefault();
        var text = COPY_SOURCES.get(codeButton);
        if (text == null) {
          var codeEl = codeButton.closest(".code-block").querySelector("code");
          text = codeEl ? codeEl.textContent : "";
        }
        copyText(text, "已复制代码");
        return;
      }

      var zoom = event.target.closest("[data-zoom]");
      if (zoom) {
        event.preventDefault();
        openDialog(zoom.getAttribute("data-zoom-title") || "图片",
          '<img src="' + esc(zoom.getAttribute("data-zoom")) + '" alt="' +
          esc(zoom.getAttribute("data-zoom-title") || "图片") + '">');
        return;
      }

      if (event.target.closest("#resetProgress")) {
        saveProgress({});
        viewRoadmap();
        markActiveNav("roadmap");
        toast("进度已清空");
        return;
      }

      if (event.target.closest(".nav-item")) closeNav();
    });

    document.addEventListener("change", function (event) {
      var box = event.target.closest("[data-day]");
      if (!box) return;
      var progress = loadProgress();
      if (box.checked) { progress[box.getAttribute("data-day")] = true; }
      else { delete progress[box.getAttribute("data-day")]; }
      saveProgress(progress);

      var item = box.closest(".roadmap-item");
      if (item) item.classList.toggle("is-done", box.checked);

      var done = Object.keys(progress).length;
      var label = document.querySelector(".progress-line span");
      var fill = document.querySelector(".progress-fill");
      if (label) label.textContent = "已完成 " + done + " / " + DATA.roadmap.length;
      if (fill) fill.style.width = Math.round((done / DATA.roadmap.length) * 100) + "%";
    });

    window.addEventListener("hashchange", function () {
      render();
      closeNav();
    });
  }

  /* ------------------------------------------------------------ 启动 */

  buildNav();
  setupSearch();
  bindEvents();
  render();
  refreshIcons();
})();
