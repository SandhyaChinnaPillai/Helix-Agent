import { useEffect, useState } from "react";

export const useLocalStorage = <T>(key: string, initialValue: T): [T, (value: T) => void] => {
    const [storedValue, setStoredValue] = useState(() => {
        try {
            // Retrieve from localStorage
            const item = window.localStorage.getItem(key);

            // Parse stored json or if none return initialValue
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            // If error also return initialValue
            return initialValue;
        }
    });

    useEffect(() => {
        // Retrieve from localStorage
        const item = window.localStorage.getItem(key);

        if (item) {
            setStoredValue(JSON.parse(item));
        }
    }, [key]);

    const setValue = (value: T) => {
        // Save state
        setStoredValue(value);
        // Save to localStorage
        window.localStorage.setItem(key, JSON.stringify(value));
    };

    return [storedValue, setValue];
};