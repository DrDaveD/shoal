import sys
import time
import web
import json
import logging

import pika

from time import time, sleep
from threading import Thread

import config
import geoip
import urls

logging.basicConfig()
log = logging.getLogger('shoal')
"""
    Basic class to store and update information about each squid server.
"""
class SquidNode(object):
    def __init__(self, key, public_ip, private_ip, load, geo_data, last_active=time()):
        self.key = key
        self.created = time()
        self.last_active = last_active

        self.public_ip = public_ip
        self.private_ip = private_ip
        self.load = load
        self.geo_data = geo_data

    def update(self, public_ip, private_ip, load, geo_data):
        self.last_active = time()

        self.public_ip = public_ip
        self.private_ip = private_ip
        self.load = load
        self.geo_data = geo_data

"""
    Main application that will delegate threads.
"""
class Application(object):

    def __init__(self):
        # setup configuration settings.
        config.setup()
        set_logger()
        self.shoal = {}
        self.threads = []

        # check if geolitecity database needs updating
        if geoip.check_geolitecity_need_update():
            geoip.download_geolitecity()

        try:
            rabbitmq_thread = Thread(target=self.rabbitmq, name='RabbitMQ')
            rabbitmq_thread.daemon = True
            self.threads.append(rabbitmq_thread)

            webpy_thread = Thread(target=self.webpy, name='Webpy')
            webpy_thread.daemon = True
            self.threads.append(webpy_thread)

            update_thread = Thread(target=self.update, name="ShoalUpdate")
            update_thread.daemon = True
            self.threads.append(update_thread)

            for thread in self.threads:
                thread.start()
            while True:
                for thread in self.threads:
                    if not thread.is_alive():
                        log.error('{} died.'.format(thread))
                        sys.exit(1)

        except KeyboardInterrupt:
            for thread in self.threads:
                thread.join()
                print 'killed thread: ', thread
            self.webpy.stop()
            self.rabbitmq.stop()

    def rabbitmq(self):
        self.rabbitmq = RabbitMQConsumer(self.shoal)
        self.rabbitmq.run()

    def webpy(self):
        self.webpy = WebpyServer(self.shoal)
        self.webpy.run()

    def update(self):
        self.update = ShoalUpdate(self.shoal)
        self.update.run()


"""
    ShoalUpdate is used for trimming inactive squids every set interval.
"""
class ShoalUpdate(object):

    def __init__(self, shoal):
        self.shoal = shoal
        self.interval = config.squid_cleanse_interval
        self.inactive = config.squid_inactive_time

    def run(self):
        while True:
            sleep(self.interval)
            self.update()

    def update(self):
        curr = time()
        for squid in self.shoal.values():
            if curr - squid.last_active > self.inactive:
                self.shoal.pop(squid.key)

"""
    Webpy webserver used to serve up active squid lists and restul API calls. For now we just use the development webpy server to serve requests.
"""
class WebpyServer(object):

    def __init__(self, shoal):
        web.shoal = shoal

    def run(self):
        self.app = web.application(urls.urls, globals())
        self.app.run()

    def stop(self):
        self.app.stop()

"""
    Basic RabbitMQ blocking consumer. Consumes messages from `QUEUE` takes the json in body, and put it into the dictionary `shoal`
    Messages received must be a json string with keys:
    {
      'uuid': '1231232',
      'public_ip': '142.11.52.1',
      'private_ip: '192.168.0.1',
      'load': '12324432',
      'timestamp':'2121231313',
    }
"""
class RabbitMQConsumer(object):

    def __init__(self, shoal):
        self.url = config.amqp_server_url
        self.queue = config.amqp_server_queue
        self.port = config.amqp_server_port
        self.exchange = config.amqp_exchange
        self.exchange_type = config.amqp_exchange_type
        self.routing_key = '#'
        self.shoal = shoal
        self.connection = None
        self.channel = None

    def run(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.url, self.port))
        except Exception as e:
            log.error('Could not connected to AMQP Server. Error: %s' % e)
            sys.exit(1)

        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=self.exchange,
                                 type=self.exchange_type)

        self.channel.queue_declare(queue=self.queue)

        self.channel.queue_bind(exchange=self.exchange, queue=self.queue,
                           routing_key=self.routing_key)

        for method_frame, properties, body in self.channel.consume(self.queue):
            self.on_message(method_frame, properties, body)
            self.channel.basic_ack(method_frame.delivery_tag)

    def on_message(self, method_frame, properties, body):
        try:
            squid_inactive_time = config.squid_inactive_time
            curr = time()
            data = json.loads(body)

            key = data['uuid']
            public_ip = data['public_ip']
            private_ip = data['private_ip']
            load = data['load']
            geo_data = geoip.get_geolocation(public_ip)
            last_active = data['timestamp']

            if key in self.shoal:
                self.shoal[key].update(public_ip, private_ip, load, geo_data)
            elif curr - last_active < squid_inactive_time:
                new_squid = SquidNode(key, public_ip, private_ip, load, geo_data, last_active)
                self.shoal[key] = new_squid

        except KeyError as e:
            log.error("Message received was not the proper format (missing:{}), discarding...\nmethod_frame:{}\nproperties:{}\nbody:{}\n".format(e,method_frame,properties,body))

    def stop(self):
        self.channel.stop()
        self.connection.close()

def set_logger():
    log_file = config.log_file
    log_format = config.log_format
    log_level = config.log_level

    log = logging.getLogger('shoal')
    hdlr = logging.FileHandler(log_file)
    formatter = logging.Formatter(log_format)
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(log_level)

def main():
    set_logger()
    app = Application()

if __name__ == '__main__':
    main()
