import json
from http.cookies import SimpleCookie


def save_cookies():
    cookies_raw = input('Cookies: ')

    cookies_obj = SimpleCookie()
    cookies_obj.load(cookies_raw)
    cookies = {k: v.value for k, v in cookies_obj.items()}

    with open('cookies.json', 'w', encoding='utf-8') as f:
        json.dump(cookies, f)


if __name__ == '__main__':
    save_cookies()
