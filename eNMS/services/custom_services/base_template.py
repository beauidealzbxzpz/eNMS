from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict

from eNMS.services.custom_service import CustomService, service_classes

class AService(CustomService):

    __tablename__ = 'AService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)
    vendor = Column('Vendor', String)
    operating_system = Column('Operating sytem', String)
    an_integer = Column('An integer', Integer)
    a_float = Column('A float', Float)
    a_dict = Column('A dictionnary', MutableDict.as_mutable(PickleType))

    __mapper_args__ = {
        'polymorphic_identity': 'a_service',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def job(self, *args):
        return True, 'a', 'a'

service_classes['A Service'] = AService