ip.berlin.freifunk.net API
==========================

RESTful API for ip.berlin.freifunk.net

Install

    $ virtualenv2 env
    $ . env/bin/activate
    $ pip install -r requirements.txt
    $ python manage.py initdb


Dev Server (including dev smtp server for emails)

    $ python -m smtpd -n -c DebuggingServer localhost:1025
    $ python manage.py runserver
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader


Tests

    $ nosetests
    ......
    ----------------------------------------------------------------------
    Ran 9 tests in 0.389s


For database migrations

    $ python manage.py db init
    $ python manage.py db migrate
    $ python manage.py db upgrade



User
----

Register new account

    $ curl --data "email=foo%40bar.de&password=foobar" http://localhost:5000/user
    {
      "message": "success"
    }


Get account information

    $ curl -u foo@bar.de:foobar http://localhost:5000/user
    {
      "user": {
        "email": "foo@bar.de",
        "id": 1,
        "networks": [
          {
            "network": "104.0.0.0/28",
            "url": "http://localhost:5000/networks/104.0.0.0/28"
          },
          {
            "network": "192.168.0.0/26",
            "url": "http://localhost:5000/networks/192.168.0.0/26"
          }
        ]
      }
    }


Delete an account

    $ curl -X DELETE -u foo@bar.de:foobar http://localhost:5000/user
    {
      "message": "success"
    }


Networks
--------

Register new network

    $ curl -u foo@bar.de:foobar --data "address=104.0.0.0&prefixlen=28" http://localhost:5000/networks
    {
      "message": "success"
    }


Get information about a network

    $ curl -u foo@bar.de:foobar http://localhost:5000/networks/104.0.0.0/28
    {
      "network": {
        "address": "104.0.0.0",
        "broadcast": "104.0.0.15",
        "hosts": [
          "104.0.0.1",
          "104.0.0.2",
          "104.0.0.3",
          "104.0.0.4",
          "104.0.0.5",
          "104.0.0.6",
          "104.0.0.7",
          "104.0.0.8",
          "104.0.0.9",
          "104.0.0.10",
          "104.0.0.11",
          "104.0.0.12",
          "104.0.0.13",
          "104.0.0.14"
        ],
        "is_private": false,
        "netmask": "255.255.255.240",
        "network": "104.0.0.0/28",
        "owner": "foo@bar.de",
        "prefixlen": 28
      }


Get network for a specific ip address

    $ curl -u foo@bar.de:foobar http://localhost:5000/networks/104.0.0.1


List all registered networks

    $ curl -u foo@bar.de:foobar http://localhost:5000/networks
    {
      "networks": [
        {
          "network": "104.0.0.0/28",
          "owner": "foo@bar.de",
          "url": "http://localhost:5000/networks/104.0.0.0/28"
        },
        {
          "network": "192.168.0.0/26",
          "owner": "foo@bar.de",
          "url": "http://localhost:5000/networks/192.168.0.0/26"
        }
      ]
    }


Remove a network

    $ curl -X DELETE -u foo@bar.de:foobar http://localhost:5000/networks/104.0.0.0/28
