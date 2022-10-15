import { twitterPercentageData } from "../assets/diagramData";
import Plot from "react-plotly.js";
import { useState, useRef, useEffect } from "react";
import { useWindowSize } from "../helpers/useWindowSize";

// make sure parent container have a defined height when using
// responsive component, otherwise height will be 0 and
// no chart will be rendered.
// website examples showcase many properties,
// you'll often use just a few of them.

export const TokenChart = ({ token_count }) => {
  const rounded_token_count =
    token_count <= 50
      ? Math.round(token_count)
      : Math.round(token_count / 10) * 10;
  const [height, setHeight] = useState(null);
  const [width, setWidth] = useState(null);
  const divRef = useRef(null);
  const screenSize = useWindowSize();
  useEffect(() => {
    if (divRef.current !== null) {
      setHeight(divRef.current.getBoundingClientRect().height);
      setWidth(divRef.current.getBoundingClientRect().width);
    }
  }, [divRef, screenSize]);

  return (
    <div ref={divRef} style={{ maxWidth: "100vw" }}>
      <Plot
        data={[
          {
            x: twitterPercentageData.map((e) =>
              e.x <= rounded_token_count ? e.x : null
            ),
            y: twitterPercentageData.map((e) =>
              e.x <= rounded_token_count ? e.y : null
            ),
            marker: { color: "#f6a800" },
            mode: "lines",
            fill: "tozeroy",
            name: "",
          },
          {
            x: twitterPercentageData.map((e) =>
              e.x >= rounded_token_count ? e.x : null
            ),
            y: twitterPercentageData.map((e) =>
              e.x >= rounded_token_count ? e.y : null
            ),
            marker: { color: "#b1063a" },
            mode: "lines",
            fill: "tozeroy",
            name: "",
            labels: "test",
          },
        ]}
        style={{
          width: width ? width + "px" : "100%",
          height: "50vh",
        }}
        useResizeHandler={true}
        config={{ responsive: true }}
        layout={{
          showlegend: false,
          xaxis: { title: "Number of Tokens" },
          yaxis: { title: "Live Stream Coverage (%)" },
        }}
      />
    </div>
  );
};

export const TokenPercentage = ({ token_count }) => {
  const percentage_floor = twitterPercentageData.find(
    (e) => e.x === Math.floor(token_count / 10) * 10
  ).y;
  const percentage_ceil = twitterPercentageData.find(
    (e) => e.x === Math.ceil(token_count / 10) * 10
  ).y;
  const percentage =
    percentage_floor +
    ((percentage_ceil - percentage_floor) * (token_count % 10)) / 10;
  const percentage_rounded = Math.round(percentage * 100) / 100;

  return percentage_rounded;
};
