import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './App.css';

// Connect to backend via Vite proxy
const socket = io('/', {
  transports: ['websocket', 'polling'],
  autoConnect: true
});

function App() {
  const [userMessages, setUserMessages] = useState([]);
  const [agentMessages, setAgentMessages] = useState([]);
  const [input, setInput] = useState('');
  const userEndRef = useRef(null);
  const agentEndRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    userEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [userMessages]);

  useEffect(() => {
    agentEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentMessages]);

  // Socket listeners
  useEffect(() => {
    socket.on('connect', () => {
      console.log('✅ Connected to server');
    });

    socket.on('init_history', (data) => {
      setUserMessages(data.user);
      setAgentMessages(data.agent);
    });

    socket.on('new_user_message', (data) => {
      // Detect if the message is from Commander (contains 'Commander')
      if (data.text.includes('Commander')) {
        setUserMessages(prev => [...prev, { role: 'leader', text: data.text }]);
      } else {
        setUserMessages(prev => [...prev, { role: 'user', text: data.text }]);
      }
    });

    socket.on('new_agent_message', (data) => {
      setAgentMessages(prev => [...prev, data.text]);
    });

    return () => {
      socket.off('connect');
      socket.off('init_history');
      socket.off('new_user_message');
      socket.off('new_agent_message');
    };
  }, []);

  const sendMessage = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    socket.emit('user_message', input);
    setInput('');
  };

  return (
    <div id="app">
      <header>
        <h1>🏭 Pixel Developer Colony</h1>
        <div id="agent-status">
          <span className="dot online"></span> 6 Agents Online
        </div>
      </header>

      <main>
        {/* LEFT COLUMN: USER CHAT */}
        <section id="user-chat">
          <div className="chat-header">
            <span>💬 User Terminal</span>
            <small>(Only you & Commander)</small>
          </div>
          <div className="messages" id="user-messages">
            {userMessages.map((msg, idx) => (
              <div
                key={idx}
                className={msg.role === 'user' ? 'user-bubble' : 'leader-bubble'}
              >
                {msg.text}
              </div>
            ))}
            <div ref={userEndRef} />
          </div>
          <form className="input-area" onSubmit={sendMessage}>
            <input
              type="text"
              id="user-input"
              placeholder="Type your request... e.g. Build a calculator"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button id="send-btn" type="submit">Send</button>
          </form>
        </section>

        {/* RIGHT COLUMN: AGENT WAR ROOM */}
        <section id="agent-chat">
          <div className="chat-header">
            <span>🤖 Agent War Room</span>
            <small>(Read-only - Watch agents collaborate)</small>
          </div>
          <div className="messages" id="agent-messages">
            {agentMessages.map((msg, idx) => (
              <div key={idx} className="agent-bubble">
                {msg}
              </div>
            ))}
            <div ref={agentEndRef} />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;