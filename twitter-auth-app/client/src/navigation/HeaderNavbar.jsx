import { Layout, Menu } from "antd";
import { Link } from "react-router-dom";

const { Header } = Layout;

const HeaderNavbar = (props) => {
  const { menuData, handleHeaderClick } = props;

  return (
    <Header className="header" style={{ padding: "0rem 2.5rem 0rem 2.5rem" }}>
      <Menu theme="dark" mode="horizontal" defaultSelectedKeys={"/"}>
        <Menu.Item key="logo">
          <Link to="/">
            <img
              className="logo"
              style={{ height: "2.6rem" }}
              src="/hpi_logo.png"
              alt="Icon"
            />
          </Link>
        </Menu.Item>
        {menuData.map((menuEntry) => (
          <Menu.Item key={menuEntry.link}>
            {menuEntry.title}
            <Link to={menuEntry.link} onClick={handleHeaderClick} />
          </Menu.Item>
        ))}
      </Menu>
    </Header>
  );
};

HeaderNavbar.propTypes = {};

export default HeaderNavbar;
