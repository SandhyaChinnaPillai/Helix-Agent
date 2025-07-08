import { Box, Paper } from "@mui/material";
import ChatPanel from "./ChatPanel";
import SequencePanel from "./SequencePanel";
import ThemeToggleButton from "./ThemeToggleButton";
import { useSocket } from "../hooks/useSocket";
import { useState } from "react";
import UserInfoForm from "./UserInfoForm";

export default function HelixComponent() {

    const { userId } = useSocket();
    const [modalOpen, setModalOpen] = useState(userId === null);
    return (
        <>
            <Box display="flex" width="100%" height="100vh" >
                <Paper elevation={3} sx={{ width: "35vw", display: "flex", flexDirection: "column", height: "100vh" }}>
                    <ChatPanel />
                </Paper>
                <Box flex={1} display="flex" flexDirection="column" height="100vh" minHeight={0}>
                    <SequencePanel />
                </Box>
                <Box
                    sx={{
                        position: "absolute",
                        bottom: 16,
                        right: 16,
                        zIndex: 1000, // Ensure it appears above other elements
                    }}
                >
                    <ThemeToggleButton />
                </Box>
            </Box>
            {modalOpen && (
                <UserInfoForm open={modalOpen} onClose={() => {
                    setModalOpen(false);
                }} />
            )
            }
        </>
    );
}