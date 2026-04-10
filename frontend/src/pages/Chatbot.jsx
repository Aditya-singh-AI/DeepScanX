import { useState, useEffect, useRef } from 'react';
import './Chatbot.css';

const SYSTEM_PROMPT = `You are DeepScanX, an intelligent clinical AI assistant embedded within the DeepScanX AI radiology platform. Your role is to help pathology researchers, medical students, and doctors understand AI-driven histopathology and radiology results.

Guidelines:
- Answer questions about cancer types, tissue classification, and AI predictions clearly and accurately
- When given a diagnosis context, explain it in simple, compassionate language
- Always emphasize that AI predictions are for research/educational purposes ONLY and not a replacement for professional medical advice
- Never provide a definitive medical diagnosis
- Be concise but thorough — aim for 2–4 paragraph answers
- Use bullet points where helpful for readability
- If asked non-medical questions, gently redirect to the platform's purpose`;

export default function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      content: `Hello! I'm **DeepScanX**, your clinical AI assistant.\n\nI can help you understand AI-driven cancer detection results, explain histopathology concepts, and answer medical research questions.\n\nTry one of these:`
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load Puter.js
    if (!window.puter) {
      const script = document.createElement('script');
      script.src = 'https://js.puter.com/v2/';
      document.head.appendChild(script);
      return () => { try { document.head.removeChild(script); } catch {} };
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const parseMarkdown = (text) => {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/^• (.+)/gm, '<li>$1</li>')
      .replace(/^- (.+)/gm, '<li>$1</li>')
      .replace(/^(\d+)\. (.+)/gm, '<li>$2</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  };

  const handleSend = async (text) => {
    if (!text || !text.trim() || isLoading) return;
    
    const userMsg = text.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsLoading(true);

    try {
      const fullPrompt = `${SYSTEM_PROMPT}\n\nUser question: ${userMsg}`;
      const response = await window.puter.ai.chat(fullPrompt);
      
      let reply = '';
      if (typeof response === 'string') {
          reply = response;
      } else if (response && response.message && response.message.content) {
          reply = response.message.content;
      } else if (response && response.toString) {
          reply = response.toString();
      } else {
          reply = 'I received a response but could not parse it. Please try again.';
      }
      
      setMessages(prev => [...prev, { role: 'bot', content: reply }]);
    } catch (err) {
      console.error('Puter AI error:', err);
      setMessages(prev => [...prev, { 
        role: 'error', 
        content: `⚠️ Could not get a response right now.\n<small style="color:#666">${err.message || String(err)}</small>\n\nPlease try again in a moment.` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestions = [
    '💊 What does IDC+ mean?',
    '🔬 Explain Grad-CAM heatmaps',
    '🫁 What is Invasive Ductal Carcinoma?',
    '🧬 Difference between benign & malignant?'
  ];

  return (
    <div className="chatbot-page">
      <div className="chatbot-header">
        <div className="module-badge"><span className="pulse"></span> Clinical AI Assistant</div>
        <h1 style={{ fontFamily: 'var(--font2)', fontSize: '2rem', fontWeight: 700 }}>
          DeepScanX <span style={{ color: 'var(--crimson-l)' }}>AI Chat</span>
        </h1>
        <p style={{ color: 'var(--gray)', fontSize: '.95rem' }}>
          Ask medical questions, get clinical guidance, and explore diagnostic insights. Powered by Puter AI.
        </p>
      </div>

      <div className="chatbot-main-container">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`msg-wrapper ${msg.role === 'user' ? 'user' : 'bot'} ${msg.role === 'error' ? 'error' : ''}`}>
              <div className="msg-avatar">{msg.role === 'user' ? '👤' : '🩺'}</div>
              <div className="msg-bubble">
                <div dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content) }}></div>
                {i === 0 && msg.role === 'bot' && (
                  <div className="suggestions">
                    {suggestions.map((s, idx) => (
                      <span key={idx} className="suggestion" onClick={() => handleSend(s.replace(/^[^a-zA-Z]+/, '').trim())}>
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="msg-wrapper bot">
              <div className="msg-avatar">🩺</div>
              <div className="msg-bubble" style={{ padding: '16px' }}>
                <div className="typing-dots"><span></span><span></span><span></span></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-bar">
          <input
            type="text"
            className="input-field"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if(e.key === 'Enter') handleSend(input); }}
            placeholder="Ask about a diagnosis, cancer type, or AI explanation…"
            disabled={isLoading}
          />
          <button 
            className="send-btn"
            onClick={() => handleSend(input)}
            disabled={isLoading || !input.trim()}
          >
            {isLoading ? <span style={{ fontSize: '1rem' }}>⏳</span> : <i className="fas fa-paper-plane"></i>}
          </button>
        </div>
        <div style={{ background: 'var(--surface)', borderTop: '1px solid var(--border)' }}>
          <p style={{ textAlign: 'center', fontSize: '11px', color: 'var(--gray)', padding: '0.6rem 0', margin: 0 }}>
            ⚠️ DeepScanX is for research & educational purposes only. Not a substitute for clinical diagnosis.
          </p>
        </div>
      </div>
    </div>
  );
}
