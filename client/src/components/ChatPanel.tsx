import { Box, Typography, Divider, TextField, IconButton, useTheme } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import React, { useRef, useEffect, useState } from "react";
import MessageBubble from "./MessageBubble";
import { useSocket } from "../hooks/useSocket";
import ToolNotification from "./ToolNotification";

export default function ChatPanel() {
    const { chat, sendMessage, toolNotification } = useSocket();
    const [input, setInput] = useState("");
    const endRef = useRef<HTMLDivElement>(null);
    const theme = useTheme();

    useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chat]);

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;
        sendMessage(input);
        setInput("");
    };

    return (
        <Box display="flex" flexDirection="column" height="100%" px={2} py={2} overflow="hidden">
            <Typography variant="h6" gutterBottom>AI Recruiter Assistant</Typography>
            <Divider sx={{ mb: 1 }} />
            <Box flex={1} overflow="auto" mb={1} pr={1}>
                {chat.map((msg, idx) => (
                    <MessageBubble key={idx} {...msg} />
                ))}
                {toolNotification && (
                    <ToolNotification message={toolNotification} />
                )}
                <div ref={endRef} />
            </Box>
            <form onSubmit={handleSend}>
                <Box display="flex">
                    <TextField
                        value={input}
                        variant="standard"
                        size="medium"
                        InputProps={{ disableUnderline: true }}
                        fullWidth
                        placeholder="Chat here.."
                        onChange={e => setInput(e.target.value)}
                        sx={{ height: "75px", p: "5px", bgcolor: theme.palette.background.default, borderRadius: 4 }}
                    />
                    <IconButton type="submit" color="primary" disabled={!input.trim()}><SendIcon /></IconButton>
                </Box>
            </form>
        </Box>
    );
}
