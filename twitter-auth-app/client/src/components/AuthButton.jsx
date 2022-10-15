import React from "react";
import { Button, Row } from "antd";

/**
 * @description Homepage of the application
 * @category Frontend
 * @component
 */
const AuthButton = () => (
  <Row style={{ width: "100%" }}>
    <a href="/twitter/authorize" style={{ margin: "auto" }}>
      <Button type="primary" style={{ width: "100%" }}>
        Provide Twitter API-Token
      </Button>
    </a>
  </Row>
);
export default AuthButton;
