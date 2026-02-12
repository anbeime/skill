# 🚀 GitHub推送和Vercel部署指南

## 📋 当前状态

✅ **已完成**:
- 创建了完整的技能管理文档（5个MD文件）
- 生成了本地技能数据JSON（41个技能）
- 创建了Web界面（HTML/CSS）
- 配置了Vercel部署文件
- 创建了README和.gitignore
- 提交到本地Git仓库

❌ **待完成**:
- 推送到GitHub（网络连接问题）
- 部署到Vercel

---

## 🔧 解决网络问题

### 方法1：配置Git代理（推荐）

如果你有代理（如v2rayN），配置Git使用代理：

```bash
# 查看代理端口（通常是10809或7890）
# 在v2rayN中查看：设置 -> 本地监听端口

# 配置Git HTTP代理
git config --global http.proxy http://127.0.0.1:10809
git config --global https.proxy http://127.0.0.1:10809

# 或者使用SOCKS5代理
git config --global http.proxy socks5://127.0.0.1:10808
git config --global https.proxy socks5://127.0.0.1:10808

# 取消代理（如果需要）
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 方法2：使用SSH方式

```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥
cat ~/.ssh/id_ed25519.pub

# 在GitHub添加SSH密钥：
# 1. 访问 https://github.com/settings/keys
# 2. 点击 "New SSH key"
# 3. 粘贴公钥内容

# 修改远程仓库地址为SSH
cd D:\tool\skill-repo
git remote set-url origin git@github.com:anbeime/skill.git
```

### 方法3：使用GitHub Desktop

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录GitHub账号
3. 添加本地仓库：`D:\tool\skill-repo`
4. 点击 "Publish repository" 推送到GitHub

---

## 📤 推送到GitHub

### 步骤1：配置代理后推送

```bash
cd D:\tool\skill-repo

# 配置代理（根据你的代理端口调整）
git config http.proxy http://127.0.0.1:10809
git config https.proxy http://127.0.0.1:10809

# 推送到GitHub
git push -u origin main
```

### 步骤2：验证推送

访问 https://github.com/anbeime/skill 查看是否推送成功

---

## 🌐 部署到Vercel

### 方法1：通过Vercel网站部署（推荐）

1. **访问Vercel**
   - 打开 https://vercel.com
   - 使用GitHub账号登录

2. **导入项目**
   - 点击 "Add New..." -> "Project"
   - 选择 "Import Git Repository"
   - 找到 `anbeime/skill` 仓库
   - 点击 "Import"

3. **配置项目**
   - **Project Name**: skill-store（或自定义）
   - **Framework Preset**: Other
   - **Root Directory**: ./
   - **Build Command**: 留空（静态网站）
   - **Output Directory**: public
   - **Install Command**: 留空

4. **部署**
   - 点击 "Deploy"
   - 等待部署完成（约1-2分钟）
   - 获取部署链接（如：https://skill-store.vercel.app）

### 方法2：通过Vercel CLI部署

```bash
# 安装Vercel CLI
npm install -g vercel

# 登录Vercel
vercel login

# 部署项目
cd D:\tool\skill-repo
vercel

# 首次部署会询问：
# - Set up and deploy? Yes
# - Which scope? 选择你的账号
# - Link to existing project? No
# - What's your project's name? skill-store
# - In which directory is your code located? ./
# - Want to override the settings? No

# 部署到生产环境
vercel --prod
```

---

## 📊 部署后验证

### 检查清单

- [ ] 访问首页：https://your-domain.vercel.app
- [ ] 检查官方技能商店页面
- [ ] 检查本地技能库页面（/local-skills.html）
- [ ] 验证技能数据加载（/data/local_skills.json）
- [ ] 测试筛选功能
- [ ] 测试响应式设计（手机端）

### 预期效果

1. **首页**
   - 显示统计数据（140+官方技能，41本地技能）
   - 显示技能分类卡片
   - 显示核心特性
   - 显示快速开始指南

2. **本地技能库页面**
   - 显示41个技能卡片
   - 筛选功能正常工作
   - 分类筛选正常工作
   - 显示技能详细信息

3. **数据API**
   - `/data/local_skills.json` 可访问
   - 返回正确的JSON数据

---

## 🔄 自动部署

### 配置自动部署

Vercel会自动监听GitHub仓库的变化：

1. **推送到main分支** -> 自动部署到生产环境
2. **推送到其他分支** -> 自动部署到预览环境
3. **Pull Request** -> 自动生成预览链接

### 触发部署

```bash
# 修改文件后
git add .
git commit -m "update: 更新技能数据"
git push origin main

# Vercel会自动检测并部署
```

---

## 📝 后续维护

### 更新技能数据

1. **更新本地技能**
   ```bash
   # 修改 data/local_skills.json
   # 提交并推送
   git add data/local_skills.json
   git commit -m "update: 更新本地技能数据"
   git push origin main
   ```

2. **更新文档**
   ```bash
   # 修改 docs/ 目录下的文档
   # 提交并推送
   git add docs/
   git commit -m "docs: 更新技能管理文档"
   git push origin main
   ```

### 添加新功能

1. **添加技能对比页面**
   - 创建 `public/comparison.html`
   - 实现技能对比功能
   - 推送更新

2. **添加搜索功能**
   - 在现有页面添加搜索框
   - 实现实时搜索
   - 推送更新

---

## 🎯 完成后的成果

### 1. GitHub仓库
- 地址：https://github.com/anbeime/skill
- 包含完整的技能管理文档
- 包含Web界面源代码
- 包含本地技能数据

### 2. Vercel部署
- 地址：https://skill-store.vercel.app（或自定义域名）
- 在线展示技能商店
- 自动更新部署

### 3. 技能库
- 41个可用技能
- 100%备份覆盖
- 完整的文档和迁移指南

---

## 🆘 故障排查

### 问题1：推送失败 - 网络连接超时

**解决方案**：
1. 配置Git代理（见上文）
2. 或使用GitHub Desktop
3. 或使用SSH方式

### 问题2：Vercel部署失败

**解决方案**：
1. 检查 `vercel.json` 配置
2. 确认 `public/` 目录存在
3. 查看Vercel部署日志

### 问题3：数据加载失败

**解决方案**：
1. 检查 `data/local_skills.json` 格式
2. 确认文件路径正确
3. 查看浏览器控制台错误

---

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看GitHub Issues
2. 查看Vercel文档
3. 联系维护者

---

**创建时间**: 2026-02-10  
**最后更新**: 2026-02-10  
**维护者**: 小跃