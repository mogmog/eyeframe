from sqlalchemy import create_engine, pool 
from sqlalchemy.orm import sessionmaker

from twisted_decorators import toThread

class DBDefer(object):

    def __init__(self, dsn, poolclass=pool.StaticPool):
        self.engine = create_engine(dsn, poolclass=poolclass)
    
    def __call__(self, func):

        @toThread
        def wrapper(*args, **kwargs):

            try:
                session = None
                session = sessionmaker(bind=self.engine)()
                session.expire_on_commit = False
                ex = func(session=session, *args, **kwargs)
                session.commit()
                return ex
            except :
                session.rollback()
                raise

        return wrapper
