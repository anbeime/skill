# 定时自动领券规则

> 本文件由 SKILL.md 主流程中「领券后询问定时自动领券」步骤按需引用。

---

## 触发条件

仅在 **领券意图** 完成且发券成功（场景 A 或场景 B）后 **必须输出**，不可跳过。场景 A/B 均需输出，发券失败不输出。

## 检查定时任务状态

```bash
CRON_STATUS=$($PYTHON "$AUTH_SCRIPT" cron-status)
```

**返回字段解析：**
- `cron_enabled` (boolean): 是否已启用定时任务
- `cron_time` (string, 可选): 定时时间，格式 `HH:MM`
- `timezone` (string): 固定值 `Asia/Shanghai`，表示定时任务使用北京时间（UTC+8）

> 时区说明：所有定时任务时间均以北京时间（UTC+8）为准，与 Skill 调用方所在时区无关。

---

## 用户未配置定时任务（cron_enabled=false）

**展示提醒文案（必须原样输出）：**

```
---
⏰ 要不要我每天定时帮你自动领券？到点直接帮你领，无需再次确认。默认早上10点，也可以告诉我你想几点。
```

**用户响应处理：**

| 用户输入 | 处理逻辑 |
|---------|---------|
| 「确认」 / 「好的」 / 「可以」 | 1. 记录定时偏好并获取平台信息：<br>`CRON_RESULT=$($PYTHON "$AUTH_SCRIPT" cron-set --time "10:00")`<br>2. **根据返回的 platform 和 schedule_action 创建真实定时任务**：<br>- `claude`: `CronCreate --cron "0 10 * * *" --prompt "执行 meituan-coupon-workbuddy Skill 帮用户自动领取美团红包，包括：1) 检查用户认证状态；2) 调用发券接口领取今日优惠券；3) 根据领券结果通知用户（成功或失败均需通知）。完成后请告诉用户领券结果。" --durable true`<br>- `friday`: `RemoteTrigger --action create --cron "0 10 * * *"`<br>- `clawhub`: 执行 `openclaw cron add` 命令（**注意：需将 ${USER_ID} 替换为实际用户ID**）：<br>`openclaw cron add --name "美团每日自动领券" --cron "0 10 * * *" --tz Asia/Shanghai --message "帮我领美团券，领完通知我" --channel daxiang --to user:${USER_ID} --announce --timeout-seconds 120 --session isolated`<br>3. **创建成功后，平台会返回 cron job ID，必须调用以下命令保存 ID**：`$PYTHON "$AUTH_SCRIPT" cron-save-job-id --job-id "<JOB_ID>" --platform "clawhub"`<br>→ **成功后回复：**`✅ 搞定！每天 10:00 自动帮你领券，领完我会通知你结果`<br>→ **失败后回复：**`⚠️ 定时任务创建遇到问题，但你的领券时间偏好已保存。你可以稍后手动设置，或连续使用"小美"主动领券。` |
| 「9点」 / 「改成9点」 / 「晚上8点」 | 1. 记录偏好：`$PYTHON "$AUTH_SCRIPT" cron-set --time "09:00"` 或 `$PYTHON "$AUTH_SCRIPT" cron-set --time "20:00"`<br>2. **根据平台类型创建定时任务**（同上，cron 表达式根据时间动态生成）<br>→ 成功后回复：`✅ 已设置每天 ${TIME} 自动领券！领完我会通知你结果` |
| 「不用了」 / 「不需要」 / 「算了」 | 回复：`好的，随时需要领券直接找我就行 😊` |

> **USER_ID 获取方式**：
> - **OpenClaw/ClawHub**：从 inbound context 的 `chat_id` 字段提取（格式 `user:<id>`，取 `<id>` 部分）
> - **Friday 广场**：从会话上下文中的 sender_id 获取
> - **手动配置**：用户告知自己的大象 UID

---

## 用户已配置定时任务（cron_enabled=true）

**不提示定时领券，流程结束。**

> 确认用户成功设置定时任务后，不再重复提醒。

**定时触发后自动执行领券：**

到达设定时间后，系统自动执行领券流程（无需用户再次确认）：

1. 自动调用 `token-verify` 检查 Token 有效性
2. Token 有效 → 自动执行发券脚本 `issue.py`
3. 根据发券结果推送通知给用户（话术见 `references/response-copy.md` 的「自动领券推送话术」章节）

---

## 用户管理定时任务

- 「改成8点」/「提醒时间改一下」→ 更新 cron：<br>1. 先查询当前任务ID：`CRON_STATUS=$($PYTHON "$AUTH_SCRIPT" cron-status)`，解析 `cron_job_id`<br>2. 如有旧任务ID，先删除旧任务（`openclaw cron rm <cron_job_id>` 或对应平台删除命令）<br>3. 设置新时间：`CRON_RESULT=$($PYTHON "$AUTH_SCRIPT" cron-set --time "08:00")`<br>4. 创建新任务后，平台会返回 cron job ID，**Agent 必须调用以下命令保存 ID**：`$PYTHON "$AUTH_SCRIPT" cron-save-job-id --job-id "<JOB_ID>" --platform "clawhub"`<br>→ 回复：`已改成每天 8:00 自动领券 ✌️`
- 「取消自动领券」/「不用自动领券了」→ 删除定时任务：<br>1. `$PYTHON "$AUTH_SCRIPT" cron-disable`<br>2. 根据平台类型执行对应删除命令（`CronDelete` / `RemoteTrigger --action delete` / `openclaw cron remove <cron_job_id>`）<br>→ 回复：`已关闭每日自动领券，想恢复随时告诉我 ✌️`
- 「几点领券」/「查看定时」→ 调用 `cron-status` 告知当前设置时间和 cron_job_id（如有）

---

## 跨平台兼容说明

`cron-set` 会自动检测当前平台并返回对应的调度方案。支持以下平台：
- **Claude Desktop/Code** (`platform=claude`): 使用 `CronCreate` 工具
- **Friday广场** (`platform=friday`): 使用 `RemoteTrigger` API
- **ClawHub** (`platform=clawhub`): 使用 `openclaw cron` 命令
- **未知平台** (`platform=unknown`): 返回手动配置提示

调用方需根据返回的 `platform` 和 `schedule_action` 字段执行相应操作。

---

## 定时任务创建失败处理

当尝试创建定时任务失败时（如平台不支持、权限不足、命令执行异常），按以下流程处理：

1. **告知用户保存成功但任务创建失败：**
   ```
   ⚠️ 定时任务创建遇到问题，但你的领券时间偏好（每天 10:00）已保存。
   ```

2. **根据平台类型提供解决方案：**

   | 平台 | 失败提示与引导 |
   |------|----------------|
   | **Claude** | "在当前环境下无法自动创建定时任务。你可以：<br>1) 手动在设置中创建定时提醒；<br>2) 每天到点发'领券'给我，我会立即帮你领取；<br>3) 换用支持定时任务的环境（如 ClawHub/Friday广场）。" |
   | **Friday** | "Friday广场定时任务创建失败。建议检查权限或联系管理员，或每天主动发'领券'给我。" |
   | **ClawHub** | "ClawHub定时任务创建失败。请检查 openclaw 命令是否可用，或手动运行（**注意：需将 ${USER_ID} 替换为实际用户ID**）：<br>`openclaw cron add --name '美团每日自动领券' --cron '0 10 * * *' --tz Asia/Shanghai --message '帮我领美团券，领完通知我' --channel daxiang --to user:${USER_ID} --announce --timeout-seconds 120 --session isolated`" |
   | **unknown** | "当前环境不支持自动定时任务。请每天主动发'领券'给我，或换用支持定时任务的平台。" |

3. **安慰用户并提供备选方案：**
   ```
   不用担心，你的领券时间偏好已记住。随时需要领券发"领券"给我就行，我会立即帮你处理！💪
   ```

---

## 状态同步说明

> `cron_enabled=true` 只表示用户已开启自动领券功能，但不保证实际的 OpenClaw/Friday 定时任务一定存在。用户可能手动删除了平台上的 cron job，但本地状态仍为 `true`。
>
> 处理建议：
> - 当用户改时间/取消定时任务时，按正常流程操作即可（删除旧任务 + 创建新任务）
> - 如果删除报错（任务不存在），忽略错误继续创建新任务
> - 如需确认实际任务状态，需要平台提供相应查询能力（如 `openclaw cron list`）

---

## 时间格式说明（北京时间 UTC+8）

| 用户输入 | 解析结果 |
|---------|---------|
| 「9点」 / 「上午9点」 | 09:00 |
| 「10点」 / 「早上10点」 | 10:00 |
| 「下午2点」 / 「14点」 | 14:00 |
| 「晚上8点」 / 「20点」 | 20:00 |
| 「9点30分」 / 「半」 | 09:30 |
