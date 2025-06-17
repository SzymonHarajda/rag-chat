import './App.css'

import {
    Chat,
    ChatInput,
    Conversation,
    NewSessionButton,
    Session,
    SessionGroups,
    SessionMessages,
    SessionMessagePanel,
    SessionsList
} from "reachat";

import {useCallback, useEffect, useRef, useState} from "react";
import {chatTheme} from './theme';

function App() {
    const [activeId, setActiveId] = useState<string>();
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [, setCount] = useState<number>(sessions.length + 1);

    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        ws.current = new WebSocket("ws://localhost:8000/chat");

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === "stream") {
                setSessions((prevSessions) => {
                    return prevSessions.map((session) => {
                        if (session.id === data.sessionId) {
                            const updatedConversations = session.conversations.length > 0
                                ? [...session.conversations.slice(0, -1), {
                                    ...session.conversations[session.conversations.length - 1],
                                    response: session.conversations[session.conversations.length - 1].response + (data.word || ''),
                                    updatedAt: new Date()
                                }]
                                : [];

                            return {
                                ...session,
                                conversations: updatedConversations
                            };
                        }
                        return session;
                    });
                });
                if (data.done) {
                    setLoading(false);
                }
            }
        };

        return () => {
            ws.current?.close();
        };
    }, []);

    const handleNewSession = useCallback(() => {
        setSessions(prevSessions => {
            const newId = (prevSessions.length + 1).toString();
            const newSession: Session = {
                id: newId,
                title: `Session #${newId}`,
                createdAt: new Date(),
                updatedAt: new Date(),
                conversations: []
            };
            setActiveId(newId);
            return [...prevSessions, newSession];
        });

        setCount(prev => prev + 1);
    }, []);

    useEffect(() => {
        if (sessions.length === 0) {
            handleNewSession();
        }
    }, [handleNewSession, sessions.length]);

    const handleDelete = (id: string) => {
        const updated = sessions.filter((s) => s.id !== id);
        setSessions([...updated]);
    };

    const handleNewMessage = (message: string) => {
        setLoading(true);
        const curr = sessions.find((s) => s.id === activeId);
        if (curr) {
            const newMessage: Conversation = {
                id: `${curr.id}-${curr.conversations.length}`,
                question: message,
                response: '',
                createdAt: new Date(),
                updatedAt: new Date()
            };
            const updated = {
                ...curr,
                conversations: [...curr.conversations, newMessage]
            };
            setSessions([...sessions.filter((s) => s.id !== activeId), updated]);

            ws.current?.send(JSON.stringify({
                type: "question",
                sessionId: curr.id,
                question: message
            }));
        }
    };

    const handleStopMessage = () => {
        setLoading(false);
        if (ws.current && activeId) {
            ws.current.send(JSON.stringify({
                type: "stop",
                sessionId: activeId
            }));
        }
    };

    return (
        <div className="h-screen w-screen p-2">
            <Chat
                sessions={sessions}
                activeSessionId={activeId}
                isLoading={loading}
                onNewSession={handleNewSession}
                onSelectSession={setActiveId}
                onDeleteSession={handleDelete}
                onSendMessage={handleNewMessage}
                onStopMessage={handleStopMessage}
                theme={chatTheme}
                viewType="console"
            >
                <SessionsList>
                    <NewSessionButton/>
                    <SessionGroups/>
                </SessionsList>
                <SessionMessagePanel>
                    <SessionMessages/>
                    <ChatInput placeholder="Ask anything"/>
                </SessionMessagePanel>
            </Chat>
        </div>
    );
}

export default App
