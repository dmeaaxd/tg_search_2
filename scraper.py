import os
import time
from datetime import datetime

from telethon.sync import TelegramClient
from telethon.tl.patched import Message
from misc import database


messages_history = {}


def create_telegram_client(session_name, api_id, api_hash):
    client = TelegramClient(session_name, int(api_id), api_hash)
    client.start()
    return client


def main():
    database.clear_info_for_bot_table()
    while True:
        start = time.time()
        accounts = database.get_all_accounts()
        for id, account in enumerate(accounts):
            # print(id + 1, '/', len(accounts), ':', account.session_name + ".session")
            print(f"\n{id + 1}/{len(accounts)} : {account.session_name}.session")
            if not os.path.exists(account.session_name + ".session"):
                continue

            if account.session_name not in messages_history.keys():
                messages_history[account.session_name] = {}

            telegram_client = create_telegram_client(
                account.session_name, account.api_id, account.api_hash
            )

            keywords = account.search_words.split(",")
            search_groups = database.get_all_enabled_chats_by_user_id(account.id)
            chat_names = ', '.join(search_group.chat_name for search_group in search_groups)
            for search_group in search_groups:
                search_title = search_group.chat_name
                group_id = account.link_to_telegram_channel

                def find_keywords(mess):
                    founded_keywords = [
                        keyword
                        for keyword in keywords
                        if keyword.lower().strip() in mess.text.lower().strip()
                    ]
                    return founded_keywords

                chats = telegram_client.get_dialogs()
                for chat in chats:
                    try:
                        if chat.title == search_title:
                            s = time.time()
                            messages = telegram_client.get_messages(
                                entity=chat, limit=100
                            )
                            # print('Get messages time:', time.time() - s)
                            for message in messages:
                                message: Message = message
                                if (chat.title in messages_history[account.session_name].keys() and
                                        messages_history[account.session_name][chat.title] >= message.id):
                                    continue

                                if chat.title in messages_history[account.session_name]:
                                    print(
                                        f'{chat.title}    -    {messages_history[account.session_name][chat.title]} < {message.id}')

                                messages_history[account.session_name][chat.title] = message.id

                                if message:
                                    # if not isinstance(message, Message):
                                    #     continue
                                    try:
                                        found_keywords = find_keywords(message)
                                        if found_keywords:
                                            print("Найдено сообщение!")
                                            keyword_str = ", ".join(found_keywords)
                                            message_text = f"{message.text}\n\n"


                                            time.sleep(1)
                                            telegram_client.send_message(
                                                int(group_id),
                                                message_text,
                                                parse_mode="HTML",
                                            )

                                    except Exception as e:
                                        print(f"Error processing {chat.title}: {e}")

                    except:
                        print("messages get error")

            telegram_client.disconnect()
        print('Execution time:', time.time() - start)


if __name__ == "__main__":
    main()
