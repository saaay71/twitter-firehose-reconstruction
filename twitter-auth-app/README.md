# Twitter Firehose Web Application

### Configuration / Add environment variables

Type in your twitter-app credentials and your domain-name in `server/.npmrc` and in `client/src/config.js`. (See `.npmrc.example` and `client/src/config.js.example`)

### Start production build (docker)

Just type `make run-build-production` for a complete build and afterwards type `make run-production` to start the container.

### Start development

Start server and client separately with `make` in `/client` and `/server` or follow our recommendation and use `make run-development -j2` (type at top level of your project).

### Open WebApp

The frontend runs on [http://127.0.0.1:3001](http://127.0.0.1:3001), the backend which includes a reverse proxy on [http://127.0.0.1:3000/](http://127.0.0.1:3000/).

### How to integrate Telegram notification for new Tokens.

If you want to get notifications for every new Token in Telegram (incl. their Token and secret), just follow [this tutorial](https://core.telegram.org/bots) and include the credentials in the `.npmrc` file.

### How to build your own Twitter Auth-App

💣 **Full tutorial can be found on [cri.dev](https://cri.dev/posts/2020-03-05-Twitter-OAuth-Login-by-example-with-Node.js/)!** 🚀

---

Create an app on [developer.twitter.com](https://developer.twitter.com/en/apps) and get the following key and tokens:

- `TWITTER_CONSUMER_API_KEY`
- `TWITTER_CONSUMER_API_SECRET`

Then set them in the local `.npmrc`file and run `npm start`.
