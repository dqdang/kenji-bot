import os
import psycopg2
import sqlalchemy as sql
from sqlalchemy import Table, Column, Integer, BigInteger, String, ForeignKey, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import joinedload, relationship, sessionmaker

Base = declarative_base()

# heroku pg:psql -a groovy3
# import dburl
url = os.environ['DATABASE_URL']
engine = sql.create_engine(url, pool_size=17, client_encoding='utf8')


class Seen(Base):
    __tablename__ = "seen"
    url = Column(String, primary_key=True)


table_dict = {
    "Seen": Seen
}


def start_sess():
    Session = sessionmaker(bind=engine, autocommit=False)
    return Session()


def create_tables():
    sess = start_sess()
    Base.metadata.create_all(engine)
    sess.commit()
    sess.close()


def entry_exists(url, sess=start_sess()):
    return sess.query(Seen).filter(Seen.url == url).scalar()


def insert_entry(url):
    sess = start_sess()

    if entry_exists(url, sess):
        change_url(url)
        sess.close()
        return False

    entry = Seen(url=url)

    sess.add(entry)
    sess.commit()
    sess.close()
    return True


""" Private getters """


def _get_object(table, sess=start_sess()):
    results = sess.query(table).all()
    return results


""" Public getters """


def get_table(table, column):
    sess = start_sess()
    results = sess.query(getattr(table_dict[table], column)).all()
    sess.close()
    return [] if len(results) == 0 else list(zip(*results))[0]


def get_url(url):
    sess = start_sess()
    entry = entry_exists(url, sess)
    if entry:
        sess.close()
        return entry
    sess.close()
    return None


def change_url(url):
    sess = start_sess()
    entry = entry_exists(url, sess)

    if entry:
        sess.commit()
        sess.close()
        return True

    sess.close()
    return False


def delete_entry(url):
    sess = start_sess()
    entry = entry_exists(url, sess)

    if entry:
        sess.delete(url)
        sess.commit()
        sess.close()
        return True

    sess.close()
    return False
