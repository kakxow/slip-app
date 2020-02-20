from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.orm as orm

import config


Base = declarative_base()

db_address = config.slip_db
engine = create_engine(db_address)
Session = orm.sessionmaker(bind=engine)
from .utils import SessionContextManager
SessionCM = SessionContextManager(Session)
