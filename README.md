# pixi_g1

macOS で Unitree G1 ロボットを `pixi` 環境で開発するためのワークスペース．


> [!NOTE]
> 現在 `Mujoco` シミュレータのみ対応．実機検証はしていません．

## Setup

1. **開発環境を構築**
    ```bash
    pixi run install_unitree_sdk2_python
    ```

1. **`unitree_sdk2_python` が正常にインストールされたか確認**
    ```bash
    pixi run check_installed_unitree_sdk2_python
    ```

## Mujoco

1. **[`config.py`](config.py) を編集する**<br>
    1. `ifconfig` コマンドなどを用いて使用するネットワークインターフェース名を `INTERFACE` に代入して下さい．
    1. `DOF` 変数に使用するロボットの関節数を指定して下さい．

1. **Mujoco を起動する**
    ```bash
    pixi run bringup_mujoco
    ```

    |G1 23DOF|G1 29DOF|
    |:---:|:---:|
    |<img width=100% src="https://i.imgur.com/58cbkZO.gif"/>|<img width=100% src="https://i.imgur.com/PaybUhe.gif"/>|

## Example
1. **Mujoco を起動する**
    ```bash
    pixi run bringup_mujoco
    ```

1. **別ターミナルでサンプルコードを起動する．引数に渡すネットワークインターフェースに注意．**
    ```bash
    pixi run python examples/g1_low_level_example.py en0
    ```
    |`examples/g1_low_level_example.py` 実行時の様子|
    |:---:|
    |<img width=100& src="https://i.imgur.com/n1axLv4.gif"/>|
