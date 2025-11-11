import { FormEvent, useState, useEffect } from "react";
import styled from "styled-components";
import { sendChatMessage } from "../services/api";
import { ChatMessage } from "../types";

interface ChatPanelProps {
  messages: ChatMessage[];
  onMessagesChange: (messages: ChatMessage[]) => void;
  sessionId?: string;
  onSessionChange: (sessionId: string) => void;
  onPromotionCompleted?: () => void;
}

const ChatWrapper = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;

const ChatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
`;

const Title = styled.h2`
  font-size: 1.5rem;
`;

const NewPromotionButton = styled.button`
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.colors.primary};
  padding: 8px 16px;
  background: transparent;
  color: ${({ theme }) => theme.colors.primary};
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ theme }) => theme.colors.primary};
    color: #ffffff;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(31, 60, 136, 0.2);
  }
`;

const ScrollArea = styled.div`
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const MessageBubble = styled.div<{ $origin: "user" | "agent" }>`
  align-self: ${({ $origin }) => ($origin === "user" ? "flex-end" : "flex-start")};
  background: ${({ $origin, theme }) => ($origin === "user" ? theme.colors.primary : theme.colors.surface)};
  color: ${({ $origin }) => ($origin === "user" ? "#ffffff" : "#1a1a1a")};
  padding: 14px 18px;
  border-radius: 18px;
  max-width: 70%;
  line-height: 1.6;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08);
  border: ${({ $origin, theme }) => ($origin === "agent" ? `1px solid ${theme.colors.muted}33` : "none")};
`;

const MessageMeta = styled.span`
  display: block;
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 6px;
`;

// 🎯 AJUSTE 4: Últimas Promoções
const RecentPromotions = styled.div`
  background: ${({ theme }) => theme.colors.surface};
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
`;

const RecentTitle = styled.h3`
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: ${({ theme }) => theme.colors.primary};
  display: flex;
  align-items: center;
  gap: 8px;
`;

const RecentList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const RecentItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(31, 60, 136, 0.05);
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(31, 60, 136, 0.1);
    transform: translateX(4px);
  }
`;

const RecentIcon = styled.span`
  font-size: 1.1rem;
`;

const RecentText = styled.span`
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const DataField = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 8px 0;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);

  &:last-child {
    border-bottom: none;
  }
`;

const FieldIcon = styled.span`
  font-size: 1.2rem;
  flex-shrink: 0;
  margin-top: 2px;
`;

const FieldContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
`;

const FieldLabel = styled.span`
  font-weight: 600;
  font-size: 0.85rem;
  opacity: 0.8;
`;

const FieldValue = styled.span`
  font-size: 0.95rem;
  line-height: 1.5;
`;

// Função auxiliar para formatar data
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      return new Date().toLocaleString('pt-BR');
    }
    return date.toLocaleString('pt-BR');
  } catch {
    return new Date().toLocaleString('pt-BR');
  }
}

// Função para fazer download do Excel
function downloadExcel(base64: string, filename: string) {
  try {
    const binaryString = window.atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    const blob = new Blob([bytes], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    console.log(`✅ Download iniciado: ${filename}`);
  } catch (error) {
    console.error('❌ Erro ao fazer download do Excel:', error);
  }
}

// 🎯 Funções para gerenciar últimas promoções no localStorage
function saveRecentPromotion(title: string) {
  try {
    const recent = localStorage.getItem('recent-promotions');
    const promotions = recent ? JSON.parse(recent) : [];
    
    const newPromotion = { 
      title, 
      date: new Date().toLocaleDateString('pt-BR'),
      timestamp: new Date().toISOString() 
    };
    
    const updated = [newPromotion, ...promotions.filter((p: any) => p.title !== title)].slice(0, 3);
    localStorage.setItem('recent-promotions', JSON.stringify(updated));
  } catch (error) {
    console.error('Erro ao salvar promoção recente:', error);
  }
}

function getRecentPromotions(): Array<{ title: string; date: string; timestamp: string }> {
  try {
    const recent = localStorage.getItem('recent-promotions');
    return recent ? JSON.parse(recent) : [];
  } catch {
    return [];
  }
}

const Form = styled.form`
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
`;

const Input = styled.textarea`
  flex: 1;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  padding: 12px 16px;
  min-height: 90px;
  font-size: 1rem;
  resize: vertical;
  font-family: inherit;
  background: #fdfdfd;
`;

const Button = styled.button`
  border-radius: 12px;
  border: none;
  padding: 16px 24px;
  background: ${({ theme }) => theme.colors.primary};
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(31, 60, 136, 0.2);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

// Função para parser e renderizar campos estruturados
function parseStructuredData(content: string) {
  const fieldPattern = /^([✅📌🎯📝👥📅✨💰🎁📦]+)\s*([^:]+):\s*(.+)$/gm;
  const matches = [...content.matchAll(fieldPattern)];
  
  if (matches.length > 0) {
    const parts: (string | JSX.Element)[] = [];
    let lastIndex = 0;
    
    matches.forEach((match, idx) => {
      const [fullMatch, icon, label, value] = match;
      const matchIndex = match.index!;
      
      if (matchIndex > lastIndex) {
        const textBefore = content.substring(lastIndex, matchIndex);
        if (textBefore.trim()) {
          parts.push(textBefore);
        }
      }
      
      parts.push(
        <DataField key={`field-${idx}`}>
          <FieldIcon>{icon}</FieldIcon>
          <FieldContent>
            <FieldLabel>{label}:</FieldLabel>
            <FieldValue>{value}</FieldValue>
          </FieldContent>
        </DataField>
      );
      
      lastIndex = matchIndex + fullMatch.length;
    });
    
    if (lastIndex < content.length) {
      const textAfter = content.substring(lastIndex);
      if (textAfter.trim()) {
        parts.push(textAfter);
      }
    }
    
    return <>{parts}</>;
  }
  
  return content;
}

export function ChatPanel({ messages, onMessagesChange, sessionId, onSessionChange, onPromotionCompleted }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [currentState, setCurrentState] = useState<any>(null);
  const [recentPromotions, setRecentPromotions] = useState<Array<{ title: string; date: string }>>([]);
  const currentSession = sessionId;

  // 🎯 AJUSTE 4: Carrega últimas promoções ao montar
  useEffect(() => {
    setRecentPromotions(getRecentPromotions());
  }, []);

  const handleNewPromotion = () => {
    onMessagesChange([]);
    setCurrentState(null);
    const newSessionId = crypto.randomUUID();
    onSessionChange(newSessionId);
    localStorage.setItem("promoagente-session", newSessionId);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString()
    };

    const updated = [...messages, userMessage];
    onMessagesChange(updated);
    setInput("");
    setIsSending(true);

    try {
      const response = await sendChatMessage(trimmed, currentSession, currentState);

      if (response.state) {
        setCurrentState(response.state);
        
        // 🎯 AJUSTE 4: Salva promoção recente quando tem título
        if (response.state.data?.titulo) {
          saveRecentPromotion(response.state.data.titulo);
          setRecentPromotions(getRecentPromotions());
        }
        
        if (response.state.data?.excel_base64 && response.state.data?.excel_filename) {
          downloadExcel(response.state.data.excel_base64, response.state.data.excel_filename);
        }
      }

      const agentMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "agent",
        content: response.response,
        timestamp: response.timestamp
      };

      onMessagesChange([...updated, agentMessage]);
      if (response.session_id && response.session_id !== currentSession) {
        onSessionChange(response.session_id);
      }

      if (onPromotionCompleted && (response.response.includes("Promoção enviada com sucesso") || response.response.includes("Promoção salva no sistema"))) {
        setTimeout(() => {
          onPromotionCompleted();
        }, 500);
      }
    } catch (error) {
      console.error("Erro ao enviar mensagem", error);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <ChatWrapper>
      <ChatHeader>
        <Title>PromoAgente chat</Title>
        <NewPromotionButton onClick={handleNewPromotion}>
          ✨ Nova Promoção
        </NewPromotionButton>
      </ChatHeader>

      {/* 🎯 AJUSTE 4: Mostra últimas 3 promoções se houver */}
      {recentPromotions.length > 0 && (
        <RecentPromotions>
          <RecentTitle>
            <span>🕐</span>
            Últimas promoções
          </RecentTitle>
          <RecentList>
            {recentPromotions.map((promo, idx) => (
              <RecentItem key={idx}>
                <RecentIcon>📦</RecentIcon>
                <RecentText>{promo.title}</RecentText>
                <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>{promo.date}</span>
              </RecentItem>
            ))}
          </RecentList>
        </RecentPromotions>
      )}

      <ScrollArea>
        {messages.map(message => (
          <MessageBubble key={message.id} $origin={message.role}>
            {message.role === "agent" ? parseStructuredData(message.content) : message.content}
            <MessageMeta>{formatTimestamp(message.timestamp)}</MessageMeta>
          </MessageBubble>
        ))}
      </ScrollArea>
      
      <Form onSubmit={handleSubmit}>
        <Input
          value={input}
          onChange={event => setInput(event.target.value)}
          placeholder="Descreva a promoção ou peça uma sugestão ao agente"
        />
        <Button type="submit" disabled={isSending}>
          {isSending ? "Enviando..." : "Enviar"}
        </Button>
      </Form>
    </ChatWrapper>
  );
}
