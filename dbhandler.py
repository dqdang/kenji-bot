import os
import psycopg2
import sqlalchemy as sql
from sqlalchemy import Table, Column, Integer, BigInteger, String, ForeignKey, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import joinedload, relationship, sessionmaker

Base = declarative_base()

# heroku pg:psql -a groovy3
# import dburl
url = os.environ['DATABASE']
engine = sql.create_engine(url, pool_size=17, client_encoding='utf8')


class Seen(Base):
    __tablename__ = "seen"
    id = Column(Integer, primary_key=True)
    url = Column(String)


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


def url_exists(url, sess=start_sess()):
    return sess.query(Seen).filter(Seen.url == url).scalar()

def id_exists(id, sess=start_sess()):
    return sess.query(Seen).filter(Seen.id == id).scalar()

def insert_url(value, url):
    sess = start_sess()
    id = id_exists(value, sess)
    if id:
        id.url = url
        sess.commit()
        sess.close()
        return True
    sess.close()
    return False


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


def get_url(id):
    sess = start_sess()
    url = url_exists(id, sess)
    if url:
        rv = url.url
        sess.close()
        return rv
    sess.close()
    return None


def change_url(id, url, sess=start_sess()):
    id = id_exists(id)

    if id:
        id.url = url
        sess.commit()
        sess.close()
        return True

    sess.close()
    return False


def delete_url(id):
    sess = start_sess()
    url = url_exists(id, sess)

    if url:
        sess.delete(url)
        sess.commit()
        sess.close()
        return True

    sess.close()
    return False
