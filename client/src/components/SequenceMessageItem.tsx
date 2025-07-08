import { useState } from "react";
import { Box, Typography, IconButton, TextField, Paper, Stack, useTheme } from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import SaveIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import EmailIcon from "@mui/icons-material/Email";
import { OutreachMessage } from "../types/conversations";

export default function SequenceMessageItem({ message, onUpdate }: { message: OutreachMessage, onUpdate: (newContent: string) => void }) {

    const [editing, setEditing] = useState(false);
    const [content, setContent] = useState(message.content);
    const theme = useTheme();

    const handleSave = () => {
        if (content.trim() === "") return;
        onUpdate(content);
        setEditing(false);
    }

    const handleCancel = () => {
        setContent(message.content);
        setEditing(false);
    }

    return (
        <Paper sx={{ p: 2, mb: 1, borderRadius: 2, position: "relative" }}>
            <Stack direction="row" alignItems="center" justifyContent="space-between">
                <Typography variant="subtitle2">{message.order} : {message.subject}</Typography>
                {!editing && (<IconButton size="small" sx={{ color: theme.palette.text.primary }} onClick={() => setEditing(!editing)}>
                    <EditIcon />
                </IconButton>)}
            </Stack>
            {editing ? (
                <Stack direction="row" spacing={1} mt={1}>
                    <TextField
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        fullWidth
                        multiline
                        rows={20}
                        variant="outlined"
                        size="small"
                        sx={{ flexGrow: 1 }}
                    />
                    <IconButton color="primary" size="small" onClick={handleSave} disabled={!content.trim()}>
                        <SaveIcon />
                    </IconButton>
                    <IconButton color="error" size="small" onClick={handleCancel} >
                        <CloseIcon />
                    </IconButton>
                </Stack>
            ) : (
                <Typography variant="body2" sx={{ whiteSpace: "pre-line", mt: 1 }}>
                    {content}
                </Typography>
            )}
            <Box sx={{
                position: "absolute",
                bottom: 8,
                right: 8,
            }}>
                <EmailIcon />
            </Box>
        </Paper >
    )
}