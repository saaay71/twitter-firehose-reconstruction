import React, { useState } from "react";
import { BrowserRouter, Route, Switch } from "react-router-dom";
import { Layout } from "antd";
import Home from "./pages/Home/Home";
import Privacy from "./pages/Privacy/Privacy";
import About from "./pages/About/About";
import Dashboard from "./pages/Dashboard/Dashboard";
import AuthError from "./pages/AuthError/AuthError";
import Error from "./pages/Error/Error";
import HeaderNavbar from "./navigation/HeaderNavbar";
import Success from "./pages/Success/Success";
import menuData from "./navigation/menuData.json";

import "./App.less";

const { Content, Footer } = Layout;

/**
 * @description Route component of the application
 * @category Frontend
 * @component
 */
const App = () => {
  const [refresh, setRefresh] = useState(true);

  return (
    <BrowserRouter>
      <Layout className="layout">
        <HeaderNavbar
          menuData={menuData}
          handleHeaderClick={() => setRefresh(!refresh)}
        />

        <Content className="site-layout-content">
          <Switch>
            <Route path="/" component={Home} exact />
            <Route path="/privacy" component={Privacy} exact />
            <Route path="/success" component={Success} exact />
            <Route path="/about" component={About} exact />
            <Route path="/dashboard" component={Dashboard} exact />
            <Route path="/autherror" component={AuthError} exact />
            <Route component={Error} />
          </Switch>
        </Content>

        <Footer style={{ textAlign: "center" }}>
          <div> Twitter Firehose Reconstruction © 2022 </div>
          <div>
            Created with ❤️ by Lukas Hüller, Tim Kuffner and Bjarne Sievers
            <a href="https://hpi.de"> @HPI </a>
            Potsdam, Germany
          </div>
        </Footer>
      </Layout>
    </BrowserRouter>
  );
};

export default App;
