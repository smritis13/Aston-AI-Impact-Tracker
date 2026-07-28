import React from 'react';
import UrlSourceWidget from './UrlSourceWidget';

export interface JsonStructure {
  [key: string]: string;
}

export const cleanJsonString = (str: string): string => {
  // Remove markdown code block markers and language identifier
  return str.replace(/```json\n?|\n?```/g, '').trim();
};

export const isJsonArray = (str: string): boolean => {
  try {
    const cleanedStr = cleanJsonString(str);
    const parsed = JSON.parse(cleanedStr);
    return Array.isArray(parsed);
  } catch {
    return false;
  }
};

const isUrlField = (header: string): boolean => {
  return header.toLowerCase() === 'source' || header.toLowerCase().includes('url')|| header.toLowerCase().includes('link');
};

export const JsonTable: React.FC<{ data: any[], structure?: JsonStructure }> = ({ data, structure }) => {
  if (!data.length) return null;

  const headers = structure ? Object.keys(structure) : Object.keys(data[0]);

  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header.replace(/_/g, ' ')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index}>
              {headers.map((header) => (
                <td key={header}>
                  {isUrlField(header) ? (
                    <UrlSourceWidget source={row[header]} />
                  ) : (
                    row[header]
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}; 