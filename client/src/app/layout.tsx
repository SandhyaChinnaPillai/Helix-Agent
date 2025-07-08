"use client";

import { ThemeContextProvider } from "../context/ThemeContextProvider";

export default function RootLayout({
    children
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body style={{ overflow: "hidden" }}>
                <ThemeContextProvider>
                    {children}
                </ThemeContextProvider>
            </body>
        </html>
    );
}
