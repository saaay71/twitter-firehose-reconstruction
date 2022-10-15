import React from "react";
import { Typography } from "antd";
import Home from "../Home/Home";

const { Title } = Typography;

/**
 * @description Homepage of the application
 * @category Frontend
 * @component
 */
const Success = () => (
  <>
    <Title style={{ textAlign: "center", margin: "2rem", color: "#007a9e" }}>
      SUCCESS - THANKS!
    </Title>
    <Home success={true} />
  </>
);

export default Success;
