# Kiva Home Assistant Integration

Exposes your [Kiva.org](https://www.kiva.org) account balance as a Home Assistant sensor.

## Installation

1. Copy the `custom_components/kiva/` folder into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration** and search for **Kiva**.

## Getting API credentials

Kiva uses OAuth 1.0. You need four values:

| Field | Where to get it |
|---|---|
| **Consumer Key** | Your Kiva developer app's App ID |
| **Consumer Secret** | Your Kiva developer app's secret |
| **Access Token** | Obtained after authorizing the app for your account |
| **Access Token Secret** | Paired with the access token |

Register a developer app at <https://www.kiva.org/build/docs>, then complete the OAuth 1.0 authorization flow to get your access token and secret.

### Quick OAuth dance (Python helper)

```python
import requests
from requests_oauthlib import OAuth1Session

CONSUMER_KEY = "your_consumer_key"
CONSUMER_SECRET = "your_consumer_secret"

oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET)

# Step 1 – request token
r = oauth.fetch_request_token("https://api.kivaws.org/oauth/request_token.json")

# Step 2 – authorize (open this URL in your browser and note the verifier)
auth_url = oauth.authorization_url("https://www.kiva.org/oauth/authorize")
print(f"Go to: {auth_url}")
verifier = input("Enter the verifier: ")

# Step 3 – access token
oauth = OAuth1Session(
    CONSUMER_KEY,
    client_secret=CONSUMER_SECRET,
    resource_owner_key=r["oauth_token"],
    resource_owner_secret=r["oauth_token_secret"],
    verifier=verifier,
)
tokens = oauth.fetch_access_token("https://api.kivaws.org/oauth/access_token.json")
print("Access Token:", tokens["oauth_token"])
print("Access Token Secret:", tokens["oauth_token_secret"])
```

## Sensor

| Entity | Description |
|---|---|
| `sensor.kiva_<name>_balance` | Current Kiva account balance in USD |

The sensor polls every 30 minutes and includes `lender_id`, `name`, and `currency_code` as attributes.
