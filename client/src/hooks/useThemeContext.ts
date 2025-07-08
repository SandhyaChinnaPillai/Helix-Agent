import { createContext, useContext } from "react";


export const ThemeContext = createContext({
    toggleTheme: () => { },
    mode: "light",
});

export const useThemeContext = () => useContext(ThemeContext);