"""Cookie処理ユーティリティ."""

from urllib.parse import unquote


def parse_cookie_header(cookie_header: str) -> dict[str, str]:
    """HTTPヘッダーのCookie文字列を辞書に変換.

    Args:
        cookie_header: Cookie HTTPヘッダーの値（例: "name1=value1; name2=value2"）

    Returns:
        Cookie名をキー、値をバリューとする辞書

    Examples:
        >>> parse_cookie_header("session=abc123; user=john")
        {'session': 'abc123', 'user': 'john'}
        >>> parse_cookie_header("")
        {}
    """
    cookies: dict[str, str] = {}
    if not cookie_header:
        return cookies

    for part in cookie_header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies[unquote(name)] = unquote(value)

    return cookies
