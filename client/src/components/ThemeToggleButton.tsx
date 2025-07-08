import { IconButton } from "@mui/material";
import { Brightness4, Brightness7 } from "@mui/icons-material";
import { useThemeContext } from "../hooks/useThemeContext";

export default function ThemeToggleButton() {
    const { toggleTheme, mode } = useThemeContext();

    return (
        <IconButton onClick={toggleTheme} color="inherit">
            {mode === "light" ? <Brightness4 /> : <Brightness7 />}
        </IconButton>
    );
}