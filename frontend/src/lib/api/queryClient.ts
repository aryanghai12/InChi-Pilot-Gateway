import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./types";

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          if (error instanceof ApiError) {
            // Never retry unauthenticated or permission denied errors
            if ([401, 403, 404].includes(error.status)) {
              return false;
            }
          }
          return failureCount < 2;
        },
      },
      mutations: {
        retry: false,
      },
    },
  });
}
