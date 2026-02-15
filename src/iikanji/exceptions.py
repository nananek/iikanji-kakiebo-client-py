"""いいかんじ家計簿 API 例外クラス"""


class KakeiboAPIError(Exception):
    """APIがエラーレスポンスを返した場合の例外"""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"[{status_code}] {message}")


class AuthenticationError(KakeiboAPIError):
    """認証エラー (401)"""

    def __init__(self, message: str = "無効な API キーです。") -> None:
        super().__init__(401, message)
