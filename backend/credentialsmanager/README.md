# Credentialsmanager

The credentialsmanager is a very simple flask app on port 5000 with three routes:
- `/new_token/<id>`: Returns another working token and assumes that the token that was previously returned is now empty for the remaining time of the 15min-window.
- `/first_token/<id>`: Returns a working token without setting the previous token as empty. Is used by starting workers, so that during development, tokens are not marked as blocked just because you restarted the workers.
- `/num_tokens`: Returns the current number of usable tokens.

The credentialsmanager does a couble of things on startup:
1. It downloads the current tokens from a route of the webapp
2. It checks them against a cached blocklist in redis to make sure we don't try revoked tokens again, and
3. lastly it makes a single call against the API to make sure the token really works

