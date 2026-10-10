import ChatPanel from "@/components/ChatPanel";

export default function ChatPage() {
  return (
    <div className="h-[calc(100vh-12rem)]">
      <div className="mb-4 text-center">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">💬 智能问答</h1>
        <p className="text-sm text-gray-500">
          基于已上传的规章制度 PDF，输入你的问题
        </p>
      </div>
      <ChatPanel />
    </div>
  );
}