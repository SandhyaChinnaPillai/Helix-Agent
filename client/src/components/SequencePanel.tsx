import { Box, Typography } from "@mui/material";
import { useSocket } from "../hooks/useSocket";
import SequenceMessageItem from "./SequenceMessageItem";

export default function SequencePanel() {
    const { sequence, sendSequenceUpdate } = useSocket();

    const updateMessage = (id: string, newContent: string) => {
        sendSequenceUpdate(id, newContent);
    };

    return (
        <Box px={4} py={2} overflow="auto" height="100%" >
            <Typography variant="h6">Sequence</Typography>
            {sequence.map((msg) => (
                <SequenceMessageItem
                    key={msg.id}
                    message={msg}
                    onUpdate={(newContent) => updateMessage(msg.id, newContent)}
                />
            ))}
        </Box>
    );
}
