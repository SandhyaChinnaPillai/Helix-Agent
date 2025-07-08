import { Paper, Typography, Box } from "@mui/material";
import { ConversationMessage } from "../types/conversations";

const bubbleColor = {
    user: "#1976d2",
    assistant: "#ffffff",
    tool: "#fff6d1",
} as any;
const textColor = {
    user: "#fff",
    assistant: "#222",
    tool: "#856100",
} as any;

export default function MessageBubble({ role, content }: ConversationMessage) {
    return (
        <Box display="flex" justifyContent={role === "user" ? "flex-end" : "flex-start"} my={.5}>
            <Paper
                sx={{
                    background: bubbleColor[role],
                    color: textColor[role],
                    p: 1.2,
                    px: 2,
                    borderRadius: 2,
                    maxWidth: "90%",
                    fontSize: 15,
                    fontWeight: 400,
                    boxShadow: "none",
                }}
            >
                <Typography variant="body2" sx={{ whiteSpace: "pre-line" }}>{content}</Typography>
            </Paper>
        </Box>
    );
}