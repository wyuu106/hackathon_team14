---
name: frontend-dev
description: Reactを使用したフロントエンド機能、画面、コンポーネント、フォーム、API連携などの新規実装・変更を行うときに使用する。
---

# Reactフロントエンド開発

## 基本方針

このプロジェクトでは、Reactを使用してフロントエンドを実装する。

原則として以下を使用する。

- UI: React
- ビルドツール: Vite
- API通信: プロジェクトで既に採用されている方法を使用する
- ルーティング: React Router
- スタイリング: プロジェクトで既に採用されている方法を使用する

新しいフレームワークや大規模なライブラリを、
明示的な指示なしに導入しないこと。

React標準機能や既存の依存関係で実現可能な場合は、
新しいライブラリを追加しないこと。

既存のコンポーネント、hooks、CSS、API通信処理を再利用できる場合は優先して利用する。


## 作業開始前

実装・変更を行う前に以下を確認する。

1. 関連する要件
2. 関連する既存ページ
3. 関連する既存コンポーネント
4. React Routerの既存ルーティング
5. APIとのRequest / Response形式
6. 既存のAPI通信処理
7. 既存のCSS・UIコンポーネント
8. state管理方法
9. 認証・認可への影響
10. 関連するテスト

既存のデザイン・命名規則・ディレクトリ構成・実装パターンを優先すること。


## Component

React Componentは既存プロジェクトのディレクトリ構成に従って配置する。

例:

- `src/components/`
- `src/pages/`

ページ単位のComponentと、
複数画面で再利用するComponentを適切に分離する。

例:

`src/pages/Users.jsx`

`src/components/UserCard.jsx`

Componentには表示とUI操作に関する処理を記述する。

APIアクセス、複雑なデータ変換、ビジネスロジックなどを
巨大なComponent内に集中させないこと。


## Component分割

複数箇所で使用するUIや、
Componentが大きくなった場合は分割を検討する。

例えば以下のようなUIはComponent化を検討する。

- ユーザーカード
- モーダル
- フォーム
- ナビゲーション
- ボタン
- 一覧の各要素

ただし、小さなUIまで過剰にComponent化しないこと。

一度しか使用せず、単純な要素については
無理にComponentへ分割する必要はない。


## State

画面上で変化するデータについては、
必要に応じてReactのstateを使用する。

例:

```javascript
const [users, setUsers] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
```