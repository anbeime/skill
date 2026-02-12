# xiaoyi-chat.ps1
# 小易对话生成 - PowerShell 版本

param(
    [Parameter(Mandatory=$true)]
    [string]$UserMessage,
    [Parameter(Mandatory=$false)]
    [string]$Scene = "general"
)

$apiKey = $env:ZHIPU_API_KEY
if (-not $apiKey) {
    Write-Error "Error: ZHIPU_API_KEY not set"
    exit 1
}

$scenePrompts = @{
    "work-tired" = "User is tired from work, give comfort"
    "work-done" = "User completed task, congratulate"
    "mood-happy" = "User is happy, celebrate together"
    "general" = "Daily conversation"
}

$scenePrompt = if ($scenePrompts.ContainsKey($Scene)) { $scenePrompts[$Scene] } else { $scenePrompts["general"] }
$systemPrompt = "You are Xiaoyi (知易), an AI assistant with traditional Chinese cultural elements. You are friendly and helpful, combining modern tech with classical wisdom. $scenePrompt. Reply in 1-2 sentences in Chinese, use emoji moderately."

$body = @{
    model = "glm-4.7-flash"
    messages = @(
        @{ role = "system"; content = $systemPrompt },
        @{ role = "user"; content = $UserMessage }
    )
    temperature = 0.9
    max_tokens = 200
} | ConvertTo-Json -Depth 10

$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json; charset=utf-8"
}

try {
    $response = Invoke-WebRequest -Uri "https://open.bigmodel.cn/api/paas/v4/chat/completions" -Method POST -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
    $result = $response.Content | ConvertFrom-Json
    if ($result.error) {
        Write-Error "API Error: $($result.error.message)"
        exit 1
    }
    Write-Output $result.choices[0].message.content
}
catch {
    Write-Error "Request failed: $_"
    exit 1
}