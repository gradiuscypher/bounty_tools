#!/usr/bin/env python

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref
from database.database import Base


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
    http_data = Column(String)
    data_org = Column(String)
    data_isp = Column(String)


class Port(Base):
    __tablename__ = 'ports'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    host = relationship(Host, backref=backref("ports", uselist=True, cascade="delete,all"))
    host_id = Column(Integer, ForeignKey('host.id'))


class Althosts(Base):
    __tablename__ = 'althosts'
    id = Column(Integer, primary_key=True)
    host = relationship(Host, backref=backref("althosts", uselist=True, cascade="delete,all"))
    host_id = Column(Integer, ForeignKey('host.id'))
    hostname = Column(String)
    source = Column(String)
