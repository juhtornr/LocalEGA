#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Connecting to Central EGA
#
####################################

Re-publish a message from the local broker into CentralEGA's broker.
'''

import sys
import logging

from .conf import CONF
from . import amqp as broker

LOG = logging.getLogger('cega_answer')

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    cega_connection = broker.get_connection('cega.broker')
    cega_channel = cega_connection.channel()

    lega_connection = broker.get_connection('local.broker')
    lega_channel = lega_connection.channel()
    lega_channel.basic_qos(prefetch_count=1) # One job

    try:
        broker.forward(lega_channel,
                       from_queue  = CONF.get('local.broker','verified_queue'),
                       to_channel  = cega_channel,
                       to_exchange = CONF.get('cega.broker','exchange'),
                       to_routing  = CONF.get('cega.broker','routing_to'))
    except KeyboardInterrupt:
        lega_channel.stop_consuming()
    finally:
        cega_connection.close()
        lega_connection.close()

if __name__ == '__main__':
    main()
