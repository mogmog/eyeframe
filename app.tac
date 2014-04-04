import os

from twisted.application import internet, service
from twisted.web import server
from twisted.scripts import twistd

import app

port = int(os.environ['OPENSHIFT_DIY_PORT'])
interface = os.environ['OPENSHIFT_DIY_IP']

site = server.Site(app.apiresource)
web_service = internet.TCPServer(port, site, interface=interface)

if __name__ == '__main__':
    from twisted.internet import reactor
    reactor.listenTCP(8080, site)
    reactor.run()
else:
    application = service.Application("OpenShift Twisted DIY demo")
    web_service.setServiceParent(application)
