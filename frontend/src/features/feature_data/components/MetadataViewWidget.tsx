import React from "react";

type MetadataViewWidgetProps = {
  data: any;
  level?: number;
};

const MetadataViewWidget: React.FC<MetadataViewWidgetProps> = ({ data, level = 0 }) => {
  const isObject = (value: any) => typeof value === "object" && value !== null && !Array.isArray(value);

  return (
    <div style={{ paddingLeft: level * 20 }}>
      {isObject(data) ? (
        Object.entries(data)
          .filter(([key]) => key !== 'research_summary')
          .map(([key, value]) => (
            <div key={key} style={{ marginBottom: 10 }}>
              <strong>{key}:</strong>
              <MetadataViewWidget data={value} level={level + 1} />
            </div>
          ))
      ) : Array.isArray(data) ? (
        <ul style={{ paddingLeft: 20 }}>
          {data.map((item, index) => (
            <li key={index}>
              {isObject(item) || Array.isArray(item) ? (
                <MetadataViewWidget data={item} level={level + 1} />
              ) : (
                <a href={item} target="_blank" rel="noopener noreferrer">
                  {item}
                </a>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <span style={{ marginLeft: 8 }}>{data}</span>
      )}
    </div>
  );
};

export default MetadataViewWidget;
