# Twisted, the Framework of Your Internet
# Copyright (C) 2001-2003 Matthew W. Lefkowitz
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
from twisted.application import service

class _VolatileDataService(service.Service):

    volatile = []

    def __getstate__(self):
        d = service.Service.__getstate__(self)
        for attr in self.volatile:
            if d.has_key(attr):
                del d[attr]
        return d

class _AbstractServer(_VolatileDataService):

    privileged = 0
    volatile = '_port'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def privilegedStartService(self):
        service.Service.privilegedStartService(self)
        if self.privileged:
            self._port = self.getPort()

    def startService(self):
        service.Service.startService(self)
        if not self.privileged:
            self._port = self.getPort()

    def stopService(self):
        service.Service.stopService(self)
        self._port.stopListening()

    def getPort(self):
        from twisted.internet import reactor
        return getattr(reactor, 'listen'+self.method)(*self.args, **self.kwargs)

class _AbstractClient(_VolatileDataService):

    volatile = ['_connection']

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def startService(self):
        service.Service.startService(self)
        self._connection = self.getConnection()

    def stopService(self):
        service.Service.stopService(self)
        #self._connection.stopConnecting()

    def getConnection(self):
        from twisted.internet import reactor
        return getattr(reactor, 'connect'+self.method)(*self.args,
                                                       **self.kwargs)


import new
for tran in 'Generic TCP UNIX SSL UDP UNIXDatagram Multicast'.split():
    for side in 'Server Client'.split():
        base = globals()['_Abstract'+side]
        method = (tran=='Generic' and 'With') or tran
        klass = new.classobj(tran+side, (base,), {'method': method})
        globals()[tran+side] = klass


class TimerService(_VolatileDataService):

    volatile = ['_call']

    def __init__(self, step, callable, *args, **kwargs):
        self.step = step
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

    def startService(self):
        from twisted.internet import reactor
        service.Service.startService(self)
        self._call = reactor.callLater(self.step, self._setupCall)

    def _setupCall(self):
        from twisted.internet import reactor
        self.callable(*self.args, **self.kwargs)
        self._call = reactor.callLater(self.step, self._setupCall)

    def stopService(self):
        service.Service.stopService(self)
        self._call.cancel()
