from __future__ import absolute_import
from twisted.application import service
from zeit_premium_dwh.consumer import PikaService

application = service.Application('zeit-premium-dwh')
PikaService().setServiceParent(application)
