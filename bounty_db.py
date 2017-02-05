#!/usr/bin/env python

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Host(Base):
    __tablename__ = 'host'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    host = Column(String)
    source = Column(String)

engine = create_engine("sqlite:///recon.db")
Base.metadata.create_all(engine)
