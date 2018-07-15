
from sqlalchemy import Column, Integer, String, Table, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(256))
    device_id = Column(String(256), nullable=False, primary_key=True)
    nonfication_address = Column(String(256), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'device_id': self.device_id,
        }


engine = create_engine('sqlite:///BLE.db')
Base.metadata.create_all(engine)
