import subprocess
import sys
import os

def test_run_main_no_errors():
    """
    main.pyを短時間実行し、標準エラーに出力がないことを確認するテスト。
    """
    # main.pyへのパスを取得
    main_py_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')

    # 環境変数を設定して、ヘッドレス環境でQtを実行できるようにする
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'

    try:
        result = subprocess.run(
            [sys.executable, main_py_path],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,  # タイムアウト時に例外を発生させない
            env=env
        )
    except subprocess.TimeoutExpired as e:
        # タイムアウトは正常な動作（GUIが起動し、ユーザー入力を待っている状態）
        # なので、エラー出力がないかだけ確認する
        stderr_output = e.stderr.decode('utf-8', errors='ignore') if e.stderr else ""
        # Qtが生成する可能性のある無害なメッセージを除外
        filtered_stderr = [
            line for line in stderr_output.splitlines()
            if "QApplication" not in line and "qt." not in line.lower() and "This plugin does not support" not in line
        ]
        assert not filtered_stderr, f"main.py実行中に予期せぬエラーが発生しました (Timeout):\n{''.join(filtered_stderr)}"
        return

    # タイムアウトしなかった場合でも、標準エラーをチェック
    # Qtが生成する可能性のある無害なメッセージを除外
    filtered_stderr = [
        line for line in result.stderr.splitlines()
        if "QApplication" not in line and "qt." not in line.lower() and "This plugin does not support" not in line
    ]
    assert not filtered_stderr, f"main.py実行中にエラーが発生しました:\n{''.join(filtered_stderr)}"