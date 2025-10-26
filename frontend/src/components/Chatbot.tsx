import { useState, useRef, useEffect } from "react";
import { Send, MessageCircle, X, Loader2 } from "lucide-react";
import type { WeatherParams } from "../services/api";

interface Message {
  id: string;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
  queryType?: string;
  aiPowered?: boolean;
  tokens?: number;
}

interface ChatbotProps {
  weather: WeatherParams;
}

const SUGGESTED_QUESTIONS = [
  "What's the current grid status?",
  "Are there any overloaded lines?",
  "What if temperature increases by 10°C?",
  "Explain the loading percentage metric",
  "Which lines are most sensitive to weather?",
];

export default function Chatbot({ weather }: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      text: "Hello! I'm your AI-powered Grid Monitor Assistant. I can explain grid data, predict impacts of variable changes, and help you make informed decisions. Try asking me something or click a suggestion below!",
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
      const response = await fetch("http://localhost:5000/api/chatbot", {
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

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            position: "fixed",
            bottom: "2rem",
            right: "2rem",
            width: "60px",
            height: "60px",
            borderRadius: "50%",
            background:
              "linear-gradient(135deg,rgb(197, 197, 197) 0%,rgb(208, 195, 222) 100%)",
            border: "none",
            boxShadow: "0 4px 12px rgba(102, 126, 234, 0.4)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.3s ease",
            zIndex: 1000,
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = "scale(1.1)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = "scale(1)";
          }}
        >
          <MessageCircle size={28} color="white" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          style={{
            position: "fixed",
            bottom: "2rem",
            right: "2rem",
            width: "400px",
            height: "600px",
            background: "white",
            borderRadius: "16px",
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.15)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            zIndex: 1000,
          }}
        >
          {/* Header */}
          <div
            style={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              color: "white",
              padding: "1rem 1.5rem",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div
              style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}
            >
              <MessageCircle size={24} />
              <div>
                <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 600 }}>
                  Grid Assistant
                </h3>
                <p style={{ margin: 0, fontSize: "0.75rem", opacity: 0.9 }}>
                  Always here to help
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: "transparent",
                border: "none",
                color: "white",
                cursor: "pointer",
                padding: "0.25rem",
                display: "flex",
                alignItems: "center",
                transition: "opacity 0.2s",
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.opacity = "0.7";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.opacity = "1";
              }}
            >
              <X size={24} />
            </button>
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "1.5rem",
              background: "#f9fafb",
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
            }}
          >
            {messages.map((message) => (
              <div
                key={message.id}
                style={{
                  display: "flex",
                  justifyContent:
                    message.sender === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    maxWidth: "80%",
                    padding: "0.75rem 1rem",
                    borderRadius:
                      message.sender === "user"
                        ? "16px 16px 4px 16px"
                        : "16px 16px 16px 4px",
                    background:
                      message.sender === "user"
                        ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                        : "white",
                    color: message.sender === "user" ? "white" : "#1f2937",
                    boxShadow:
                      message.sender === "user"
                        ? "0 2px 8px rgba(102, 126, 234, 0.3)"
                        : "0 2px 8px rgba(0, 0, 0, 0.1)",
                    whiteSpace: "pre-wrap",
                    wordWrap: "break-word",
                    fontSize: "0.9rem",
                    lineHeight: 1.5,
                  }}
                >
                  {message.text}
                  <div
                    style={{
                      fontSize: "0.65rem",
                      marginTop: "0.5rem",
                      opacity: 0.7,
                    }}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: "flex", justifyContent: "flex-start" }}>
                <div
                  style={{
                    padding: "0.75rem 1rem",
                    borderRadius: "16px 16px 16px 4px",
                    background: "white",
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Loader2
                    size={16}
                    style={{ animation: "spin 1s linear infinite" }}
                  />
                  <span style={{ fontSize: "0.9rem", color: "#6b7280" }}>
                    AI is thinking...
                  </span>
                </div>
              </div>
            )}

            {/* Suggested Questions */}
            {showSuggestions && messages.length === 1 && (
              <div style={{ marginTop: "1rem" }}>
                <p
                  style={{
                    fontSize: "0.75rem",
                    color: "#6b7280",
                    marginBottom: "0.5rem",
                    fontWeight: 600,
                  }}
                >
                  SUGGESTED QUESTIONS:
                </p>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.5rem",
                  }}
                >
                  {SUGGESTED_QUESTIONS.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      style={{
                        padding: "0.6rem 0.75rem",
                        background: "white",
                        border: "1px solid #e5e7eb",
                        borderRadius: "8px",
                        fontSize: "0.8rem",
                        color: "#374151",
                        cursor: "pointer",
                        textAlign: "left",
                        transition: "all 0.2s",
                        boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.background = "#f3f4f6";
                        e.currentTarget.style.borderColor = "#667eea";
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.background = "white";
                        e.currentTarget.style.borderColor = "#e5e7eb";
                      }}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div
            style={{
              padding: "1rem 1.5rem",
              background: "white",
              borderTop: "1px solid #e5e7eb",
              display: "flex",
              gap: "0.75rem",
            }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about the grid..."
              disabled={loading}
              style={{
                flex: 1,
                padding: "0.75rem 1rem",
                border: "1px solid #e5e7eb",
                borderRadius: "24px",
                outline: "none",
                fontSize: "0.9rem",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "#667eea";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "#e5e7eb";
              }}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              style={{
                width: "44px",
                height: "44px",
                borderRadius: "50%",
                background:
                  input.trim() && !loading
                    ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                    : "#e5e7eb",
                border: "none",
                cursor: input.trim() && !loading ? "pointer" : "not-allowed",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.2s",
              }}
              onMouseOver={(e) => {
                if (input.trim() && !loading) {
                  e.currentTarget.style.transform = "scale(1.05)";
                }
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = "scale(1)";
              }}
            >
              <Send
                size={20}
                color={input.trim() && !loading ? "white" : "#9ca3af"}
              />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
