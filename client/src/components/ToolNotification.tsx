import { Box, Typography } from '@mui/material';

export default function ToolNotification({ message }: { message: string }) {
    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: 'flex-start',
                mb: 1,
            }}
        >
            <Box
                sx={{
                    px: 2,
                    py: 1,
                    bgcolor: '#e6e0f8',
                    color: '#4a3f78',
                    borderRadius: 2,
                    boxShadow: 2,
                    animation: 'pulse 1s infinite alternate',
                    fontWeight: 'bold',
                    fontSize: 15,
                    maxWidth: '75%',
                    '@keyframes pulse': {
                        from: {
                            boxShadow: '0 0 0px 0px rgba(134, 118, 255, 0.4)',
                            backgroundColor: '#e6e0f8',
                        },
                        to: {
                            boxShadow: '0 0 12px 4px rgba(134, 118, 255, 0.6)',
                            backgroundColor: '#d1c4f9',
                        },
                    },
                }}
            >
                <Typography variant="body1">{message}</Typography>
            </Box>
        </Box>
    );
}