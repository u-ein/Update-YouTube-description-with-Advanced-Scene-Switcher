<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>update_description.py - README</title>
</head>
<body>
    <h1>update_description.py</h1>
    <p><strong>バージョン:</strong> 1.0</p>

    <h2>概要</h2>
    <p>
        このスクリプトは、<strong>YouTube ライブ配信の概要欄を自動更新</strong>するためのものです。<br>
        OBS Studio の配信経過時間とシーン名を取得し、それを YouTube のライブ配信の概要欄に追記します。
    </p>

    <h2>主な機能</h2>
    <ul>
        <li>OBS Studio から配信経過時間（タイムコード）を取得</li>
        <li>シーン名を取得し、概要欄に追加</li>
        <li>限定公開のライブ配信にも対応</li>
        <li>詳細なログ出力とエラーハンドリング</li>
    </ul>

    <h2>必要な環境・前提条件</h2>
    <ul>
        <li>Python 3.6 以上</li>
        <li>OBS Studio（OBS WebSocket 5.x プラグインがインストールされていること）</li>
        <li>YouTube Data API の認証情報（OAuth 2.0 クライアント ID とシークレット）</li>
        <li>必要な Python ライブラリがインストールされていること</li>
    </ul>

    <h2>依存ライブラリのインストール</h2>
    <p>以下のコマンドを実行して必要なライブラリをインストールしてください。</p>
    <pre><code>pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client websockets</code></pre>

    <h2>セットアップ手順</h2>
    <ol>
        <li>
            <strong>YouTube Data API の認証情報を取得</strong><br>
            <a href="https://console.cloud.google.com/apis/credentials">Google Cloud Console</a> にアクセスし、新しい OAuth 2.0 クライアント ID を作成します。<br>
            取得した <code>client_secret.json</code> をスクリプトと同じディレクトリに配置します。
        </li>
        <li>
            <strong>OBS WebSocket の設定</strong><br>
            OBS Studio に OBS WebSocket 5.x プラグインをインストールします。<br>
            OBS の設定で WebSocket サーバーを有効にし、ポート番号とパスワードを設定します。
        </li>
        <li>
            <strong>設定ファイル <code>user_settings.json</code> の作成</strong><br>
            スクリプトと同じディレクトリに以下の内容で <code>user_settings.json</code> ファイルを作成します。
            <pre><code>{
    "channel_id": "YOUR_CHANNEL_ID",
    "token_path": "token.json",
    "client_secret_path": "client_secret.json",
    "obs_websocket_url": "ws://localhost:4455",
    "obs_websocket_password": "YOUR_WEBSOCKET_PASSWORD",
    "manual_video_id": "YOUR_MANUAL_VIDEO_ID"
}</code></pre>
            <ul>
                <li><code>channel_id</code>: YouTube のチャンネル ID を指定します。</li>
                <li><code>token_path</code>: 認証トークンを保存するファイルのパス（デフォルトで <code>token.json</code>）</li>
                <li><code>client_secret_path</code>: 取得した <code>client_secret.json</code> のパス</li>
                <li><code>obs_websocket_url</code>: OBS WebSocket の接続先 URL（例: <code>ws://localhost:4455</code>）</li>
                <li><code>obs_websocket_password</code>: OBS WebSocket のパスワード</li>
                <li><code>manual_video_id</code>: ライブ配信のビデオ ID を手動で指定する場合に入力</li>
            </ul>
        </li>
        <li>
            <strong>初回実行と認証</strong><br>
            スクリプトを初めて実行する際、ブラウザが自動的に開き、Google アカウントでの認証を求められます。<br>
            指示に従って認証を完了してください。認証が成功すると、<code>token.json</code> ファイルが生成されます。
        </li>
    </ol>

    <h2>使い方</h2>
    <p>以下のコマンドを実行します。</p>
    <pre><code>python update_description.py &lt;source_file&gt;</code></pre>
    <p>
        <strong>引数：</strong><br>
        <code>&lt;source_file&gt;</code>: Advanced Scene Switcher から渡されるシーンのファイルパスを指定します。
    </p>

    <h2>動作の仕組み</h2>
    <ol>
        <li>スクリプトが OBS WebSocket に接続し、配信の経過時間（タイムコード）を取得します。</li>
        <li>指定された <code>source_file</code> からシーン名を取得します。</li>
        <li>YouTube Data API を使用して、現在のライブ配信のビデオ ID を取得します。</li>
        <li>取得したタイムコードとシーン名を組み合わせて、新しい概要欄のテキストを作成します。</li>
        <li>YouTube のライブ配信の概要欄を更新します。</li>
    </ol>

    <h2>ログファイル</h2>
    <p>
        スクリプトの実行結果やエラーは、<code>error_log.txt</code> ファイルに記録されます。<br>
        ログファイルは最大 10MB まで保存され、古いログは自動的に削除されます。
    </p>

    <h2>注意事項</h2>
    <ul>
        <li>スクリプトは YouTube Data API を使用しているため、API のクォータに注意してください。</li>
        <li>OBS WebSocket のバージョンは 5.x 以上が必要です。</li>
        <li>必要な権限を持つ Google アカウントで認証してください。</li>
        <li>認証情報やトークンファイルは第三者に共有しないでください。</li>
    </ul>

    <h2>トラブルシューティング</h2>
    <ul>
        <li>
            <strong>トークンエラーが発生する場合：</strong><br>
            <code>token.json</code> ファイルを削除し、再度スクリプトを実行して認証をやり直してください。
        </li>
        <li>
            <strong>OBS WebSocket に接続できない場合：</strong><br>
            OBS が起動しているか、WebSocket の設定が正しいか確認してください。
        </li>
        <li>
            <strong>ライブ配信のビデオ ID が取得できない場合：</strong><br>
            <code>manual_video_id</code> にビデオ ID を手動で設定してみてください。
        </li>
        <li>
            <strong>API クォータのエラーが出る場合：</strong><br>
            Google Cloud Console で API のクォータ状況を確認し、必要に応じて制限を引き上げてください。
        </li>
    </ul>

    <h2>ライセンス</h2>
    <p>このスクリプトは <strong>MIT ライセンス</strong> の下で提供されています。</p>

    <h2>お問い合わせ</h2>
    <p>ご不明な点や問題が発生した場合は、開発者までご連絡ください。</p>
</body>
</html>
