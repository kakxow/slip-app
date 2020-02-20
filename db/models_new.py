from typing import Dict

from sqlalchemy import Column, Integer, String, Date, Time, Float

from .db import Base


class Slip(Base):
    __tablename__ = 'slips'
    # __bind_key__ = 'slips'

    merchant_name = Column('merchant_name', String)
    city = Column('city', String)
    address = Column('address', String)
    phone_num = Column('phone_num', String)
    date = Column('date', Date, index=True)
    time = Column('time', Time)

    operation_type = Column('operation_type', String)
    pos_id = Column('pos_id', String, index=True)
    merchant_num = Column('merchant_num', String, index=True)
    fin_service = Column('fin_service', String)
    something = Column('something', String)
    card_number = Column('card_number', String, index=True)
    card_holder = Column('card_holder', String)
    summ = Column('summ', Float, index=True)
    result = Column('result', String)
    auth_code = Column('auth_code', String, index=True)
    ref_num = Column('ref_num', Integer, index=True)
    payment_type = Column('payment_type', String)
    file_link = Column('file_link', String, index=True, unique=True, primary_key=True)

    updated = Column('updated', Date)
    object_code = Column('object_code', String, index=True)

    def to_dict(self) -> Dict[str, str]:
        """
        Returns dict with column names and values.
        """
        attr_dict = {c.key: getattr(self, c.key) for c in self.__table__.columns}
        return attr_dict

    def to_json(self) -> Dict[str, str]:
        """
        Returns dict with column names and stringified column values.
        """
        attr_dict = {c.key: str(getattr(self, c.key)) for c in self.__table__.columns}
        attr_dict = {
            **attr_dict,
            'ref_num': f'{int(self.ref_num):012d}',
            'time': self.time.strftime('%H:%M')
        }
        return attr_dict
