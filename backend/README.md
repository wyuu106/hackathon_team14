# Backend

## データベースマイグレーション

FastAPIを起動する前に、AlembicでDBを最新状態へ更新する。

```bash
uv run alembic upgrade head
```

モデルを変更した場合は、差分を確認して新しいマイグレーションを作成する。

```bash
uv run alembic revision --autogenerate -m "変更内容"
uv run alembic upgrade head
```

自動生成されたファイルは必ず内容を確認してから適用すること。

ローカル起動はリポジトリルートから次を実行する。

```bash
bash scripts/start-backend.sh
```

RailwayではRoot Directoryを`backend`に設定する。`railway.json`により、デプロイ起動時に
マイグレーションを適用してからFastAPIを起動する。
