# Shoal Server v0.7.X README

##Services
**Shoal Server** provides two services that can be utilized by clients.

###RESTful API
Clients can use the Shoal Server RESTful API to retrieve a list of nearest squids. Assuming Shoal Server is running on `localhost` the following commands can be used:

- To get a list of the default 5 nearest squids use:
 - `http://localhost/nearest`
- To retrieve a variable size of nearest squids you can use `http://localhost/nearest/<# of squids>`. For example to retrieve the closest 20 squid servers you can use:
 - `http://localhost/nearest/20`

###WPAD
Shoal Server has a basic implementation of the [WPAD](http://en.wikipedia.org/wiki/Web_Proxy_Autodiscovery_Protocol) standard.

- To retrieve a WPAD file containing the 5 closest squids you can visit:
  - `http://localhost/wpad.dat`

##Installation
 _**Note**: Requires you have a working RabbitMQ AMQP Server, and Python 2.6+_
_Recommended to use a system wide install (sudo), but works in a virtualenv with tweaks_

_**Note**: Shoal static files will be located either at `~/shoal_server/` or `/var/shoal/` if sudo was used_

_**Note**: Shoal config files will be located either at `~/.shoal/` or `/etc/shoal/` if sudo was used_

###Using Pip

1. `pip install shoal-server`

2. Check settings in `shoal_server.conf` update as needed. Make sure RabbitMQ server is running.

4. Start `shoal-server`
  - _First run make take a few seconds to start as it needs to download the GeoLiteCity database (~12MB)._

5. Visit `http://localhost:8080`

###Using Git

1. `git clone git://github.com/hep-gc/shoal.git`
2. `cd shoal/shoal-server/`
3. `python setup.py install`
4. Check settings in `shoal_server.conf` update as needed. Make sure RabbitMQ server is running.
5. Start `shoal-server`
 - _First run make take a few seconds to start as it needs to download the GeoLiteCity database (~12MB)._

6. Visit `http://localhost:8080`

##Apache and Mod_WSGI

1. Use one of the following above methods to install Shoal Server.
 - Make sure the shoal_server package is in the **global** Python packages folder.

2. Adjust settings in `/etc/shoal/shoal_server.conf`
3. Make sure you have a working Apache installation with mod_wsgi.
4. Move Shoal folder to Apache readable location. `mv /var/shoal/ /var/www/`
 - _Ensure you also change `shoal_dir` in `shoal_server.conf` to point to new directory (`/var/www/shoal/` as per example)_

5. Include this bare minimum Apache config settings in a file within `/etc/apache2/conf.d/` or similiar location.

        WSGIDaemonProcess shoal user=www-data group=www-data threads=10 processes=1
        WSGIScriptAlias / /var/www/shoal/scripts/shoal_wsgi.py
        WSGIProcessGroup shoal

        Alias /static /var/www/shoal/static/

        AddType text/html .py 

        <Directory /var/www/shoal/>
            Order deny,allow
            Allow from all 
        </Directory>
 - Some values above may need to be adjusted depending on Linux Distro used.

6. Restart Apache.
7. Visit `http://localhost`
 
