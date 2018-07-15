from sqlalchemy import create_engine
from monster_db import Base, User
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///BLE.db')

Base.metadata.bind = engine

Session = sessionmaker(bind=engine)
session = Session()

session.bulk_save_objects(
    [
        User(
            id=1,
            name="まなぶさん",
            device_id="00000000-0000-0000-0000-000000000000",
            nonfication_address="*@gmail.com"
        ),
        User(
            id=2,
            name="かなこさん",
            device_id="8ec76ea3-6668-48da-9866-75be8bc86f4d",
            nonfication_address="*@gmail.com"
        ),
        User(
            id=3,
            name="りんたろうさん",
            device_id="f7826da6-4fa2-4e98-8024-bc5b71e0893e",
            nonfication_address="*@gmail.com"
        ),
    ]
)

session.commit()


