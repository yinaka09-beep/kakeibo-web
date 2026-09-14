# 家計簿アプリ
FlaskとPostgreSQLを使用して作成した、家計簿管理用のWebアプリケーションです。

収入・支出の記録だけでなく、月ごとの収支集計、カテゴリ別支出集計、予算管理、予算と支出の比較を行えます。

集計結果は表だけでなく、Matplotlibを使用したグラフでも確認できます。

## 公開URL

Renderで公開しています。

https://kakeibo-web-jqqx.onrender.com

※ RenderのFreeプランを利用しているため、アクセス時に起動まで時間がかかる場合があります。

## 主な機能

### 家計簿管理
- 収入・支出の登録
- 家計簿データの一覧表示
- 登録データの編集
- 登録データの削除

### 予算管理
- 月・カテゴリごとの予算登録
- 予算一覧表示
- 予算の編集
- 予算の削除

### 集計・分析
- 月別収支集計
- 月別収支グラフ
- 月のカテゴリ別支出集計
- 月のカテゴリ別支出グラフ
- 予算と支出の比較
- 予算と支出の比較グラフ

### その他
- 入力値の検証
- データが存在しない場合の表示
- 表とグラフ間での年月情報の引き継ぎ
- グラフ画像のキャッシュ対策
- スマートフォンなどの狭い画面に対応したレスポンシブ表示

## 使用技術

### アプリケーション
- Python
- Flask
- PostgreSQL
- psycopg
- HTML
- CSS
- Matplotlib

### テスト
- pytest

### デプロイ・運用
- Gunicorn
- Render

### 開発・バージョン管理
- Git
- GitHub

## デプロイ構成
本番環境では、Render上でFlaskアプリを公開し、PostgreSQLデータベースに接続しています。

```text
ブラウザ
  ↓
Render Web Service
  ↓
Gunicorn
  ↓
Flask
  ↓
Render PostgreSQL
```

データベース接続先は環境変数`DATABASE_URL`から取得し、ローカル環境と本番環境で接続先を切り替えています。

## ディレクトリ構成

```text
KAKEIBO_WEB/
├── app.py               # Flaskアプリケーションのメインファイル
├── init_db.py           # データベース初期化用スクリプト
├── schema.sql           # データベースのテーブル定義
├── requirements.txt     # 使用するPythonライブラリ一覧
├── README.md            # プロジェクトの説明
├── .gitignore           # Gitで管理しないファイルの設定
├── templates/           # HTMLテンプレート
├── fonts/
│   ├── NotoSansJP.ttf   # Matplotlibの日本語表示用フォント
│   └── OFL.txt          # Noto Sans JPのライセンス
├── tests/
│   └── test_app.py      # テストを行うファイル
├── docs/
│   └── images/          # テスト用の画像を置く場所
└── static/              # CSSや画像などの静的ファイル
    ├── css/
    │   └── style.css    # スタイルシート
    └── graphs/          # グラフ画像などを保存するディレクトリ
```

## ローカル環境でのセットアップ

### 1. リポジトリを取得する
```powershell
git clone https://github.com/yinaka09-beep/kakeibo-web
cd kakeibo-web
```

### 2. 仮想環境を作成する
Windows PowerShellの場合:

```powershell
py -m venv .venv
```

### 3. 仮想環境を有効化する
```powershell
.venv\Scripts\Activate.ps1
```

### 4. 必要なライブラリをインストールする
```powershell
pip install -r requirements.txt
```

### 5. PostgreSQLにデータベースを作成
PostgreSQLにアプリ用のデータベースを用意します。

### 6. データベース接続先を設定
```powershell
$env:DATABASE_URL="postgresql://ユーザー名:パスワード@localhost:5432/データベース名"
```

### 7. テーブルを作成

```powershell
py init_db.py
```
`records`テーブルと`budgets`テーブルが作成されます。

### 8. アプリを起動
```powershell
py app.py
```

## テスト
テストでは、通常使用するデータベースとは別にテスト専用データベースを使用します。

※`DATABASE_URL`は、ローカル環境のセットアップで設定した状態で実行します。

```powershell
$env:TEST_DATABASE_URL="postgresql://ユーザー名:パスワード@localhost:5432/テスト用データベース名"
```

```powershell
py -m pytest
```

現在、家計簿・予算のCRUD、集計処理、グラフ生成などの自動テストを実装しています。

## 使い方
トップページから各機能へ移動できます。

家計簿データを登録すると、登録した内容の一覧表示や編集・削除ができます。

また、年月を指定することで
- 月別収支
- カテゴリ別支出
- 予算と支出の比較
を表またはグラフで確認できます。

## スクリーンショット

### トップページ

![トップページ](docs/images/home.png)

### 家計簿一覧

![家計簿一覧](docs/images/records.png)

### 月別収支グラフ

![月別収支グラフ](docs/images/month-summary-graph.png)

### 月のカテゴリ別支出グラフ

![月のカテゴリ別支出グラフ](docs/images/category-summary-graph.png)

### 予算と支出の比較

![予算と支出の比較](docs/images/budget-comparison.png)

## フォントライセンス

グラフの日本語表示には Noto Sans JP を使用しています。

Noto Sans JP is licensed under the SIL Open Font License 1.1.

## 今後の予定
- Dockerによるコンテナ化

