# OpenDuck

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
operatorプロセス(別repo)
```

COME_HEREとSTOPは、ロボットを直接操作せず、`std_msgs/String`のJSONとして別プロセスへ送信します。

```json
{"command": "come_here", "target": "speaker"}
```

```json
{"command": "stop"}
```

operatorプロセスの標準出力は、main.pyによって`[operation]`接頭辞付きで表示されます。

```text
[operation] Subscribed to /openduck/operation/actions
```

## ROS topic

| 用途 | Topic | Message Type |
|---|---|---|
| 文字起こし入力 | `/openduck/speech/transcription` | `std_msgs/String` |
| COME_HERE / STOP命令 | `/openduck/operation/actions` | `std_msgs/String` |

マイク音声の`/openduck/audio/raw`購読モジュールもありますが、文字起こし処理自体は外部プロセスが担当し、結果を`/openduck/speech/transcription`へ送信します。