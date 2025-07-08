import React, { useState } from "react";
import { Box, Button, TextField, Dialog, DialogTitle, DialogContent } from "@mui/material";
import axios from "axios";
import { useSocket } from "../hooks/useSocket";

export default function UserInfoForm({ open, onClose }: { open: boolean, onClose: () => void }) {
    const [name, setName] = useState("");
    const [company, setCompany] = useState("");
    const [additionalInfo, setAdditionalInfo] = useState("");
    const [loading, setLoading] = useState(false);
    const { setUserId, sessionId } = useSocket();


    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        setLoading(true);
        const response = await axios.post(`http://localhost:4000/api/session/${sessionId}/user`, {
            name,
            company,
            additionalInfo
        });
        if (response.data) {
            console.log("User info response:", response.data);
            setUserId(response.data);

        } else {
            console.log("Failed to update user information");
        }

        setLoading(false);
        onClose();
    };

    return (
        <Dialog open={open} maxWidth="xs" fullWidth>
            <DialogTitle>Tell us about yourself</DialogTitle>
            <DialogContent>
                <Box p={0} py={2} borderRadius={2} bgcolor="background.paper">
                    <form onSubmit={handleSubmit}>
                        <TextField
                            label="Name"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            fullWidth
                            required
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            label="Company"
                            value={company}
                            onChange={e => setCompany(e.target.value)}
                            fullWidth
                            required
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            label="Additional Info (optional)"
                            value={additionalInfo}
                            onChange={e => setAdditionalInfo(e.target.value)}
                            fullWidth
                            multiline
                            rows={4}
                            sx={{ mb: 2 }}
                        />
                        <Button
                            type="submit"
                            disabled={!name || !company || loading}
                            fullWidth
                            variant="contained"
                        >{loading ? "Saving..." : "Continue"}</Button>
                    </form>
                </Box>
            </DialogContent>
        </Dialog>
    );
}