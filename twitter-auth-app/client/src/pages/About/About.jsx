import React from "react";
import { Typography, Row, Col } from "antd";

const { Title, Text } = Typography;

const About = () => {
  const faqContentArray = () => {
    return [
      <>
        <Title level={3}>How exactly does this work?</Title>
        <Text>
          With your authorization, we receive a user token that we can use to
          make requests on your behalf. In each 15-minute time slot we can send
          900 requests. This is exactly one request per second. In each request
          we can ask Twitter for 100 Tweet-Ids. Unfortunately, we don't know all
          the ids that are taken, so we have to guess a bit. Fortunately, the
          tweet ids are not as random as it seems at first glance. Twitter
          creates the Tweet-Ids as so-called{" "}
          <a href="https://en.wikipedia.org/wiki/Snowflake_ID">Snowflakes</a>.
          In this type of unique identifier, the timestamp, data center number,
          server number and a sequential number are encoded. Since we know the
          current time and have created a list of Twitter servers, the only
          thing missing is the sequence number. We have to guess this. Or just
          start from 0 and count up. But since about 20% of all tweets have the
          running number 0, we first request all tweets with this ID, and
          increase the running number accordingly.
        </Text>
      </>,
      <>
        <Title level={3}>How can I remove myself from the list?</Title>
        <Text>
          To withdraw your token from our system, you can easily remove it via
          the <a href="https://www.twitter.com">Twitter website</a>:
          <ol>
            <li>Sign in to your account.</li>
            <li>
              Go to the 'Apps and sessions' section of your account settings.
              All of the apps connected to your account will be displayed. You
              can see the specific permissions that each app has to use your
              account listed under the app name and description.
            </li>
            <li>
              If you'd like to disconnect an app from your account, click the
              Revoke access button next to the app or at the bottom of the page
              after clicking the app's name.
            </li>
          </ol>
        </Text>
      </>,
      <>
        <Title level={3}>Who are you?</Title>
        <Text>
          We are three master students at the{" "}
          <a href="https://www.hpi.de">Hasso Plattner Institute</a> in Potsdam.
          In our joint seminar 'Social Media Mining' we built a software
          solution that can be used to create a livestream of tweets with the
          help of so-called user tokens. We get these user tokens by your
          approval via the 'Auth/Login' button on the top right, or via the
          button on our main page.
        </Text>
      </>,
      <>
        <Title level={3}>Are you allowed to do that?</Title>
        <Text>
          Sure, otherwise we wouldn't do it ;). But seriously, you can read all
          about that{" "}
          <a href="https://developer.twitter.com/en/developer-terms/policy#4-c">
            here
          </a>
          . Twitter is very generous when it comes to analyzing their data for
          research purposes.
        </Text>
      </>,
      <>
        <Title level={3}>What are you doing with my data?</Title>
        <Text>
          As mentioned, we can send a certain number of requests per minute for
          each user registered with our app. We only use your access permission
          to query tweet ids that we generate. Your personal tweets, likes and
          retweets are not queried by us.
        </Text>
      </>,
      <>
        <Title level={3}>Can my account be suspended?</Title>
        <Text>
          We have been testing our system for a few weeks and have of course
          already provided tokens with our private accounts. No account has been
          blocked, but there was one account that was created before Twitter
          compulsively asked for a phone number, where we were asked to confirm
          the phone number.
        </Text>
      </>,
      <>
        <Title level={3}>How can we support your great work?</Title>
        <Text>
          Just donate{" "}
          <a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ">here</a> on our
          Patreo.... Just kidding 😉. The most you can do to support us is to
          authorize our app. If you want to support us a little more, it would
          be super sweet if you could tell your friends about this. It would
          really help us a lot.
        </Text>
      </>,
    ];
  };

  const infoText = () => (
    <Text>
      Twitter Firehose is a paid API of the short message service Twitter that
      provides a live stream of all tweets sent. This API is used by many
      business security and consulting companies, which allegedly pay mid
      5-digit sums for it.
      <br />
      With this project, we implement the concept of Jason Baumgartner, in which
      he demonstrates how OAuth tokens from verified users can be used to
      request tweets via another Twitter API. To request a tweet, we need to
      guess the TweetId for this purpose. This TweetId is also called Snowflake
      and consists of the Twitter server used and the datacenter ID, a timestamp
      and a sequential number. We have developed the algorithm for guessing
      correct Snowflakes independently and optimized it several times. Due to a
      limit on the maximum tweets to be queried per 15 minutes, we still need
      numerous tokens to get good coverage of the Twitter live feed.
    </Text>
  );

  return (
    <>
      <Title level={2}>About our project</Title>
      <Row gutter={[16, 16]}>
        <Col sm={24} md={18} xl={20}>
          {infoText()}
        </Col>

        <Col
          sm={0}
          md={6}
          xl={4}
          style={{ textAlign: "center", verticalAlign: "middle" }}
        >
          <img
            className="logo"
            style={{ height: "8rem" }}
            src="/twitter_logo.png"
            alt="Icon"
          />
        </Col>
      </Row>
      <br />

      <Title level={2}>Frequently asked questions (FAQ)</Title>
      <Row gutter={[16, 16]} style={{ heigth: "100%" }}>
        {faqContentArray().map((faqItem, index) => (
          <Col sm={24} md={12} xl={8} style={{ height: "100%" }} key={index}>
            <div
              style={{
                background: "#f0f2f5",
                minHeight: "18rem",
                padding: "1rem",
              }}
            >
              {faqItem}
            </div>
          </Col>
        ))}
      </Row>
    </>
  );
};

export default About;
