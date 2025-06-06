import http.client

conn = http.client.HTTPSConnection("open.steamdt.com")
payload = ''
headers = {}
conn.request("GET", "/open/cs2/v1/base", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))