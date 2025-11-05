/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';

const usePromise = <T, F extends (...args: any) => Promise<T>>(
  task: F,
  set?: (value: T) => void
): [(...args: Parameters<F>) => Promise<void>, boolean, Error | undefined, () => void] => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(undefined as Error | undefined);
  const clearError = (): void => setError(undefined);
  const doTask = async (...args: Parameters<F>): Promise<void> => {
    setIsLoading(true);
    try {
      const data = await task(...args as any);
      if (set !== undefined) set(data);
      setError(undefined);
    } catch (error) {
      console.error(error);
      setError(error as Error);
    } finally {
      setIsLoading(false);
    }
  };
  return [doTask, isLoading, error, clearError];
};

export default usePromise;