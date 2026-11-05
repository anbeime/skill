"use strict";
(() => {
  const kind = location.pathname.endsWith("layouts.html") ? "layout" : "style";
  const nav = document.querySelector(".sub-nav");
  const main = document.querySelector("main");
  if (!nav || !main) return;
  const ownLabel = kind === "style" ? "我的画风" : "我的图型";
  const panel = document.createElement("section");
  panel.hidden = true;
  panel.setAttribute("aria-label", "个人资源库");
  panel.style.cssText = "padding:25px 0;max-width:1100px;margin:auto";
  const previousHidden = new Map();
  let active = false;
  const buttons = [];

  function restore() {
    if (!active) return;
    previousHidden.forEach((hidden, node) => { node.hidden = hidden; });
    previousHidden.clear(); panel.hidden = true; active = false;
    buttons.forEach((button) => button.classList.remove("is-active"));
  }
  const officialButtons = [...nav.querySelectorAll("button")];
  officialButtons.forEach((button) => button.addEventListener("click", restore, { capture: true }));
  function element(tag, text) { const node = document.createElement(tag); node.textContent = text; return node; }
  function show(section, button) {
    if (!active) {
      [...main.children].forEach((node) => { if (node !== panel) { previousHidden.set(node, node.hidden); node.hidden = true; } });
    }
    active = true; panel.hidden = false;
    [...nav.querySelectorAll("button")].forEach((node) => node.classList.toggle("is-active", node === button));
    const records = (window.HANDRAW_PERSONAL_LIBRARY?.resources || []).filter((item) => item.kind === kind && item.section === section);
    panel.replaceChildren(element("h1", section === "owned" ? ownLabel : "我的收藏"),
      element("p", "个人资源与官方编号库独立。收藏保留来源；同步和本地修改不会自动公开。"));
    if (!records.length) {
      panel.append(element("p", location.protocol === "file:" ? "这里还没有资源。向 Skill 说“创建我的画风／图型”或“同步我的收藏”即可开始。" : "个人资源仅在本地 Skill 中显示。登录社区后可查看云端收藏与解锁状态。"));
    }
    for (const resource of records) {
      const article = document.createElement("article");
      article.style.cssText = "padding:20px 0;border-bottom:1px solid #ded8cf";
      article.append(element("h2", resource.name || resource.title || resource.id),
        element("p", `${resource.id} · v${resource.version || "1.0.0"}`), element("p", resource.prompt_zh));
      if (resource.origin?.author) article.append(element("p", `原作者：${resource.origin.author.username || resource.origin.author}`));
      article.append(element("p", `授权：${resource.license}`));
      const copy = element("button", "复制完整定义");
      copy.type = "button"; copy.className = "copy";
      copy.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(`${resource.prompt_zh}\n\n${resource.prompt_en}`); copy.textContent = "已复制"; }
        catch { copy.textContent = "请选择下方文本复制"; const text = element("textarea", `${resource.prompt_zh}\n\n${resource.prompt_en}`); article.append(text); text.select(); }
      });
      article.append(copy); panel.append(article);
    }
    const link = element("a", "前往社区资源与收藏 ↗");
    link.href = "https://handraw-style.com/studio?view=resources"; link.target = "_blank"; link.rel = "noopener noreferrer";
    panel.append(link);
  }
  main.prepend(panel);
  for (const [section, name] of [["owned", ownLabel], ["collected", "我的收藏"]]) {
    const button = element("button", name);
    button.type = "button"; button.className = "filter";
    button.dataset.labelZh = name; button.dataset.labelEn = section === "owned" ? "My resources" : "My collection";
    button.addEventListener("click", () => show(section, button));
    nav.append(button); buttons.push(button);
  }
  if (location.protocol === "file:") {
    const data = document.createElement("script");
    data.src = "../../../.handraw-personal/library.js";
    document.head.append(data);
  }
})();
