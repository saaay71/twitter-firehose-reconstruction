const CracoLessPlugin = require("craco-less");

const customizedTheme = {
  "@primary-color": "#b1063a",
  "@link-color": "#dd6108",
  "@success-color": "#f6a800",
  "@warning-color": "#f6a800",
  "@font-family": "Lato, sans-serif",
};

module.exports = {
  plugins: [
    {
      plugin: CracoLessPlugin,
      options: {
        lessLoaderOptions: {
          lessOptions: {
            modifyVars: customizedTheme,
            javascriptEnabled: true,
          },
        },
      },
    },
  ],
};
