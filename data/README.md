# 可选的本地 JMdict 数据包

网页会先尝试从本目录读取固定文件名，找不到时再访问 jmdict-simplified 的 GitHub Release。
将下载好的文件原样放在这里，可避免用户首次安装词典时访问外部下载站。

- `jmdict-eng-common-3.6.2+20260727141257.json.tgz`
  - 常用词库，约 1.37 MB 压缩包
  - SHA-256: `a7f9e1f6fd14ff361fa86fbeafa2261ee215c6ffff7e4b2625df26b7fba47173`
- `jmdict-examples-eng-3.6.2+20260727141257.json.tgz`
  - 完整英文例句词库，约 13.4 MB 压缩包
  - SHA-256: `508d41af24121624d69b2cf35aa9e5dc214a3272c529f688518c1025bf870f11`

也可以不放。进入网页的“词典与 SRS → 词典制卡”点击安装，或手动选择 `.tgz` / `.json` 导入。

JMdict 词典数据版权归 Electronic Dictionary Research and Development Group 所有，使用时遵循 CC BY-SA 4.0 与项目发布说明。本仓库默认不重新分发词典数据。
