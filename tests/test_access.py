import http.cookiejar
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from server import Handler, RECORDS

class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f"http://127.0.0.1:{cls.server.server_port}"
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
    def browser(self):
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def sign_in(self,client,user):
        request=urllib.request.Request(self.base+"/login",method="POST",
            data=urllib.parse.urlencode({"username":user,"password":"demo123"}).encode())
        return client.open(request)
    def test_anonymous_redirect(self):
        client=self.browser()
        with client.open(self.base+"/dashboard") as response:
            self.assertEqual(response.url,self.base+"/login")
    def test_own_records_but_not_other_employees(self):
        client=self.browser()
        self.sign_in(client,"diego")
        own=next(r for r in RECORDS if r["owner"]=="diego")
        other=next(r for r in RECORDS if r["owner"]=="maria")
        with client.open(self.base+"/record?id="+own["id"]) as response:
            self.assertEqual(response.status,200)
        with self.assertRaises(urllib.error.HTTPError) as response:
            client.open(self.base+"/record?id="+other["id"])
        self.assertEqual(response.exception.code,404)
    def test_csv_export_is_owner_scoped(self):
        client=self.browser()
        self.sign_in(client,"allison")
        with client.open(self.base+"/export.csv?fy=FY26&category=mrs") as response:
            csv_text=response.read().decode("utf-8")
        actual={line.split(",",1)[0] for line in csv_text.splitlines()[1:]}
        expected={r["id"] for r in RECORDS if r["owner"]=="allison" and r["fy"]=="FY26" and r["category"]=="mrs"}
        self.assertEqual(actual,expected)
    def test_switch_year(self):
        client=self.browser()
        self.sign_in(client,"roger")
        with client.open(self.base+"/dashboard?fy=FY24") as response:
            self.assertIn("FY24 overview",response.read().decode())

if __name__=="__main__":
    unittest.main()
