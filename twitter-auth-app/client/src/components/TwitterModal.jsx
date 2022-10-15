import React from "react";
import { Button, Typography, Space, Modal, Col, Row } from "antd";

const { Title } = Typography;

/**
 * @description Homepage of the application
 * @category Frontend
 * @component
 */
const TwitterModal = (props) => {
  if (!props.visible) return null;

  return (
    <>
      <Modal
        title="" /* "Donate your Token or Login" */
        visible={true}
        onCancel={props.onClose}
        footer={<Button onClick={props.onClose}>Close</Button>}
      >
        <Space direction="vertical" style={{ width: "100%" }}>
          <Title level={3}>Donate your Token or Login</Title>

          <Row gutter={[16, 16]} style={{ width: "100%" }}>
            <Col sm={24} md={12}>
              First time on our page?
            </Col>
            <Col sm={24} md={12}>
              <a href="/twitter/authorize">
                <Button type="primary" style={{ width: "100%" }}>
                  Authorize
                </Button>
              </a>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ width: "100%" }}>
            <Col sm={24} md={12}>
              Already authorized?
            </Col>
            <Col sm={24} md={12}>
              <a href="/twitter/authenticate">
                <Button type="primary" style={{ width: "100%" }}>
                  Log In (Authenticate)
                </Button>
              </a>
            </Col>
          </Row>
        </Space>
      </Modal>
    </>
  );
};

export default TwitterModal;
