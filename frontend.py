import requests
from sanic import Sanic, Request, HTTPResponse
import config
import os

app = Sanic.get_app("SwiftNext")

app.static("/", os.path.join(config.dist_path, "index.html"))

app.static("/favicon.ico", os.path.join(config.dist_path, "favicon.ico"))

app.static("/*", os.path.join(config.dist_path, "index.html"), )

app.static("/assets", config.assets_path)


