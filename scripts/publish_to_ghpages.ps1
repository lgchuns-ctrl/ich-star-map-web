param(
  [string]$ProjectDir = (Get-Location).Path,
  [string]$GitName = "lgchuns-ctrl",
  [string]$GitEmail = "lgchuns-ctrl@users.noreply.github.com"
)

$ErrorActionPreference = "Stop"
$tmp = $null

function Assert-GitOk([string]$Message) {
  if ($LASTEXITCODE -ne 0) { throw $Message }
}

if ((git branch --show-current) -eq "gh-pages") {
  git checkout main
  Assert-GitOk "切换到 main 失败"
}

$dirty = git status --porcelain
if ($LASTEXITCODE -ne 0) { throw "无法读取 git 状态" }
if ($dirty) {
  throw '工作区有未提交的改动，请先提交：git add -A && git commit -m "你的改动说明"'
}

Write-Host "== 1/4 构建前端 =="
Push-Location (Join-Path $ProjectDir "web")
try {
  & npm.cmd run build
  if ($LASTEXITCODE -ne 0) { throw "构建失败" }
} finally {
  Pop-Location
}

Write-Host "== 2/4 准备 gh-pages 分支 =="
git fetch origin gh-pages
Assert-GitOk "git fetch 失败，请检查代理与网络"

if (git show-ref --verify --quiet refs/remotes/origin/gh-pages) {
  if (git show-ref --verify --quiet refs/heads/gh-pages) {
    git branch -f gh-pages origin/gh-pages
    Assert-GitOk "无法将本地 gh-pages 对齐到 origin/gh-pages"
  } else {
    git branch gh-pages origin/gh-pages
    Assert-GitOk "无法创建本地 gh-pages 分支"
  }
} elseif (-not (git show-ref --verify --quiet refs/heads/gh-pages)) {
  Write-Host "远端没有 gh-pages，创建空分支"
  git checkout --orphan gh-pages
  Assert-GitOk "无法创建 gh-pages 空分支"
  git rm -rf . | Out-Null
  git commit --allow-empty -m "init gh-pages"
  git checkout main
}

$tmp = Join-Path $env:TEMP ("ghpages_" + [guid]::NewGuid().ToString("N"))
git worktree add $tmp gh-pages
if ($LASTEXITCODE -ne 0) { throw "无法创建工作区（请确认当前不在 gh-pages 分支）" }

try {
  Write-Host "== 3/4 同步构建产物 =="
  Push-Location $tmp
  try {
    Get-ChildItem -Force | Where-Object { $_.Name -ne ".git" } | Remove-Item -Recurse -Force
    Copy-Item -Recurse -Force (Join-Path $ProjectDir "web\dist\*") .
    New-Item -ItemType File -Name ".nojekyll" -Force | Out-Null
    git add -A
    if ((git status --porcelain | Measure-Object -Line).Lines -gt 0) {
      git -c user.name=$GitName -c user.email=$GitEmail commit -m "update site"
      Assert-GitOk "提交失败"
    } else {
      Write-Host "没有内容变化，跳过提交"
    }
  } finally {
    Pop-Location
  }

  Write-Host "== 4/4 推送 =="
  git push origin gh-pages
  Assert-GitOk "推送失败，请检查代理与网络"
} finally {
  if ($tmp -and (Test-Path $tmp)) {
    git worktree remove --force $tmp | Out-Null
  }
}

Write-Host ""
$repoName = (Split-Path (git remote get-url origin) -Leaf) -replace '\.git$',''
Write-Host "完成！请等待 1-2 分钟后打开（Ctrl+F5 强刷）："
Write-Host "  https://$($GitName).github.io/$repoName/"
