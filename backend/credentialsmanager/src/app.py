from urllib import response
from markupsafe import escape
from flask import Flask, Response
from Credentialsmanager import Credentialsmanager
import logging
import os

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

def ensure_env_variables_exist():
    for variable in ["TWITTER_USER_CREDENTIALS_URL",
                    "TWITTER_CONSUMER_KEY_SECRET",
                    "TWITTER_CONSUMER_KEY_SECRET",
                    ]:
        temp = os.environ.get(variable)
        if temp == None or temp == "":
            LOGGER.error(variable + " is not set in credentialsmanager! Will exit now.")
            exit(1)

ensure_env_variables_exist()
app = Flask(__name__)

LOGGER.info("Credentialsmanager starting up...")
cred_manager = Credentialsmanager()
LOGGER.info("Credentialsmanager ready, we have " + str(cred_manager.get_number_of_usable_tokens()) + " tokens.")

@app.route('/first_token/<container_id>')
def first_token(container_id):
    return get_token(container_id, mark_old_as_blocked=False)

@app.route('/new_token/<container_id>')
def new_token(container_id):
    return get_token(container_id, mark_old_as_blocked=True)

@app.route('/num_tokens')
def num_tokens():
    return {"num_tokens": cred_manager.get_number_of_usable_tokens()}

def get_token(container_id, mark_old_as_blocked):
    token, retry_after = cred_manager.get_credentials(escape(container_id), mark_as_blocked=mark_old_as_blocked)
    if token != None:
        return token.keys
    else:
        response = Response(None, status=503, mimetype='application/json')
        response.retry_after = retry_after
        return response