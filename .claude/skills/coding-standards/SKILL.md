---
name: coding-standards
description: Python/Terraformのコーディング規約。コード作成、修正、レビュー時に参照。型ヒント、dataclass、Ruff、CIDR設定など。
allowed-tools: Read, Grep, Glob
---

# Coding Standards

## Python

| ルール | 詳細 |
|--------|------|
| 型ヒント | 必須。Python 3.11+ union syntax `X | None` |
| データ構造 | `dataclass` で定義 |
| 環境変数 | `os.getenv()` で取得 |
| フォーマッタ | Ruff (line-length=88) |
| エラー処理 | 適切にハンドリングしてUIに表示 |

### 例

```python
from dataclasses import dataclass

@dataclass
class RepoInfo:
    name: str
    description: str | None
    language: str | None
    stars: int
```

## Terraform

| ルール | 詳細 |
|--------|------|
| ingress | `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` のみ |
| egress | VPC Connector経由 `ALL_TRAFFIC` |
| CIDR | 重複禁止: connector=10.8.0.0/28, subnet=10.10.0.0/24 |
| ポート | Streamlit=8501 (container_port設定) |
| イメージタグ | main.tf と gcloud builds submit で一致 |

### コマンド

```bash
cd terraform
terraform fmt && terraform validate
terraform plan
terraform apply
```
