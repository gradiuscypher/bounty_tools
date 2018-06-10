import traceback
from sqlalchemy import Column, Boolean, Integer, String, ForeignKey, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///bountytools.db')
Base.metadata.bind = engine
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
session = Session()


class BountyToolManager:
    def build_db(self):
        Base.metadata.create_all(engine)


class BountyToolClient:
    __tablename__ = 'bountytoolclients'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    port = Column(Integer)
    service = Column(String)

    def __repr__(self):
        return '<BountyToolClient(id={}, ip_address={}, port={}, service={})>'.format(
            self.id, self.ip_address, self.port, self.service
        )
