import React, { useMemo, useState } from "react";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { ThemeContext } from "../hooks/useThemeContext";

export const ThemeContextProvider = ({ children }: { children: React.ReactNode }) => {
    const [mode, setMode] = useState<"light" | "dark">("light");

    const toggleTheme = () => {
        console.log("Toggling theme...");
        setMode((prevMode) => (prevMode === "light" ? "dark" : "light"));
    };

    const theme = useMemo(
        () =>
            createTheme({
                palette: {
                    mode,
                    ...(mode === "light"
                        ? {
                            background: {
                                default: "#f5f5f5", // Light grey background
                                paper: "#ffffff", // White paper background

                            },
                            text: {
                                primary: "#000000", // Black text
                            },
                        }
                        : {
                            background: {
                                default: "#2c2c2c", // Dark grey background
                                paper: "#3a3a3a", // Slightly lighter grey for paper
                            },
                            text: {
                                primary: "rgba(255, 255, 255, 0.87)",
                            },
                        }),
                },
            }),
        [mode]
    );

    return (
        <ThemeContext.Provider value={{ toggleTheme, mode }}>
            <ThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </ThemeProvider>
        </ThemeContext.Provider>
    );
};