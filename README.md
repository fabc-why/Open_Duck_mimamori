# OpenDuck

## 概要

OpenDuckは、次のような情報を処理し、必要に応じて別プロセスへ指示を送る司令塔です。

- 文字起こしされたマイク入力
- 時間やスケジュールに関する情報
- その他のセンサー情報s

現時点では、OpenDuckのカメラ画像から解析された情報は受信していません。
将来的には対応しようかなとも思ってます。

## 起動

ROS bridgeが`localhost:9090`で起動している状態で、リポジトリルートから実行します。

```bash
src/main.py
```

hostとportは変更できます。

```bash
src/main.py \
  --host localhost \
  --port 9090
```

`main.py`を起動すると、OpenDuckの中核処理が起動します。

- EventRouter
- `/openduck/speech/transcription`の購読
- SpeechUnderstandingHandler
- FeatureごとのIntent登録
- COME_HERE / STOPのROS topic publisher
- 外部operatorプロセス

## 音声から動作まで

```text
/openduck/speech/transcription
  ↓
TranscriptionSubscriber
  ↓ speech.utterance.recognized
EventRouter
  ↓
UnderstandingHandler
  ↓ dialogue.intent.recognized
Feature Handler
  ↓
/openduck/operation/actions
  ↓
operatorプロセス
```

COME_HEREとSTOPは、ロボットを直接操作せず、`std_msgs/String`のJSONとして別プロセスへ送信します。

```json
{"command": "come_here", "target": "speaker"}
```

```json
{"command": "stop"}
```

## operatorプロセス

operatorプロセスは、OpenDuckの行動に関する処理を担当します。

実装は[Open_Duck_mimamori_Operator](https://github.com/fabc-why/Open_Duck_mimamori_Operator)で管理しています。

`main.py`を起動するとoperatorプロセスも自動的に起動します。
operatorの標準出力には`[operation]`という接頭辞が付きます。

```text
[operation] Subscribed to /openduck/operation/actions
```

## ROS topic

| 用途 | Topic | Message Type |
|---|---|---|
| 文字起こし入力 | `/openduck/speech/transcription` | `std_msgs/String` |
| COME_HERE / STOP命令 | `/openduck/operation/actions` | `std_msgs/String` |

マイク音声の`/openduck/audio/raw`購読モジュールもありますが、文字起こし処理自体は外部プロセスが担当し、結果を`/openduck/speech/transcription`へ送信します。