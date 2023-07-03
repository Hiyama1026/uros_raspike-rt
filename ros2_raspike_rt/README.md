# RaspberryPi側のROS2プログラム

## ファイル構成
- `rpi_ros2_node.py`：ROS2によるpub・subプログラム
    - `rasberryPiNode`と`appNode`がマルチスレッドで動作
        - 追加することも可能
- `app_node.py`：アプリケーション開発用のファイル
    - `app_timer()`内にアプリケーションを作成することを想定している
    - デフォルトでは`app_timer()`は10ms周期で呼ばれる
        - `create_timer(()`の第一引数を変更することで周期を変更できる
        - 10msより短い周期の動作確認は行っていない
    - APIはリファレンス([api_reference.md](./api_reference.md))を参照
- libフォルダ内のファイル
    - APIのライブラリ等

## 実行方法
- このフォルダを`<ROS2ワークスペース>\src`に置いてビルド・実行をする
- 下記のようにビルド
```
$ cd <ROS2ワークスペース>
$ colcon build
$ . install/setup.bash
```
- 実行は下記のコマンド
    - `$ ros2 run ros2_raspike_rt rpi_ros2_node`