import React from 'react';
import MainRoutes from 'core/components/route/MainRoutes';
import { QueryClient, QueryClientProvider } from 'react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      retryDelay: 1000,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
    },
  },
});

const App: React.FC = () => {
  
  return (
    <div>
      <QueryClientProvider client={queryClient}>
      <MainRoutes />
      </QueryClientProvider>
    </div>
  );
};

export default App;
