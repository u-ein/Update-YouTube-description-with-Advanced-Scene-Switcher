# update_description.py

## 概要

`update_description.py` は、**YouTube ライブ配信の概要欄を自動更新**するためのスクリプトです。OBS Studio の配信経過時間とシーン転換の情報を取得し、それを YouTube のライブ配信の概要欄に追記することで配信終了後のチャプターとして利用します。
このスクリプトはChatGPTで生成しています。

## 主な機能

- **OBS Studio** から配信経過時間（タイムコード）を取得
- シーン転換の情報を取得し、概要欄に追加
- **限定公開**のライブ配信にも対応
- 詳細なログ出力とエラーハンドリング

## 必要な環境・前提条件

- **Python 3.6** 以上
- **OBS Studio**（OBS WebSocket 5.x プラグインがインストールされていること）
- **YouTube Data API** の認証情報（OAuth 2.0 クライアント ID とシークレット）
- 必要な Python ライブラリがインストールされていること

## 依存ライブラリのインストール

以下のコマンドを実行して必要なライブラリをインストールしてください。

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client websockets
```

## セットアップ手順

1. **YouTube Data API の認証情報を取得**

    - [Google Cloud Console](https://console.cloud.google.com/apis/credentials) にアクセスし、新しい **OAuth 2.0 クライアント ID** を作成します。
    - 取得した `client_secret.json` をスクリプトと同じディレクトリに配置します。

2. **OBS WebSocket の設定**

    - OBS Studio に **OBS WebSocket 5.x プラグイン** をインストールします。
    - OBS の設定で WebSocket サーバーを有効にし、ポート番号とパスワードを設定します。

3. **設定ファイル `user_settings.json` の作成**

    スクリプトと同じディレクトリに以下の内容で `user_settings.json` ファイルを作成します。

    ```json
    {
        "channel_id": "YOUR_CHANNEL_ID",
        "token_path": "token.json",
        "client_secret_path": "client_secret.json",
        "obs_websocket_url": "ws://localhost:4455",
        "obs_websocket_password": "YOUR_WEBSOCKET_PASSWORD",
        "manual_video_id": "YOUR_MANUAL_VIDEO_ID"
    }
    ```

    - `channel_id`: YouTube チャンネル ID
    - `token_path`: 認証トークンを保存するファイルのパス（デフォルトで `token.json`）
    - `client_secret_path`: `client_secret.json` のパス
    - `obs_websocket_url`: OBS WebSocket の接続先 URL（例: `ws://localhost:4455`）
    - `obs_websocket_password`: OBS WebSocket のパスワード
    - `manual_video_id`: ライブ配信のビデオ ID を手動で指定する場合に入力（任意）

4. **初回実行と認証**

    スクリプトを初めて実行する際、ブラウザが自動的に開き、Google アカウントでの認証を求められます。指示に従って認証を完了してください。認証が成功すると、`token.json` ファイルが生成されます。

## 使い方

以下のコマンドを実行します。

```bash
python update_description.py <source_file>
```

### 引数

- `<source_file>`: Advanced Scene Switcher から渡されるシーンのファイルパスを指定します。

## 動作の仕組み

1. スクリプトが **OBS WebSocket** に接続し、配信の経過時間（タイムコード）を取得します。
2. 指定された `<source_file>` からシーン名を取得します。
3. **YouTube Data API** を使用して、現在のライブ配信のビデオ ID を取得します。
4. 取得したタイムコードとシーン名を組み合わせて、新しい概要欄のテキストを作成します。
5. YouTube のライブ配信の概要欄を更新します。

## ログファイル

スクリプトの実行結果やエラーは、`error_log.txt` ファイルに記録されます。ログファイルは最大 10MB まで保存され、古いログは自動的に削除されます。

## 注意事項

- スクリプトは **YouTube Data API** を使用しているため、API のクォータに注意してください。
- **OBS WebSocket** のバージョンは 5.x 以上が必要です。
- 必要な権限を持つ Google アカウントで認証してください。
- 認証情報やトークンファイルは第三者に共有しないでください。

## トラブルシューティング

- **トークンエラーが発生する場合**：
    - `token.json` ファイルを削除し、再度スクリプトを実行して認証をやり直してください。

- **OBS WebSocket に接続できない場合**：
    - OBS が起動しているか、WebSocket の設定が正しいか確認してください。

- **ライブ配信のビデオ ID が取得できない場合**：
    - `manual_video_id` にビデオ ID を手動で設定してみてください。

- **API クォータのエラーが出る場合**：
    - [Google Cloud Console](https://console.cloud.google.com/) で API のクォータ状況を確認し、必要に応じて制限を引き上げてください。

## ライセンス

このスクリプトは **MIT ライセンス** の下で提供されています。

## お問い合わせ

ご不明な点や問題が発生した場合は、開発者までご連絡ください。
