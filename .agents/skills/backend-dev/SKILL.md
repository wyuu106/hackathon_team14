---
name: backend-dev
description: Python Fast APIでmodels、schemas、cruds、routers、DB、認証・認可などのバックエンド機能を新規実装・変更するときに使用する。
---

# Fast APIバックエンド開発

## 基本方針

このプロジェクトではPython Fast APIの標準的な設計を優先する。

過剰な抽象化や不要なライブラリ追加を避け、
Python Fast API標準機能で実現できる場合はそれを優先する。

- backend/pyproject.toml と uv.lock で依存関係を管理
- DB設定は backend/app/db.py
- Modelは backend/app/models ディレクトリ内に作成
- Schemaは backend/app/schemas ディレクトリに作成
- Crudは backend/app/cruds ディレクトリに作成
- Routerは backend/app/routers ディレクトリに作成
- main.pyにrouterをincludeし、apiを実装する

## 作業開始前

実装・変更を行う前に以下を確認する。

1. 関連する要件・仕様
2. 関連するSQLAlchemy models
3. 関連するPydantic schemas
4. 関連するcruds / services
5. 関連するrouters
6. DB schemaとAlembic migration
7. 関連するテスト
8. 認証・認可への影響
9. 既存API・フロントエンドへの影響

既存の設計・命名規則・責務分割を優先し、
新しい構成を独自に追加する前に既存実装を確認すること。

## Model

Modelは原則として以下に配置する。

`app/models/`

Modelでは主に以下を扱う。

- SQLAlchemyによるDBテーブルの定義
- カラムの定義
- primary key / foreign key
- relationship
- unique制約などのDB制約

例:

```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
```