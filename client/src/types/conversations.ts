export enum MessageType {
    INITIAL_OUTREACH = "initial_outreach",
    FOLLOW_UP = "follow_up",
    MEETING_REQUEST = "meeting_request",
    THANK_YOU = "thank_you",
    REJECTION_HANDLING = "rejection_handling",
    VALUE_ADD = "value_add",
    FINAL_FOLLOW_UP = "final_follow_up",
    OFFER = "offer",
}

export type OutreachMessage = {
    id: string;
    type: MessageType | string;
    subject: string;
    content: string;
    timing: string;
    order: number;
};

export type UserInfo = {
    id?: string;
    name?: string;
    company?: string;
    role?: string;
    industry?: string;
    experience_level?: string;
    location?: string;
    additional_context?: string;
};

export type ConversationMessage = {
    role: "user" | "assistant" | "tool";
    content: string;
    name?: string;
    tool_call_id?: string;
};