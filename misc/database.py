from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    BigInteger,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os
import dotenv

dotenv.load_dotenv()

Base = declarative_base()


class TgSearchAccounts(Base):
    __tablename__ = "TgSearchAccounts"

    id = Column(Integer, primary_key=True)
    email = Column(String)
    password = Column(String)

    api_id = Column(String, default="")
    api_hash = Column(String, default="")
    session_name = Column(String, default="")

    deal_hi_message = Column(String, default="Привет")
    link_to_telegram_channel = Column(String, default="")
    search_words = Column(String, default="")

    telegram_chats = relationship("TelegramChats", back_populates="owner")


class TelegramChats(Base):
    __tablename__ = "TelegramChats"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("TgSearchAccounts.id"))
    chat_id = Column(BigInteger)
    chat_name = Column(String)
    enabled = Column(Boolean)

    owner = relationship("TgSearchAccounts", back_populates="telegram_chats")


class InfoForBot(Base):
    __tablename__ = 'InfoForBot'

    id = Column(Integer, primary_key=True)
    email = Column(String, default='')
    status = Column(Boolean, default=False)
    last_iter_date = Column(String, default='')
    keywords = Column(String, default='')
    chats = Column(String, default='')




# Database setup
engine = create_engine(
    f'postgresql://{os.getenv("DB_LOGIN")}:{os.getenv("DB_PASSWORD")}'
    f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}',
    pool_pre_ping=True,
)
Base.metadata.create_all(bind=engine)

# Session setup
Session = sessionmaker(bind=engine)
session = Session()


# Methods to interact with the database


def add_search_account(
    hi_message,
    email,
    password,
):
    account = TgSearchAccounts(
        deal_hi_message=hi_message,
        email=email,
        password=password,
    )
    session.add(account)
    session.commit()
    return account


def add_telegram_chat(owner_id, chat_id, chat_name, enabled=True):
    search_account = session.query(TgSearchAccounts).filter_by(id=owner_id).first()
    if search_account:
        telegram_chat = (
            session.query(TelegramChats)
            .filter_by(chat_id=chat_id, owner_id=owner_id)
            .one_or_none()
        )
        if not telegram_chat:
            telegram_chat = TelegramChats(
                owner_id=owner_id, chat_id=chat_id, chat_name=chat_name, enabled=enabled
            )
            session.add(telegram_chat)
            session.commit()
        return telegram_chat
    else:
        return None


def edit_telegram_chat_enable_status(chat_id, new_status):
    telegram_chat = session.query(TelegramChats).filter_by(id=chat_id).first()
    if telegram_chat:
        telegram_chat.enabled = new_status
        session.commit()
        return True
    else:
        return False


def get_username_status(username: str):
    telegram_account = (
        session.query(TgSearchAccounts).filter_by(email=username).one_or_none()
    )
    return telegram_account is not None


def auth_correct(username: str, password: str) -> bool:
    telegram_account = (
        session.query(TgSearchAccounts)
        .filter_by(email=username, password=password)
        .one_or_none()
    )
    return telegram_account is not None


def get_user(username: str) -> bool:
    telegram_account = session.query(TgSearchAccounts).filter_by(email=username).first()
    return telegram_account


def get_chats_by_user(user_id: int):
    telegram_chats = (
        session.query(TelegramChats)
        .order_by(TelegramChats.enabled)
        .filter_by(owner_id=user_id)
        .all()
    )
    return telegram_chats[::-1]


def disable_chats_by_user_id(user_id: int):
    chats = get_chats_by_user(user_id)
    for chat in chats:
        chat.enabled = False
        session.add(chat)
    session.commit()


def enable_chat(chat_id: int, user_id):
    chat = (
        session.query(TelegramChats)
        .filter_by(chat_id=chat_id, owner_id=user_id)
        .first()
    )
    chat.enabled = True
    session.add(chat)
    session.commit()


def update_search_info(keywords, hi_message, account_to_post, user_id: int):
    telegram_account = session.query(TgSearchAccounts).filter_by(id=user_id).first()
    telegram_account.deal_hi_message = hi_message.strip()
    telegram_account.link_to_telegram_channel = account_to_post.strip()
    telegram_account.search_words = keywords.strip()
    session.add(telegram_account)
    session.commit()


def get_search_info(user_id: int):
    telegram_account = session.query(TgSearchAccounts).filter_by(id=user_id).first()
    return telegram_account


def get_all_accounts():
    session.commit()
    return session.query(TgSearchAccounts).all()


def get_all_enabled_chats_by_user_id(user_id: int):
    return session.query(TelegramChats).filter_by(owner_id=user_id, enabled=True).all()


def save_telegram(api_id: str, api_hash: str, session_name: str, user_id: int):
    telegram_account = session.query(TgSearchAccounts).filter_by(id=user_id).first()
    telegram_account.api_id = api_id
    telegram_account.api_hash = api_hash
    telegram_account.session_name = session_name
    session.add(telegram_account)
    session.commit()


def check_same_tg_number(session_name: str):
    result = session.query(TgSearchAccounts).filter_by(session_name=session_name).one()

    if result:
        return True
    else:
        return False



def add_info_for_bot(
        email,
        status,
        last_iter_date,
        keywords,
        chats
):
    info = InfoForBot(
        email=email,
        status=status,
        last_iter_date=last_iter_date,
        keywords=keywords,
        chats=chats
    )
    session.add(info)
    session.commit()
    return info

def delete_current_account_from_info(email):
    account_to_delite = session.query(InfoForBot).filter_by(email=email).first()

    if account_to_delite:
        session.delete(account_to_delite)
        session.commit()

def update_current_account_from_info(
        email,
        new_status,
        new_last_iter_date,
        new_keywords,
        new_chats
):
    account_to_update = session.query(InfoForBot).filter_by(email=email).first()

    if account_to_update:
        account_to_update.status = new_status
        account_to_update.last_iter_date = new_last_iter_date
        account_to_update.keywords = new_keywords
        account_to_update.chats = new_chats
        session.commit()



def clear_info_for_bot_table():
    session.query(InfoForBot).delete()
    session.commit()


def add_or_update_info_for_bot(email, status, last_iter_date, keywords, chats):
    # Пытаемся найти аккаунт по email
    account_to_update = session.query(InfoForBot).filter_by(email=email).first()

    if account_to_update:
        account_to_update.status = status
        account_to_update.last_iter_date = last_iter_date
        account_to_update.keywords = keywords
        account_to_update.chats = chats
        session.commit()
    else:
        info = InfoForBot(
            email=email,
            status=status,
            last_iter_date=last_iter_date,
            keywords=keywords,
            chats=chats
        )
        session.add(info)
        session.commit()

