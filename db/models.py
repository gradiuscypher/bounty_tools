#!/usr/bin/env python

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref
from db.database import Base


class Host(Base):
    __tablename__ = 'host'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    host = Column(String)
    source = Column(String)
    workspace = Column(String)


class Shodan(Base):
    __tablename__ = 'shodan'
    id = Column(Integer, primary_key=True)
    host = relationship(Host, backref=backref("shodan", uselist=True, cascade="delete,all"))
    host_id = Column(Integer, ForeignKey('host.id'))


class Port(Base):
    __tablename__ = 'port'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    host = relationship(Host, backref=backref("port", uselist=True, cascade="delete,all"))
    host_id = Column(Integer, ForeignKey('host.id'))
