import json
import os
import tempfile
import threading
import time
import unittest
import urllib.request
from http.client import HTTPConnection
from pathlib import Path

from voidsweep.config import Store
from voidsweep.platforms import Env
from voidsweep.server import App, serve


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        env = Env.detect()
        cls.app = App(env, store=Store(env, root=Path(cls.tmp.name)), demo=True)
        cls.httpd = serve(cls.app)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.tmp.cleanup()

    def req(self, method, path, body=None, token=True, host=None, origin=None):
        c = HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        if token:
            headers["X-Voidsweep-Token"] = self.app.token
        if origin:
            headers["Origin"] = origin
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        c.request(method, path, body=data, headers=headers)
        r = c.getresponse()
        raw = r.read()
        return r.status, raw

    def test_static_index_and_csp(self):
        c = HTTPConnection("127.0.0.1", self.port)
        c.request("GET", "/")
        r = c.getresponse()
        self.assertEqual(r.status, 200)
        self.assertIn("default-src 'self'", r.getheader("Content-Security-Policy"))

    def test_path_traversal_blocked(self):
        status, _ = self.req("GET", "/../server.py", token=False)
        self.assertEqual(status, 404)

    def test_api_requires_token(self):
        self.assertEqual(self.req("GET", "/api/info", token=False)[0], 401)
        self.assertEqual(self.req("GET", "/api/info")[0], 200)

    def test_dns_rebinding_and_cross_origin_blocked(self):
        self.assertEqual(self.req("GET", "/api/info", host="evil.example:80")[0], 403)
        self.assertEqual(self.req("POST", "/api/scan", {}, origin="https://evil.example")[0], 403)

    def test_demo_scan_and_clean_flow(self):
        status, _ = self.req("POST", "/api/scan", {"deep": False, "drives": []})
        self.assertEqual(status, 200)
        _, raw = self.req("GET", "/api/results")
        findings = json.loads(raw)["findings"]
        self.assertTrue(findings)
        self.assertTrue(all(f["reason"]["ru"] and f["reason"]["en"] for f in findings))
        ids = [f["id"] for f in findings[:3]]
        self.assertEqual(self.req("POST", "/api/clean", {"ids": ids, "mode": "trash"})[0], 200)
        for _ in range(50):
            job = json.loads(self.req("GET", "/api/job")[1])
            if job["state"] != "running":
                break
            time.sleep(0.05)
        res = json.loads(self.req("GET", "/api/clean/result")[1])
        self.assertEqual(len(res["results"]), 3)

    def test_bad_mode_rejected(self):
        self.assertEqual(self.req("POST", "/api/clean", {"ids": [], "mode": "nuke"})[0], 400)


if __name__ == "__main__":
    unittest.main()
