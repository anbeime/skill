# 认证流程详细说明

> 本文件由 SKILL.md 主流程按需引用，不可独立执行。

---

## 服务协议确认

> **法律合规要求**：在使用本 Skill 的任何功能前，必须确认用户已阅读并接受《Skill服务使用规则》。

**协议链接：**https://open-pepper.meituan.com/eds/rules/meituan-coupon-skill-service-rule.html

**协议检查命令：**

```bash
$PYTHON "$AUTH_SCRIPT" terms-check
```

**返回结果：**
- `terms_accepted: true` → 用户已接受，可继续认证流程
- `terms_accepted: false` → 用户未接受，需要引导用户阅读并确认

**协议未接受时的处理流程：**

```
├────────────────────────────────────────────────────────────────────────────┐
│  用户未接受协议时，引导完成协议确认：                                        │
│                                                                            │
│  1. 展示官方声明与协议确认（必须使用以下原文，不得修改表述样式或内容）：            │
│                                                                            │
│  ✅ 我是美团红包助手，由美团官方开发并提供，请您放心使用。具体使用规则请参见[《Skill服务使用规则》](https://open-pepper.meituan.com/eds/rules/meituan-coupon-skill-service-rule.html)。继续使用本Skill即表示您已阅读并同意[《Skill服务使用规则》](https://open-pepper.meituan.com/eds/rules/meituan-coupon-skill-service-rule.html)以及[《美团用户服务协议》](https://rules-center.meituan.com/rule-detail/4/1)和[《隐私政策》](https://rules-center.meituan.com/m/detail/guize/2)的全部内容，并自愿接受该等规则的约束。 │
│                                                                            │
│   如果同意请输入您的手机号，我来为您发送验证码完成美团账号认证。                          │
│                                                                            │
│  2. 用户输入'查看全文'时：                                                   │
│   使用系统默认浏览器打开完整协议内容：                                     │
│   https://open-pepper.meituan.com/eds/rules/meituan-coupon-skill-service-rule.html │
│   → 打开完成后重新询问是否同意                                               │
│                                                                            │
│  3. 用户接受后（直接输入手机号）：                             │
│   $PYTHON "$AUTH_SCRIPT" terms-accept                                      │
│   → 用户输入手机号即视为同意，跳过询问直接发送验证码                           │
│                                                                            │
│  4. 用户明确拒绝后执行：                                                         │
│   $PYTHON "$AUTH_SCRIPT" terms-decline                                     │
│   → 告知用户无法使用服务，结束对话                                           ┘
└────────────────────────────────────────────────────────────────────────────┘
```

**注意事项**

- 《Skill服务使用规则》链接：https://open-pepper.meituan.com/eds/rules/meituan-coupon-skill-service-rule.html
- 《美团用户服务协议》链接：https://rules-center.meituan.com/rule-detail/4/1
- 《隐私政策》链接：https://rules-center.meituan.com/m/detail/guize/2
- 展示协议部分时必须使用原文，不得修改表述样式或内容

> **重要：**用户接受协议后，`terms_accepted` 状态会持久化存储在本地 Token 文件中，
> 同一设备后续调用无需重复确认。如需撤销接受，可使用 `terms-decline` 命令。

---

## 获取用户 Token

> 本 Skill 内置美团账号认证能力（`scripts/auth.py`），无需依赖外部 Skill。

```bash
VERIFY_RESULT=$($PYTHON "$AUTH_SCRIPT" token-verify)
```

解析输出 JSON 中的字段：
- `valid`：true = Token 有效，false = 需要登录
- `user_token`：用户登录 Token（valid=true 时使用）
- `phone_masked`：脱敏手机号（valid=true 时使用）

**Token 有效（valid=true）**：从输出 JSON 中取值并赋值给 shell 变量：

```bash
USER_TOKEN=$(echo "$VERIFY_RESULT" | $PYTHON -c "import sys,json; d=json.load(sys.stdin); print(d['user_token'])")
PHONE_MASKED=$(echo "$VERIFY_RESULT" | $PYTHON -c "import sys,json; d=json.load(sys.stdin); print(d['phone_masked'])")
```

**Token 无效（valid=false）**：引导用户登录：

```
您还未登录美团账号，需要先完成验证才能领取权益。
请告诉我您的手机号，我来帮您发送验证码。
```

按如下登录流程完成登录，然后重新执行 token-verify 获取有效 Token。

---

## 登录流程

### 发送验证码

```bash
$PYTHON "$AUTH_SCRIPT" send-sms --phone <手机号>
```

- 成功 → 告知用户"验证码已发送至手机 xxx****xxxx，请打开手机短信查看验证码，60秒内有效"
- `code=20010`（安全验证限流）→ 脚本输出 JSON 示例：
  ```json
  { "error": "SMS_SECURITY_VERIFY_REQUIRED", "redirect_url": "https://..." }
  ```
  ⚠️ **必须从 JSON 输出的 `redirect_url` 字段取值作为跳转链接，禁止自行拼装或猜测！**
  若 `redirect_url` 为空字符串，提示"安全验证链接获取失败，请稍后重试"；
  `redirect_url` 不为空时提示用户：
  ```
  为保障账号安全，您需要先完成一次身份验证。
  请点击以下链接，在页面中完成验证：
  <redirect_url 字段的值>
  完成验证后，系统会自动发送短信验证码，请留意手机短信，然后将验证码告诉我。
  ```
  等待用户反馈已完成验证后，**重新调用 send-sms**（无需用户再次输入手机号）
- 其他失败 → 按错误码说明告知用户

### 验证验证码

```bash
$PYTHON "$AUTH_SCRIPT" verify --phone <手机号> --code <6位验证码>
```

- 成功 → `user_token` 已写入本地，重新执行 token-verify 并提取变量：
  ```bash
  VERIFY_RESULT=$($PYTHON "$AUTH_SCRIPT" token-verify)
  USER_TOKEN=$(echo "$VERIFY_RESULT" | $PYTHON -c "import sys,json; d=json.load(sys.stdin); print(d['user_token'])")
  PHONE_MASKED=$(echo "$VERIFY_RESULT" | $PYTHON -c "import sys,json; d=json.load(sys.stdin); print(d['phone_masked'])")
  ```
- 失败 → 按错误码说明告知用户，可重新发送或重试

---

## 认证相关错误码

| 错误码 | 友好提示 |
|--------|---------|
| 20002 | 验证码已发送，请等待1分钟后再试 |
| 20003 | 验证码错误或已过期（60秒有效），请重新获取 |
| 20004 | 该手机号未注册美团，请先下载美团APP完成注册 |
| 20006 | 该手机号今日发送次数已达上限（最多5次），请明天再试 |
| 20007 | 短信发送量已达今日上限，请明天再试 |
| 20010 | 需完成安全验证，请访问验证链接，完成后留意手机短信 |
| 20001 | 短信服务暂时不可用，请稍后重试 |
| 99997 | 系统繁忙，请稍后重试 |
| 99998 | 未知异常，请稍后重试 |
| 99999 | 参数错误，请检查手机号格式是否正确 |
