<<<<<<< HEAD
# Hackathon Team14

## 開発環境

- Docker Desktop
- VS Code
- Dev Containers拡張機能

使用技術：

- Backend: FastAPI
- Frontend: React + Vite
- Database: PostgreSQL（SQLite）

---

# 環境構築

## 1. リポジトリをclone

```bash
git clone "リポジトリURL（SSHの方がいいかも？）
cd hackathon_team14
```

---

## 2. VS Codeで開く

VS Codeでプロジェクトを開く。

必要な拡張機能：

- Dev Containers

インストール後、

```
Cmd + Shift + P
```

を押して、

```
Dev Containers: Reopen in Container
```

を選択。

初回起動時はDockerイメージ作成と依存関係インストールを行うため時間がかかります。

---

## 3. 環境変数設定

ルートディレクトリで以下を実行
cp .env .env.example

※ 本番DB設定は後で変更予定

---

# 起動方法

## Backend

コンテナ内ターミナルで：

```bash
bash scripts/start-backend.sh
```

起動確認：

```
http://localhost:8000/docs
```

---

## Frontend

別ターミナルで：

```bash
bash scripts/start-frontend.sh
```

起動確認：

```
http://localhost:5173
```

---

# Docker構成

```
.
├── backend
│   └── FastAPI
│
├── frontend
│   └── React(Vite)
│
├── docker
│   └── dev
│       └── Dockerfile
│
├── scripts
│   ├── start_backend.sh
│   └── start_frontend.sh
│
├── .devcontainer
│   └── devcontainer.json
│
├── docker-compose.yml
└── .env
```

---

## パッケージ追加

### Backend

```bash
cd backend
uv add <package>
```

例：

```bash
uv add sqlalchemy
```

### Frontend

```bash
cd frontend
npm install <package>
```

例：

```bash
npm install axios
```

---

# 注意事項

## node_modulesについて

frontendのnode_modulesはDocker側で管理しています。

Mac側で直接、

```bash
npm install
```

を実行しないでください。

---

## Pythonパッケージについて

Pythonパッケージはuvで管理しています。

直接：

```bash
pip install
```

は使用しません。
=======
# クイックチャットアプリ

## 1. 概要

### アプリ名
クイックチャットアプリ

### 目的
友人や家族との日常的な連絡をLINE等のSNSよりさらに気軽に行うためのアプリです。

### 背景・課題
ちょっとした隙間時間や疲れている時にLINEを開いて連絡、返信するのは地味にメンドウ・・・
そこで、

・出発
<br>
・帰宅
<br>
・就寝

といった日常的な連絡をワンタップでできるようにしたい

---

# 2. 主な機能

## ユーザー機能

### チャット機能
説明：

- あらかじめ作成しておいた定型文をワンタップで送信
- 送信したメッセージは、instagramのストーリーのように、フォロワー（一部のフォロワー）が閲覧できる

### フォロー機能
説明：

- ID検索で友人や家族をフォローできる

---

## 管理者機能
説明：

- ユーザーの削除等の管理
- チャットの管理

---

# 4. 画面一覧

|画面名|概要|
|-|-|
|ユーザー登録画面|IDとパスワードを設定して新規登録|
|ログイン画面|ユーザー認証|
|チャット送信画面|アプリを開いた時の初期画面|
|チャット閲覧画面|フォロー中のユーザーのチャットを閲覧|
|アカウント情報画面|アカウント管理、フォロー関連機能|
>>>>>>> origin
