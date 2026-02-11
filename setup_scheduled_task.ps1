# 使用 Windows 任务计划程序设置自动更新
# PowerShell 脚本

$TaskName = "SkillStoreAutoUpdate"
$ScriptPath = "C:\D\StepFun\skill_store_updater\main.py"
$WorkingDir = "C:\D\StepFun\skill_store_updater"
$PythonPath = (Get-Command python).Source

# 创建任务操作
$Action = New-ScheduledTaskAction -Execute $PythonPath `
    -Argument "$ScriptPath --once" `
    -WorkingDirectory $WorkingDir

# 创建触发器（每天凌晨2点执行）
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# 创建任务设置
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# 注册任务
Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "自动从 GitHub 更新技能商店数据" `
    -Force

Write-Host "定时任务已创建: $TaskName"
Write-Host "执行时间: 每天凌晨 2:00"
Write-Host "可在'任务计划程序'中查看和管理"
