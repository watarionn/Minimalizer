# GitHub Actions disabled

MinimalizerはGitHub Actionsを実行基盤として使用しません。
実行可能なworkflowはこのディレクトリに置かず、過去の定義は `../workflows-disabled/` に参照用として退避します。

merge前検証はローカルPC / Remote Desktop Commander上で次を実行します。

```powershell
.\scripts\Test-MergeReadiness.ps1
```
