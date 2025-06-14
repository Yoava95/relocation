import os
from bot_notify import send_document


def main():
    if os.path.exists('pytest.log'):
        try:
            send_document('pytest.log', caption='Test logs')
        except Exception as exc:
            print('WARN: failed to send test log →', exc)
    if os.path.exists('bot.log'):
        try:
            send_document('bot.log', caption='Bot logs')
        except Exception as exc:
            print('WARN: failed to send bot log →', exc)


if __name__ == '__main__':
    main()
