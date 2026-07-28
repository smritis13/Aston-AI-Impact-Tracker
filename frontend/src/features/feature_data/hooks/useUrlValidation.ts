import axios from "axios";
import { useQuery } from "react-query";
import { ContentHttpService } from "../services";

interface UrlValidationResponse {
  score: number;
  baseUrl: string;
}

interface CachedValidation {
  score: number;
  timestamp: number;
}

export const useUrlValidation = (url: string | null, cachedValidation: CachedValidation | null, urlValidationScore: number | null) => {
  return useQuery<UrlValidationResponse | null>({
    queryKey: ["urlValidation", url] as const,
    queryFn: async () => {
      if (!url) return null;
      if (urlValidationScore !== null) {
        return { score: urlValidationScore, baseUrl: url };
      }
      if (cachedValidation) {
        return { score: cachedValidation.score, baseUrl: url };
      }
      const response = await ContentHttpService.validateUrl(url);
      return response as UrlValidationResponse;
    },
    enabled: !!url,
  });
}; 