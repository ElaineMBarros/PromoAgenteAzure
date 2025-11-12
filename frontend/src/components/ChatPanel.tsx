import { FormEvent, useState, useEffect } from "react";
import styled from "styled-components";
import ReactMarkdown from "react-markdown";
import { sendChatMessage } from "../services/api";
import { ChatMessage } from "../types";

interface ChatPanelProps {
  messages: ChatMessage[];
  onMessagesChange: (messages: ChatMessage[]) => void;
  sessionId?: string;
  onSessionChange: (sessionId: string) => void;
  currentState?: any;
  onStateChange?: (state: any) => void;
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
  
  /* Estilos para markdown renderizado */
  p {
    margin: 0.5em 0;
    &:first-child {
      margin-top: 0;
    }
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  strong {
    font-weight: 600;
  }
  
  ul, ol {
    margin: 0.5em 0;
    padding-left: 1.5em;
  }
  
  code {
    background: rgba(0, 0, 0, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.9em;
  }
`;

const MessageMeta = styled.span`
  display: block;
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 6px;
`;

// Função para formatar timestamp com segurança
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

export function ChatPanel({ messages, onMessagesChange, sessionId, onSessionChange, currentState, onStateChange, onPromotionCompleted }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const currentSession = sessionId;

  // Função para fazer download do Excel
  const downloadExcel = (base64: string, filename: string) => {
    try {
      // Converte base64 para blob
      const byteCharacters = atob(base64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });

      // Cria link de download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log('✅ Download do Excel iniciado:', filename);
    } catch (error) {
      console.error('❌ Erro ao fazer download do Excel:', error);
    }
  };

  // Monitora mudanças no estado para detectar excel_base64
  useEffect(() => {
    if (currentState?.data?.excel_base64 && currentState?.data?.excel_filename) {
      console.log('📊 Excel detectado no estado, iniciando download...');
      downloadExcel(currentState.data.excel_base64, currentState.data.excel_filename);
      
      // Remove o excel do estado após download para não baixar novamente
      if (onStateChange) {
        const newState = { ...currentState };
        delete newState.data.excel_base64;
        delete newState.data.excel_filename;
        onStateChange(newState);
      }
    }
  }, [currentState]);

  const handleNewPromotion = () => {
    // Limpa as mensagens do chat
    onMessagesChange([]);
    // Gera um novo session ID
    const newSessionId = crypto.randomUUID();
    onSessionChange(newSessionId);
    // Limpa o estado
    if (onStateChange) {
      onStateChange(null);
    }
    // Limpa o localStorage
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
      // Envia mensagem COM o estado atual
      const response = await sendChatMessage(trimmed, currentSession, currentState);

      const agentMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "agent",
        content: response.response,
        timestamp: response.timestamp
      };

      onMessagesChange([...updated, agentMessage]);
      
      // Atualiza session_id se mudou
      if (response.session_id && response.session_id !== currentSession) {
        onSessionChange(response.session_id);
      }
      
      // Atualiza o estado recebido do backend
      if (response.state && onStateChange) {
        onStateChange(response.state);
      }

      // Detecta se a promoção foi concluída/salva
      if (onPromotionCompleted && (response.response.includes("Promoção enviada com sucesso") || response.response.includes("Promoção salva no sistema"))) {
        // Aguarda um pouco para garantir que o backend salvou
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
      <ScrollArea>
        {messages.map(message => (
          <MessageBubble key={message.id} $origin={message.role}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
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
