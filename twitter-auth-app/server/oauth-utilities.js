const oauth = require("oauth");

const { promisify } = require("util");

const TWITTER_CONSUMER_API_KEY =
  process.env.npm_config_twitter_consumer_api_key ||
  process.env.TWITTER_CONSUMER_API_KEY;
const TWITTER_CONSUMER_API_SECRET_KEY =
  process.env.npm_config_twitter_consumer_api_secret_key ||
  process.env.TWITTER_CONSUMER_API_SECRET_KEY;
const TWITTER_CALLBACK_URL =
  process.env.npm_config_twitter_callback_url ||
  process.env.TWITTER_CALLBACK_URL;

const oauthConsumer = new oauth.OAuth(
  "https://twitter.com/oauth/request_token",
  "https://twitter.com/oauth/access_token",
  TWITTER_CONSUMER_API_KEY,
  TWITTER_CONSUMER_API_SECRET_KEY,
  "1.0A",
  TWITTER_CALLBACK_URL,
  "HMAC-SHA1"
);

module.exports = {
  oauthGetUserById,
  getOAuthAccessTokenWith,
  getOAuthRequestToken,
};

async function oauthGetUserById(
  userId,
  { oauthAccessToken, oauthAccessTokenSecret } = {}
) {
  return promisify(oauthConsumer.get.bind(oauthConsumer))(
    `https://api.twitter.com/1.1/users/show.json?user_id=${userId}`,
    oauthAccessToken,
    oauthAccessTokenSecret
  ).then((body) => JSON.parse(body));
}
async function getOAuthAccessTokenWith({
  oauthRequestToken,
  oauthRequestTokenSecret,
  oauthVerifier,
} = {}) {
  return new Promise((resolve, reject) => {
    oauthConsumer.getOAuthAccessToken(
      oauthRequestToken,
      oauthRequestTokenSecret,
      oauthVerifier,
      function (error, oauthAccessToken, oauthAccessTokenSecret, results) {
        return error
          ? reject(
              new Error(
                "Error getting OAuth access token.\nCODE: " +
                  error.statusCode +
                  "\nDATA: " +
                  error.data
              )
            )
          : resolve({ oauthAccessToken, oauthAccessTokenSecret, results });
      }
    );
  });
}
async function getOAuthRequestToken() {
  return new Promise((resolve, reject) => {
    oauthConsumer.getOAuthRequestToken(function (
      error,
      oauthRequestToken,
      oauthRequestTokenSecret,
      results
    ) {
      return error
        ? reject(new Error("Error getting OAuth request token"))
        : resolve({ oauthRequestToken, oauthRequestTokenSecret, results });
    });
  });
}
