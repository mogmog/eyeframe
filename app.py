import json
import sqlalchemy as sa
import uuid
import string
import time
import calendar, datetime
import binascii
import six
import urllib2
from sqlalchemy import create_engine, pool, Date, cast, func, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Boolean, String, Integer,  DateTime, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship, backref, mapper
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import desc
from sqlalchemy.orm import aliased
from sqlalchemy_utils import JSONType
from sqlalchemy.sql import select, column
from sa_decorators import DBDefer
from twisted import protocols
from twisted.web import xmlrpc, server
from twisted.internet import reactor, threads, defer
from twisted.internet.defer import Deferred
from twisted.internet.task import deferLater
from twisted.internet.defer import succeed
from twisted.application.internet import TCPServer
from twisted.application.service import Application
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.template import Element, XMLString, renderer
from twisted.protocols import basic
from twisted.internet import threads, protocol, reactor
from twisted.application import service, internet
from twisted_decorators import toThread
from collections import OrderedDict
from txrestapi.resource import APIResource
import datetime
import calendar
from email import utils

Base = declarative_base()

#dbdefer = DBDefer('postgresql://admin6uz9lhs:FCekF2K1Jddj@127.8.125.2:5432/eyeframe')
dbdefer = DBDefer('postgresql://admin6uz9lhs:FCekF2K1JddJ@$OPENSHIFT_POSTGRESQL_DB_HOST:$OPENSHIFT_POSTGRESQL_DB_PORT/eyeframe')

metadata = sa.MetaData(dbdefer.engine)

class MyEncoder(json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, datetime.date):
         return  obj.isoformat()
        if isinstance(obj, datetime.datetime):
         return  obj.isoformat()

        return json.JSONEncoder.default(self, obj)
#test
class Track(Base):
    __tablename__   = 'Track'
    __table_args__      = {};
    id                  = Column(String, primary_key=True)

    def __init__(self, fromJson = None):
          if fromJson:
              self.id        = fromJson["id"]

    def serialise(self):
      return { 'id'  : str(self.id) }

class CyanResource(Resource):

    def build(self, result, request):
        request.setHeader('Content-Length', len(result))
        request.setHeader('Content-Type', 'application/json; charset=utf-8')
        return result

    def print_success_multiple(self, result, request):
        responseBody = self.build(json.dumps([i.serialise() for i in result],  cls = MyEncoder).encode('utf-8'), request);
        request.write(responseBody)
        request.finish()

    def print_success_delete(self, result, request):
        request.setResponseCode(204)
        request.finish()

    def print_success_single(self, result, request):
        if result == None :
         request.setResponseCode(404)
         request.finish()
        else :
         responseBody = self.build(json.dumps(result.serialise(),  cls = MyEncoder).encode('utf-8'), request);
         request.write(responseBody)
         request.finish()

    def print_failure(self,  err, request):
        print err
        request.setResponseCode(500)
        request.finish()

class TrackResource(CyanResource):

    def _GET_list(self, request):

        @dbdefer
        def getTracks(session=None):
         Tracks = session.query(Track)
         print Tracks
         print Tracks.all()
         return Tracks.all()
        print "abotu to get Tracks"
        deferred =getTracks()
        deferred.addCallback(self.print_success_multiple, request)
        deferred.addErrback(self.print_failure, request)
        return server.NOT_DONE_YET

    def _GET_single(self, request, id):
        @dbdefer
        def getTrack(session=None): return session.query(Track).filter(Track.id == id).first()
        deferred = getTrack()
        deferred.addCallback(self.print_success_single, request)
        deferred.addErrback(self.print_failure, request)
        return server.NOT_DONE_YET

    def _POST_create(self, request):

        @dbdefer
        def createTrack(Track, session=None):
         session.add(Track)
         return Track

        fromJSON               = json.loads(request.content.read())
        fromJSON["id"]         = str(uuid.uuid4())

        deferred = createTrack(Track(fromJSON))
        deferred.addCallback(self.print_success_single, request)
        deferred.addErrback(self.print_failure, request)
        return server.NOT_DONE_YET

    def _PUT_update(self, request, id):

        fromJSON        = json.loads(request.content.read())
        fromJSON["id"]  = id;

        @dbdefer
        def updateTrack(session=None): return session.merge(Track(fromJSON))
        deferred = updateTrack()
        deferred.addCallback(self.print_success_single, request)
        deferred.addErrback(self.print_failure, request)
        return server.NOT_DONE_YET

    def _DELETE_single(self, request, id):

        @dbdefer
        def deleteTrack(session=None):
         Track = session.query(Track).filter(Track.id == id).first()
         session.delete(Track)
         return Track

        deferred = deleteTrack()
        deferred.addCallback(self.print_success_single, request)
        deferred.addErrback(self.print_failure, request)
        return server.NOT_DONE_YET

apiresource                     = APIResource()
Trackresource                     = TrackResource()
staticresource                  = File('/var/lib/openshift/532f22855973cac4ef00044a/app-deployments/current/repo/static/www')

apiresource.putChild('static', staticresource)

apiresource.register('GET',                 '^/v1/Tracks/(?P<id>[^/]+)$',                     Trackresource._GET_single)
apiresource.register('GET',                 '^/v1/Tracks',                                    Trackresource._GET_list)
apiresource.register('POST',                '^/v1/Tracks',                                    Trackresource._POST_create)
apiresource.register('PUT',                 '^/v1/Tracks/(?P<id>[^/]+)$',                     Trackresource._PUT_update)
apiresource.register('DELETE',              '^/v1/Tracks/(?P<id>[^/]+)$',                     Trackresource._DELETE_single)



