import express from 'express';
import http from 'http';
import { WebSocketServer } from 'ws';

const app = express();
const port = 3001;

app.get('/', (req, res) => {
    res.send('Server is running!');
});

const server = http.createServer(app);
const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
    console.log('WebSocket client connected');

    let interval = null;

    ws.on('message', (data) => {
        try {
            const msg = JSON.parse(data.toString());
            console.log('Received:', msg);

            if (msg.type === 'question') {
                const answer = `This is a sample answer to the question: ${msg.question}`;
                const words = answer.split(' ');
                let index = 0;

                if (interval) {
                    clearInterval(interval);
                }

                interval = setInterval(() => {
                    if (index < words.length) {
                        ws.send(JSON.stringify({
                            type: 'stream',
                            sessionId: msg.sessionId,
                            word: words[index],
                            done: false
                        }));
                        index++;
                    } else {
                        clearInterval(interval);
                        ws.send(JSON.stringify({
                            type: 'stream',
                            sessionId: msg.sessionId,
                            done: true
                        }));
                    }
                }, 300);
            }

            if (msg.type === 'stop') {
                if (interval) {
                    clearInterval(interval);
                    interval = null;
                    ws.send(JSON.stringify({
                        type: 'stopped',
                        sessionId: msg.sessionId,
                        message: 'The response has been stopped.'
                    }));
                }
            }

        } catch (err) {
            console.error('Invalid message:', err);
        }
    });
});

server.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
    console.log(`WebSocket is available at ws://localhost:${port}`);
});
