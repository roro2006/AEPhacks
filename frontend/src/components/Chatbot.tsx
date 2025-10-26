import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Sparkles, Zap } from "lucide-react";
import type { WeatherParams } from "../services/api";
import "./Chatbot.css";

interface AgentInsights {
  summary: string;
  issues_count: number;
  critical_count: number;
  high_count: number;
  issues: any[];
}

interface Message {
  id: string;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
  queryType?: string;
  aiPowered?: boolean;
  tokens?: number;
  agentInsights?: AgentInsights;
}

interface ChatbotProps {
  weather: WeatherParams;
  inSidebar?: boolean;
}

const SUGGESTED_QUESTIONS = [
  "What's the current grid status?",
  "Are there any overloaded lines?",
  "What if temperature increases by 10°C?",
  "Which lines are most sensitive to weather?",
];

export default function Chatbot({ weather, inSidebar = false }: ChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Hello! I'm your AI-powered Grid Monitor Assistant. I can explain grid data, predict impacts of variable changes, and help you make informed decisions. Try asking me something!",
      sender: "bot",
      timestamp: new Date(),
      aiPowered: true,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: textToSend,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setShowSuggestions(false);

    try {
      const response = await fetch("http://localhost:5001/api/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: textToSend,
          weather: {
            ambient_temp: weather.ambient_temp,
            wind_speed: weather.wind_speed,
            wind_angle: weather.wind_angle,
            sun_time: weather.sun_time,
            date: weather.date,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response from chatbot");
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        sender: "bot",
        timestamp: new Date(),
        queryType: data.query_type,
        aiPowered: data.ai_powered,
        tokens: data.tokens,
        agentInsights: data.agent_insights,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I encountered an error. Please make sure the backend server is running and the API key is configured.",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Sidebar mode - integrated into tab
  if (inSidebar) {
    return (
      <div className="chat-sidebar-content">
        {/* Messages Container */}
        <div className="chat-messages chat-messages-sidebar">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-wrapper ${message.sender === "user" ? "message-user" : "message-bot"}`}
            >
              {message.sender === "bot" && (
                <div className="message-avatar">
                  <Zap size={14} />
                </div>
              )}
              <div className="message-bubble">
                <div className="message-text">{message.text}</div>
                {message.agentInsights && (
                  <div className="agent-insights-badge" style={{
                    marginTop: '8px',
                    padding: '8px',
                    background: message.agentInsights.critical_count > 0 ? '#fee' : '#ffe',
                    borderRadius: '4px',
                    fontSize: '12px',
                    borderLeft: `3px solid ${message.agentInsights.critical_count > 0 ? '#f44' : '#fa0'}`
                  }}>
                    <strong>⚠️ Agent Alert:</strong> {message.agentInsights.summary}
                  </div>
                )}
                <div className="message-meta">
                  <span className="message-time">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                  {message.aiPowered && (
                    <span className="message-ai-badge">
                      <Sparkles size={10} />
                      AI
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-wrapper message-bot">
              <div className="message-avatar">
                <Loader2 size={14} className="spin-animation" />
              </div>
              <div className="message-bubble message-loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          {/* Suggested Questions */}
          {showSuggestions && messages.length === 1 && (
            <div className="suggestions-container">
              <p className="suggestions-title">Try asking:</p>
              <div className="suggestions-grid">
                {SUGGESTED_QUESTIONS.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="suggestion-chip"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about the grid..."
              disabled={loading}
              className="chat-input"
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className={`chat-send-btn ${input.trim() && !loading ? "chat-send-btn-active" : ""}`}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Standalone floating mode (not used anymore, but keeping for compatibility)
  return null;
}
