#!/usr/bin/env python3

"""
Entry point for the Pub Corp Repository application.

This script initializes and runs the Flask application that serves as a proxy for pub.dev
and manages packages in a GCP bucket.

@example
```bash
python run.py
```
"""

from pub_proxy.api.app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)