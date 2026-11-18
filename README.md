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

发布版本为 0.1.3。 [MIT 许可证](LICENSE)
