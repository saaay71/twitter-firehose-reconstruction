import React, { useState } from "react";
import { Typography, Space, Row, Col } from "antd";
import { TokenChart, TokenPercentage } from "../../components/TokenChart";
import AuthButton from "../../components/AuthButton";
import DOMAIN_NAME from "../../config";

const { Title, Paragraph } = Typography;

/**
 * @description Homepage of the application
 * @category Frontend
 * @component
 */
const Home = (props) => {
  const [token_count, set_token_count] = useState(0);
  const { success } = props;

  fetch(`${DOMAIN_NAME}/api/tokencount`)
    .then((data) =>
      data.status === 200
        ? data.text().then((tc) => set_token_count(tc))
        : set_token_count(0)
    )
    .catch(() => {
      set_token_count(0);
    });

  return (
    <Space
      direction="vertical"
      style={{
        height: "100%",
        margin: "0rem",
        width: "100%",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Row gutter={[16, 16]} className="full-height">
        <Col sm={24} md={24} xl={12} style={{ textAlign: "center" }}>
          <Title level={2}>Twitter Firehose Reconstruction</Title>
          <Title
            level={5}
            style={{ textAlign: "center", width: "70%", marginLeft: "15%" }}
          >
            Twitter Firehose is a service that allows companies to get all of
            Twitter's tweets in real time in exchange for a tremendous amount of
            money. At the same time, Twitter offers every app created via the
            developer portal the possibility to execute requests on behalf of
            users. This allows us, with a small number of supporters authorizing
            our app, to capture a relatively large percentage of all tweets
            live.
          </Title>
          <Paragraph
            style={{ textAlign: "center", width: "70%", marginLeft: "15%" }}
          >
            If you like to support the project, please authenticate yourself on
            the following page. By doing so, you enable the retrieval of more
            tweets by sharing your auth token. At the moment we have{" "}
            <b>{token_count} Token</b> wich allows us to retrive
            <b> ~{TokenPercentage({ token_count: token_count })}%</b> of all
            Tweets posted. For more information also check out our{" "}
            <a href="/about">About page</a>.
          </Paragraph>
          {typeof success == "undefined" ? <AuthButton /> : <></>}
        </Col>
        <Col
          sm={24}
          md={24}
          xl={12}
          style={{
            textAlign: "center",
            verticalAlign: "middle",
            width: "100%",
          }}
        >
          <TokenChart token_count={token_count} />
        </Col>
      </Row>
    </Space>
  );
};

export default Home;
