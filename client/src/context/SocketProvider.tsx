import React, { useState, useEffect, useRef, use } from "react";
import { io, Socket } from "socket.io-client";
import { OutreachMessage, ConversationMessage } from "../types/conversations";
import { SocketContext } from "../hooks/useSocket";
import { useLocalStorage } from "../hooks/useLocalStorage";

import axios from "axios";

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || "http://localhost:4000";

export const SocketProvider = ({ children }: { children: React.ReactNode }) => {

    const [chat, setChat] = useState<ConversationMessage[]>([]);
    const [toolNotification, setToolNotification] = useState<string | null>(null);
    const [sequence, setSequence] = useState<OutreachMessage[]>([]);
    const socketRef = useRef<Socket | null>(null);
    const [sessionId, setSessionId] = useLocalStorage<string | null>("session_id", null);
    const [userId, setUserId] = useLocalStorage<string | null>("user_id", null);

    const joinOrCreateSession = async (socket: Socket, existingSessionId?: string) => {
        let currentSessionId = existingSessionId;
        try {
            if (!currentSessionId) {
                // Step 1: Create a new session if no session_id exists
                const response = await axios.post(`http://localhost:4000/api/session`);
                currentSessionId = response.data.session_id as string;
                setSessionId(currentSessionId);
            }
            // Step 2: Join the session
            socket.emit("join_session", { session_id: currentSessionId });

        }
        catch (error) {
            //Error while joining or creating a session
            console.error("Error joining or creating session:", error);
            //fall back- force new session
            setSessionId(null);
            joinOrCreateSession(socket);
        }
    };

    useEffect(() => {
        socketRef.current = io(SOCKET_URL, { autoConnect: false });
        const socket = socketRef.current;

        // Basic events (connect/disconnect/errors only)
        socket.on("connect", () => {
            // Step 2: When socket connects, request new session
            joinOrCreateSession(socket, sessionId ?? undefined);
            setChat((prev) => [...prev, { role: "assistant", content: "Welcome to Helix! How can I help you?" }]);
        });
        socket.on("tool_call", (data) => {
            console.log("Tool call received:");
            setToolNotification(data.message);
        });

        socket.on("chat_message", (data) => {
            setTimeout(() => {
                setToolNotification(null); // Clear toolNotification after delay
                setChat((prev) => [...prev, { role: data.role, content: data.message }]);
            }, 2000);
        });

        socket.on("sequence_updated", (data) => {
            setTimeout(() => {
                setToolNotification(null); // Clear toolNotification after delay
                setSequence(data.sequence);
            }, 2000);
        });

        socket.connect();

        return () => {
            socket.emit("leave_session", { session_id: sessionId });
            socket.disconnect();
        };
    }, []);

    const sendMessage = (msg: string) => {
        // socketRef.current?.emit("leave_session", { session_id: sessionId });
        // socketRef.current?.disconnect();
        // return;
        socketRef.current?.emit("chat_message", { session_id: sessionId, message: msg });
        setChat((prev) => [...prev, { role: "user", content: msg }]);

    };

    const sendSequenceUpdate = (msgId: string, newContent: string) => {
        setSequence((messages) =>
            messages.map((msg) => (msg.id === msgId ? { ...msg, content: newContent } : msg))
        );
        socketRef.current?.emit("update_sequence", { session_id: sessionId, msg_id: msgId, content: newContent });

    };

    return (
        <SocketContext.Provider value={{ sessionId, userId, setUserId, chat, toolNotification, sequence, sendSequenceUpdate, sendMessage }}>
            {children}
        </SocketContext.Provider>
    );


};