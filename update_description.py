#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
update_description.py

YouTubeライブ配信の概要欄を更新するスクリプト。

機能：
- OBSの配信経過時間とシーン名を取得し、YouTubeライブ配信の概要欄に追記。
- 限定公開のライブ配信にも対応。
- 詳細なログとエラーハンドリング。

使い方：
python update_description.py <source_file>

引数：
- source_file: Advanced Scene Switcherから渡されるシーンのファイルパス。
"""

import sys
import os
import asyncio
import json
import base64
import hashlib
import logging
from typing import Optional

import websockets
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from logging.handlers import RotatingFileHandler

# ログ設定
LOG_FILE = 'error_log.txt'
LOG_LEVEL = logging.INFO
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# ルートロガーを使用
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# ハンドラを作成
handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT
)
handler.setLevel(LOG_LEVEL)

# フォーマッタを作成
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# ハンドラにフォーマッタを設定
handler.setFormatter(formatter)

# ルートロガーにハンドラを追加
logger.addHandler(handler)

# YouTube Data APIのスコープ
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.readonly'
]

# 設定ファイルのパス
SETTINGS_FILE = "user_settings.json"

def load_settings() -> dict:
    """
    設定ファイルから設定を読み込む。

    Returns:
        dict: 設定情報の辞書。

    Raises:
        SystemExit: 必須設定が欠けている場合にスクリプトを終了。
    """
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
            # 必須項目の検証
            required_keys = [
                "channel_id",
                "token_path",
                "client_secret_path",
                "obs_websocket_url",
                "obs_websocket_password",
                "manual_video_id"
            ]
            for key in required_keys:
                if key not in settings or not settings[key]:
                    logger.error(f"Missing required setting: {key}")
                    sys.exit(1)
            return settings
    except FileNotFoundError:
        logger.critical(f"Settings file '{SETTINGS_FILE}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.critical(f"Error parsing settings file: {e}")
        sys.exit(1)

# 設定を読み込む
USER_SETTINGS = load_settings()

# OBS WebSocketのパスワードを取得
OBS_WEBSOCKET_PASSWORD = USER_SETTINGS.get("obs_websocket_password")

def get_authenticated_service() -> Optional[build]:
    """
    YouTube APIに認証するためのサービスを取得。

    Returns:
        build: 認証されたYouTube APIサービスオブジェクト。
    """
    creds = None
    try:
        if os.path.exists(USER_SETTINGS["token_path"]):
            creds = Credentials.from_authorized_user_file(USER_SETTINGS["token_path"], SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    USER_SETTINGS["client_secret_path"], SCOPES)
                creds = flow.run_local_server(port=0)
            with open(USER_SETTINGS["token_path"], 'w', encoding='utf-8') as token:
                token.write(creds.to_json())
    except RefreshError as e:
        logger.error(f"Token refresh error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return None
    return build('youtube', 'v3', credentials=creds)

def get_live_broadcast_id(youtube) -> Optional[str]:
    """
    現在のライブ配信（限定公開を含む）のビデオIDを取得。

    Args:
        youtube (build): 認証されたYouTube APIサービスオブジェクト。

    Returns:
        Optional[str]: ライブ配信のビデオID。見つからない場合はNone。
    """
    try:
        request = youtube.liveBroadcasts().list(
            part="id",
            broadcastStatus="active",
            broadcastType="all"
        )
        response = request.execute()
        if 'items' in response and len(response['items']) > 0:
            video_id = response['items'][0]['id']
            logger.info(f"Live broadcast found: {video_id}")
            return video_id
        else:
            logger.warning("No active live broadcast found.")
            return None
    except Exception as e:
        logger.error(f"Error fetching live broadcast ID: {e}")
        return None

def update_video_description(youtube, video_id: str, new_description: str) -> None:
    """
    指定されたビデオIDの概要欄を更新。

    Args:
        youtube (build): 認証されたYouTube APIサービスオブジェクト。
        video_id (str): ビデオID。
        new_description (str): 追加する概要欄の内容。
    """
    try:
        video_request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        video_response = video_request.execute()
        if 'items' in video_response and len(video_response['items']) > 0:
            snippet = video_response['items'][0]['snippet']
            updated_description = f"{snippet['description']}\n{new_description}"
            # ログに概要欄の内容を出力
            logger.info(f"Updating video description for video ID {video_id}.\nNew description:\n{updated_description}")
            update_request = youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": {
                        "title": snippet['title'],
                        "description": updated_description,
                        "categoryId": snippet.get('categoryId', '22')  # デフォルトで '22'（People & Blogs）
                    }
                }
            )
            update_response = update_request.execute()
            logger.info(f"Successfully updated video description for video ID {video_id}.")
        else:
            logger.error(f"Could not retrieve video details for video ID {video_id}.")
    except Exception as e:
        logger.error(f"Error updating video description for video ID {video_id}: {e}")

async def get_obs_stream_timecode() -> Optional[str]:
    """
    OBSから配信経過時間（タイムコード）を取得（OBS WebSocket 5.x対応）。

    Returns:
        Optional[str]: 配信経過時間の文字列。取得できない場合はNone。
    """
    try:
        uri = USER_SETTINGS["obs_websocket_url"]
        async with websockets.connect(uri) as websocket:
            # サーバーからの初回メッセージ（Hello メッセージ）を受信
            hello_message = await websocket.recv()
            hello_data = json.loads(hello_message)
            if 'd' not in hello_data or 'authentication' not in hello_data['d']:
                logger.error("Invalid hello message from OBS.")
                return None

            # 認証が必要か確認
            auth_required = 'challenge' in hello_data['d']['authentication']

            if auth_required:
                if OBS_WEBSOCKET_PASSWORD:
                    # 認証情報を取得
                    challenge = hello_data['d']['authentication']['challenge']
                    salt = hello_data['d']['authentication']['salt']

                    # 認証レスポンスを計算
                    def sha256_hash(s: str) -> bytes:
                        return hashlib.sha256(s.encode('utf-8')).digest()

                    secret = base64.b64encode(sha256_hash(OBS_WEBSOCKET_PASSWORD + salt)).decode('utf-8')
                    auth_response = base64.b64encode(sha256_hash(secret + challenge)).decode('utf-8')

                    # 認証リクエストを送信
                    auth_payload = json.dumps({
                        "op": 1,
                        "d": {
                            "rpcVersion": 1,
                            "authentication": auth_response
                        }
                    })
                    await websocket.send(auth_payload)
                    auth_result_message = await websocket.recv()
                    auth_result = json.loads(auth_result_message)
                    if auth_result.get('op') == 5:
                        logger.error("Authentication failed.")
                        return None
                else:
                    logger.error("OBS WebSocket requires authentication, but no password was provided.")
                    return None
            else:
                # 認証不要の場合、Identify リクエストを送信
                identify_payload = json.dumps({
                    "op": 1,
                    "d": {
                        "rpcVersion": 1
                    }
                })
                await websocket.send(identify_payload)
                identify_result_message = await websocket.recv()
                identify_result = json.loads(identify_result_message)
                if identify_result.get('op') == 5:
                    logger.error("Identification failed.")
                    return None

            # GetStreamStatus リクエストを送信
            request_id = "1"
            get_stream_status_payload = json.dumps({
                "op": 6,
                "d": {
                    "requestType": "GetStreamStatus",
                    "requestId": request_id
                }
            })
            await websocket.send(get_stream_status_payload)

            # レスポンスを待機
            while True:
                response_message = await websocket.recv()
                response_data = json.loads(response_message)

                if response_data.get('op') == 7 and response_data['d']['requestId'] == request_id:
                    if response_data['d']['requestStatus']['result']:
                        stream_status = response_data['d']['responseData']
                        if stream_status.get('outputActive'):
                            timecode = stream_status.get('outputTimecode')
                            return timecode.split(".")[0]  # ミリ秒部分を除去
                        else:
                            logger.warning("Stream is not active.")
                            return None
                    else:
                        logger.error("Failed to get stream status.")
                        return None
    except Exception as e:
        logger.exception("Failed to get stream timecode from OBS")
        return None

def sanitize_filename(filename: str) -> str:
    """
    ファイル名から不要な文字を除去。

    Args:
        filename (str): 元のファイル名。

    Returns:
        str: サニタイズされたファイル名。
    """
    return os.path.basename(filename).replace("@", "").replace(".png", "")

async def main() -> None:
    """
    メイン処理。
    """
    if len(sys.argv) < 2:
        print("Usage: python update_description.py <source_file>")
        sys.exit(1)

    source_file = sys.argv[1]

    # OBSの配信経過時間を取得
    elapsed_time = await get_obs_stream_timecode()
    if not elapsed_time:
        print("Failed to get stream timecode. Exiting.")
        sys.exit(1)

    # ファイル名をサニタイズ
    file_name = sanitize_filename(source_file)

    # 追加する概要欄の内容
    new_description = f"{elapsed_time} {file_name}"

    # YouTube APIを使用して概要欄を更新
    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to authenticate YouTube API.")
        sys.exit(1)

    # ライブビデオIDを取得
    video_id = get_live_broadcast_id(youtube)
    if not video_id:
        logger.warning("Failed to get live broadcast ID, using manual video ID if available.")
        if USER_SETTINGS.get("manual_video_id"):
            video_id = USER_SETTINGS["manual_video_id"]
            logger.info(f"Using manual video ID: {video_id}")
        else:
            logger.error("No live broadcast ID found and no manual video ID provided.")
            print("No video ID found or provided, cannot update description.")
            sys.exit(1)

    # ビデオの説明を更新
    update_video_description(youtube, video_id, new_description)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        sys.exit(1)
