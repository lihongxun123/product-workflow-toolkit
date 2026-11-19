# 产品工作流工具箱

四个可独立安装的 Agent Skill，覆盖产品决策、交互原型、研发需求和中文文档。

| Skill | 能完成的任务 |
| --- | --- |
| [产品研究、架构与材料](skills/product-material-workflow/SKILL.md) | 根据项目现状和用户证据比较选项，维护已确认规则。 |
| [高保真原型交付](skills/product-prototype-delivery/SKILL.md) | 沿用项目设计体系，制作并验证正常、异常和边界路径。 |
| [研发需求交付](skills/product-requirement-handoff/SKILL.md) | 写出研发可执行的详细需求、任务摘要和可观察的验收条件。 |
| [中文文档编辑](skills/chinese-document-editor/SKILL.md) | 精简需求、报告和操作说明，保留业务规则与必要证据。 |

## 在 Codex 使用

用 Node.js 22.20 或更高版本运行下面的命令，按提示选择 Skill 和 Codex。运行后开启新会话，按需选择对应 Skill。去掉 `-g` 可以安装到当前项目。 [安装工具说明](https://github.com/vercel-labs/skills#install-a-skill)

```sh
npx skills add lihongxun123/product-workflow-toolkit -g
```

用相同工具安装后，可运行 `npx skills check` 查看更新，或用 `npx skills update <skill-name>` 更新指定 Skill。也可将所需的 Skill 目录原样复制到项目根目录的 `.agents/skills/`。

## 跑一遍示例

从[山岬工坊的活动候补预约](skills/product-material-workflow/references/example/README.md)开始。这个虚构案例包含观察证据、评审决定、离线交互原型、研发需求和验收路径。原型用浏览器打开即可操作。中文文档初筛脚本可选，运行时使用 Python 3.10 或更高版本。

## 维护魔搭合集

### 从 GitHub 手动同步

1. 在 GitHub 的 `main` 分支确认待验收的提交，记下完整 SHA。魔搭从 `main` 拉取更新，验收时用这个固定提交作基准。
2. 用维护账号登录魔搭，依次打开四个 Skill 的设置页：[产品资料](https://modelscope.cn/skills/hongxun/product-material-workflow/setting)、[研发交付](https://modelscope.cn/skills/hongxun/product-requirement-handoff/setting)、[中文编辑](https://modelscope.cn/skills/hongxun/chinese-document-editor/setting)、[原型交付](https://modelscope.cn/skills/hongxun/product-prototype-delivery/setting)。逐项核对来源指向本仓库的 `tree/main/skills/<对应 Skill 名>`。
3. 在每个设置页点击 **手动同步**。如果检测到更新，点 **立即同步**，确认该项的“最近同步”时间已刷新。如果提示已是最新，直接进入安装验收。

### 在空目录验收合集

用 PowerShell 7 新建临时项目，在里面执行合集的原安装命令。后面的核对命令在同一个 PowerShell 会话运行。

```powershell
$project = Join-Path ([IO.Path]::GetTempPath()) ("toolkit-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $project -ErrorAction Stop | Out-Null
Push-Location $project
try {
    npx skills add https://modelscope.cn/collections/hongxun/chanpingongzuoliugongjuxiang --skill "*" -a codex
    if ($LASTEXITCODE -ne 0) { throw "合集安装失败" }
} finally {
    Pop-Location
}
```

将下方的 `$commit` 换成本次要验收的完整 SHA。先查 `skills-lock.json` 中四项的合集来源，再用 GitHub 返回的文件清单和 Git blob 哈希核对 `.agents/skills/` 下的每个文件，包括参考资料、示例和脚本。

```powershell
$commit = 'f41f70393669426419be11c759b6e5e23aee9e07'
$collection = 'https://modelscope.cn/collections/hongxun/chanpingongzuoliugongjuxiang'
$lock = (Get-Content "$project/skills-lock.json" -Raw -ErrorAction Stop | ConvertFrom-Json -AsHashtable).skills
if ($lock.Count -ne 4) { throw "安装记录应包含四个 Skill" }

$tree = Invoke-RestMethod "https://api.github.com/repos/lihongxun123/product-workflow-toolkit/git/trees/${commit}?recursive=1" -ErrorAction Stop
if ($tree.truncated -or !$tree.tree) { throw "GitHub 文件清单不完整" }
$files = $tree.tree | Where-Object { $_.type -eq 'blob' -and $_.path -clike 'skills/*' }
foreach ($name in $lock.Keys) {
    if ($lock[$name].sourceUrl -cne $collection -or $files.path -cnotcontains "skills/$name/SKILL.md") {
        throw "请核对 $name 的安装来源和 GitHub 目录"
    }
}

$expected = $files | ForEach-Object { $_.path.Substring(7) + ' ' + $_.sha }
$root = Join-Path $project '.agents/skills'
$actual = Get-ChildItem -LiteralPath $root -Recurse -Force -File -ErrorAction Stop | ForEach-Object {
    $path = [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\', '/')
    $hash = git hash-object --no-filters -- $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "读取文件失败 $path" }
    "$path $hash"
}
$diff = Compare-Object -ReferenceObject $expected -DifferenceObject @($actual) -CaseSensitive
if ($diff) {
    $diff | Format-Table -AutoSize | Out-Host
    throw "验收失败（<= 为 GitHub 条目，=> 为魔搭安装条目）"
}
"验收通过：4 个 Skill，$($expected.Count) 个文件与 GitHub $commit 一致。"
```

2026-11-19 按此口径验收 [`f41f703`](https://github.com/lihongxun123/product-workflow-toolkit/commit/f41f70393669426419be11c759b6e5e23aee9e07)，产品资料 15 个文件、研发交付 4 个、中文编辑 8 个、原型交付 5 个，合计 32 个文件全部一致。

发布版本为 0.1.3。 [MIT 许可证](LICENSE)
