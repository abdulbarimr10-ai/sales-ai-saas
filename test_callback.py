import requests

# Test various Gmail endpoints
endpoints = [
    '/api/gmail/callback?state=teststate123',
    '/api/gmail/status',
    '/api/gmail/connect',
]

for ep in endpoints:
    r = requests.get(f'http://localhost:5000{ep}', allow_redirects=False)
    print(f'{ep}')
    print(f'  Status: {r.status_code}')
    loc = r.headers.get('Location', 'NONE')
    print(f'  Location: {loc}')
    body = r.text[:150].replace('\n', ' ')
    print(f'  Body: {body}')
    print()
