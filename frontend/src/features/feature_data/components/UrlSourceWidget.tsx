import React from 'react';
import { useUrlValidation } from '../hooks/useUrlValidation';

interface UrlSourceWidgetProps {
  source: string;
  urlValidationScore?: any;
  showScore?: boolean;
}

// Cache for validated URLs
const urlValidationCache = new Map<string, { score: number; timestamp: number }>();
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

const UrlSourceWidget: React.FC<UrlSourceWidgetProps> = ({ source, urlValidationScore, showScore = true }) => {
  const getHostname = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.replace(/^www\./, '');
    } catch {
      return null;
    }
  };

  const getFullUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      const protocol = urlObj.protocol === 'https:' ? 'https://www.' : 'http://www.';
      return protocol + urlObj.hostname.replace(/^www\./, '');
    } catch {
      return null;
    }
  };

  const getCachedValidation = (url: string) => {
    const cached = urlValidationCache.get(url);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached;
    }
    return null;
  };

  const hostname = getHostname(source);
  const fullUrl = getFullUrl(source);
  const cachedValidation = fullUrl ? getCachedValidation(fullUrl) : null;
  const { data: validationData, isLoading } = useUrlValidation(fullUrl, cachedValidation, urlValidationScore);

  
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'success';
    if (score >= 5) return 'warning';
    return 'danger';
  };

  const isValidUrl = (url: string) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const getBaseUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname.replace(/^www\./, '');
      return hostname.charAt(0).toUpperCase() + hostname.slice(1);
    } catch {
      return url;
    }
  };

  if (!isValidUrl(source)) {
    return <span>{source}</span>;
  }


  return (
    <div className="d-flex align-items-center gap-2">
      {showScore && (
        <>
          {urlValidationScore ? (
            <span
          title={"This score is for the source URL. It is based on the domain reputation, content quality, and other factors."}
          className={`badge bg-${getScoreColor(urlValidationScore)}`}>
          {urlValidationScore}
        </span>
        ) : (
          <>
            {!isLoading && validationData && (
              <span 
                title={"This score is for the source URL. It is based on the domain reputation, content quality, and other factors."}
                className={`badge bg-${getScoreColor(validationData.score)}`}>
                {validationData.score}/10
              </span>
            )}
          </>
        )}
      </>
      )}
      <a 
        href={source} 
        target="_blank" 
        rel="noopener noreferrer"
        className="text-decoration-none"
      >
        {getBaseUrl(source)}
      </a>
      
    </div>
  );
};

export default UrlSourceWidget; 