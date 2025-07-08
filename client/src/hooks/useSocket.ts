import { createContext, useContext } from "react";
import { OutreachMessage, ConversationMessage } from "../types/conversations";


interface SocketCtxType {
    sessionId: string | null;
    userId: string | null;
    setUserId: (userId: string | null) => void;
    chat: ConversationMessage[];
    // setChat: React.Dispatch<React.SetStateAction<ConversationMessage[]>>;
    toolNotification: string | null;
    sequence: OutreachMessage[];
    // setSequence: React.Dispatch<React.SetStateAction<OutreachMessage[]>>;
    sendSequenceUpdate: (msgId: string, newContent: string) => void;
    sendMessage: (msg: string) => void;
    // socket: Socket | null;
}

export const SocketContext = createContext({} as SocketCtxType);

export const useSocket = () => {
    return useContext(SocketContext);
};