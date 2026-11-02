"""Local, single-user Engineering Insights portfolio demo (Python 3.10+, stdlib)."""
import csv, html, io, json, secrets, threading, time
from collections import Counter
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

ROOT=Path(__file__).resolve().parent
# Reproducible data is generated locally, rather than committing a large JSON file.
from generate_data import make_data
DATA=make_data()
PEOPLE=DATA["personas"]; CATS=DATA["categories"]; RECORDS=DATA["records"]
BY_ID={r["id"]:r for r in RECORDS}
SESSIONS={}; LOCK=threading.Lock(); FYS=["FY24","FY25","FY26","FY27"]
PASSWORD="demo123"  # Local demo only, never deploy or use with real employee records.
SESSION_AGE=8*3600

def esc(value): return html.escape(str(value),quote=True)
def query(url): return {k:v[0] for k,v in parse_qs(urlsplit(url).query).items()}
def link(path,**kwargs): return path+("?" + urlencode(kwargs) if kwargs else "")
def layout(title,body,user=None):
    account=(f'<div class="account"><strong>{esc(PEOPLE[user]["name"])}</strong><form method="post" action="/logout"><button class="ghost small">Sign out</button></form></div>' if user else '<span class="tag">Independent portfolio prototype</span>')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Engineering Insights</title><link rel="stylesheet" href="/assets/style.css"></head><body><header class="topbar"><div class="brand"><div class="mark">EI</div><div><strong>Engineering Insights</strong><span>Beyond the Metrics</span></div></div>{account}</header><main class="container">{body}</main><footer>Independent portfolio demo · All employees and records are synthetic · Not a performance scoring system</footer></body></html>'''

class Handler(BaseHTTPRequestHandler):
    server_version="EngineeringInsightsDemo/1.1"
    def log_message(self,fmt,*args): print("%s - %s"%(self.address_string(),fmt%args))
    def respond(self,body,status=200,content_type="text/html; charset=utf-8",headers=None):
        data=body.encode("utf-8") if isinstance(body,str) else body
        self.send_response(status)
        for k,v in [("Content-Type",content_type),("Content-Length",str(len(data))),("Cache-Control","no-store"),("X-Content-Type-Options","nosniff"),("X-Frame-Options","DENY"),("Content-Security-Policy","default-src 'self'; style-src 'self'; img-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")]:
            self.send_header(k,v)
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(data)
    def redirect(self,path,headers=None):
        self.send_response(303);self.send_header("Location",path);self.send_header("Cache-Control","no-store")
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers()
    def signed_in(self):
        jar=cookies.SimpleCookie()
        try: jar.load(self.headers.get("Cookie",""))
        except cookies.CookieError: return None
        token=jar.get("ei_session")
        if token is None:return None
        with LOCK:
            session=SESSIONS.get(token.value)
            if session is None:return None
            username,expiry=session
            if expiry<time.time():
                SESSIONS.pop(token.value,None);return None
            return username
    def do_GET(self):
        route=urlsplit(self.path).path
        if route=="/assets/style.css":
            return self.respond((ROOT/"assets"/"style.css").read_bytes(),content_type="text/css; charset=utf-8")
        if route=="/login":return self.login_page()
        user=self.signed_in()
        if user is None:return self.redirect("/login")
        if route in ["/","/dashboard"]:return self.dashboard(user)
        if route=="/records":return self.records_page(user)
        if route=="/record":return self.record_page(user)
        if route=="/export.csv":return self.export(user)
        return self.respond(layout("Not found","<section class='panel'><h1>Page not found</h1></section>",user),404)
    def do_POST(self):
        route=urlsplit(self.path).path
        size=int(self.headers.get("Content-Length","0"))
        if size>8192 or size<0:return self.respond("Request too large",413)
        args={k:v[0] for k,v in parse_qs(self.rfile.read(size).decode("utf-8","replace")).items()}
        if route=="/login":
            username=args.get("username","")
            if username not in PEOPLE or not secrets.compare_digest(args.get("password",""),PASSWORD):
                return self.login_page("Invalid demonstration account or password.")
            token=secrets.token_urlsafe(32)
            with LOCK:SESSIONS[token]=(username,time.time()+SESSION_AGE)
            return self.redirect("/dashboard",{"Set-Cookie":f"ei_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_AGE}"})
        if route=="/logout":
            jar=cookies.SimpleCookie()
            try:jar.load(self.headers.get("Cookie",""))
            except cookies.CookieError:jar=cookies.SimpleCookie()
            token=jar.get("ei_session")
            if token:
                with LOCK:SESSIONS.pop(token.value,None)
            return self.redirect("/login",{"Set-Cookie":"ei_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"})
        return self.respond("Not found",404)
    def login_page(self,error=None):
        options="".join(f'<option value="{esc(u)}">{esc(p["name"])} — {esc(p["role"])}</option>' for u,p in PEOPLE.items())
        warning=f'<div class="error">{esc(error)}</div>' if error else ""
        body=f'''<div class="login-grid"><section class="login-hero"><div class="eyebrow">Engineering leadership portfolio case study</div><h1>Every engineer brings more than numbers can show.</h1><p>Explore a contribution dashboard designed to support reflection, transparency, and development conversations—not employee rankings.</p><div class="principles"><span>Personal contributions</span><span>Evidence for conversations</span><span>Beyond the Metrics</span></div></section><section class="panel login-card"><div class="eyebrow">Local demonstration</div><h2>View your contributions</h2><p>Select a fictional employee. Each account has access only to its own records.</p>{warning}<form method="post" action="/login"><label for="username">Employee</label><select name="username" id="username">{options}</select><label for="password">Demo password</label><input id="password" name="password" type="password" value="demo123" required><button class="primary full">Sign in</button></form><p class="hint">Password: <code>demo123</code>. Local-only demo, not enterprise authentication.</p></section></div>'''
        return self.respond(layout("Sign in",body),401 if error else 200)
    def year(self):
        fy=query(self.path).get("fy","FY26")
        return fy if fy in FYS else "FY26"
    def owned(self,user,fy,category=None):
        return [r for r in RECORDS if r["owner"]==user and r["fy"]==fy and (category is None or r["category"]==category)]
    def dashboard(self,user):
        fy=self.year();person=PEOPLE[user];totals=Counter(r["category"] for r in self.owned(user,fy))
        order=["mrs","reviews","defects","spikes","customer","tasks","manual","automated"]
        symbols={"mrs":"↗","reviews":"◎","defects":"✓","spikes":"◇","customer":"♧","tasks":"▤","manual":"◉","automated":"⌘"}
        cards="".join(f'<a class="metric" href="{link("/records",fy=fy,category=c)}"><span class="metric-icon">{symbols[c]}</span><span class="metric-count">{totals[c]}</span><span class="metric-label">{esc(CATS[c]["label"])}</span><span class="metric-source">{esc(CATS[c]["source"])} ↗</span></a>' for c in order)
        years="".join(f'<option value="{v}" {"selected" if fy==v else ""}>{v}{" (illustrative)" if v=="FY27" else ""}</option>' for v in FYS)
        reflection='''<section class="reflection"><div class="eyebrow">Beyond the Metrics</div><h2>You bring something unique to the team.</h2><p>These quantitative measures are here to jog your memory about the work you contributed this year. Is this how you envisioned spending your time? Which achievements are you most proud of?</p><p><strong>Your magic—the creativity, mentorship, leadership and kindness you bring—may not show up in these counts.</strong> Use them as a starting point and discuss the rest of your story with your manager. 🙂</p><div class="reflection-prompts"><span>What did you learn?</span><span>Who did you help?</span><span>What had the biggest impact?</span><span>What would you like to do next?</span></div></section>'''
        body=f'''<div class="page-head"><div><div class="eyebrow">Your personal contribution history</div><h1>Welcome back, {esc(person["name"].split()[0])}.</h1><p class="subtitle">{esc(person["role"])} · {esc(person["focus"])}</p></div><form action="/dashboard" method="get" class="fy-form"><label for="fy">Fiscal year</label><select name="fy" id="fy">{years}</select><button class="ghost">View year</button></form></div><section class="intro"><div><div class="eyebrow">{fy} overview</div><h2>Your work, at a glance</h2><p>Click any number to inspect its fictional underlying records. Counts describe activity, not performance.</p></div><span class="private-tag">🔒 Only your records</span></section><div class="metrics">{cards}</div>{reflection}<section class="panel small-panel"><h3>How to use this dashboard</h3><p>Open a metric and explore your work items to prepare examples for an individual development or performance conversation. The data cannot capture your full impact.</p><p class="hint">Four fictional employees and FY24–FY27 synthetic records. FY27 is an illustrative partial year.</p></section>'''
        return self.respond(layout("Dashboard",body,user))
    def records_page(self,user):
        fy=self.year();p=query(self.path);category=p.get("category","")
        if category not in CATS:return self.respond(layout("Not found","<h1>Metric not found</h1>",user),404)
        rows=sorted(self.owned(user,fy,category),key=lambda r:r["date"],reverse=True)
        term=p.get("q","").strip()[:100]
        shown=[r for r in rows if term.lower() in (r["id"]+" "+r["title"]).lower()] if term else rows
        table_rows="".join(f'<tr><td><a class="record-id" href="{link("/record",id=r["id"],fy=fy,category=category)}">{esc(r["id"])}</a></td><td>{esc(r["title"])}</td><td><span class="pill">{esc(r["status"])}</span></td><td class="date">{esc(r["date"])}</td></tr>' for r in shown)
        if not table_rows:table_rows='<tr><td colspan="4" class="empty">No matching records.</td></tr>'
        body=f'''<div class="breadcrumbs"><a href="{link("/dashboard",fy=fy)}">← Dashboard</a><span>/</span>{fy}<span>/</span>{esc(CATS[category]["label"])}</div><div class="page-head"><div><div class="eyebrow">{esc(CATS[category]["source"])} · {fy}</div><h1>{esc(CATS[category]["label"])}</h1><p class="subtitle">{len(rows)} fictional contribution records for {esc(PEOPLE[user]["name"])}.</p></div><a class="secondary-button" href="{link("/export.csv",fy=fy,category=category)}">Export CSV ↓</a></div><section class="panel"><form class="search" method="get" action="/records"><input type="hidden" name="fy" value="{fy}"><input type="hidden" name="category" value="{esc(category)}"><label for="q">Filter records</label><input type="search" id="q" name="q" value="{esc(term)}" placeholder="Search ID or title"><button class="ghost">Search</button></form><div class="tablewrap"><table><thead><tr><th>ID</th><th>Contribution</th><th>Status</th><th>Date</th></tr></thead><tbody>{table_rows}</tbody></table></div><p class="hint">Showing {len(shown)} of {len(rows)} records. No internal Jira/GitLab or other proprietary links.</p></section>'''
        return self.respond(layout("Contributions",body,user))
    def record_page(self,user):
        rid=query(self.path).get("id","");r=BY_ID.get(rid)
        # Never trust the caller's employee or query parameter as an authorization check.
        if not r or r["owner"]!=user:return self.respond(layout("Not found","<section class='panel'><h1>Record not found</h1></section>",user),404)
        body=f'''<div class="breadcrumbs"><a href="{link("/dashboard",fy=r["fy"])}">← Dashboard</a><span>/</span><a href="{link("/records",fy=r["fy"],category=r["category"])}">{esc(CATS[r["category"]]["label"])}</a></div><section class="panel detail"><div class="eyebrow">{esc(r["source"])} · {esc(r["fy"])}</div><h1>{esc(r["title"])}</h1><p class="record-id big">{esc(r["id"])}</p><dl><div><dt>Status</dt><dd>{esc(r["status"])}</dd></div><div><dt>Date</dt><dd>{esc(r["date"])}</dd></div><div><dt>Contributor</dt><dd>{esc(PEOPLE[user]["name"])}</dd></div><div><dt>Provenance</dt><dd>Synthetic local record</dd></div></dl><h3>Contribution context</h3><p>{esc(r["summary"])}</p><div class="note">Which collaboration, mentoring, technical challenge or leadership contributions surrounded this work? Those details aren't captured by a count.</div></section>'''
        return self.respond(layout("Contribution",body,user))
    def export(self,user):
        fy=self.year();category=query(self.path).get("category","")
        if category not in CATS:return self.respond("Not found",404)
        output=io.StringIO();fields=["id","title","status","date","source","fy"];writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
        for record in self.owned(user,fy,category):writer.writerow({field:record[field] for field in fields})
        return self.respond(output.getvalue(),content_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="{user}-{fy}-{category}.csv"'})

if __name__=="__main__":
    print("Engineering Insights: http://127.0.0.1:8765/login")
    print("Four fictional employee accounts; demo password: demo123")
    print("Local-only demonstration. Do not expose to the internet.")
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
