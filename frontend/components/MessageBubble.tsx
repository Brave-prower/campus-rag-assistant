"use client";

interface Source {
  page: number;
  excerpt: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm ${
          isUser
            ? "bg-primary-600 text-white"
            : "bg-gray-100 text-gray-700"
        }`}
      >
        {isUser ? "👤" : "🎓"}
      </div>
      <div
        className={`max-w-[75%] ${
          isUser ? "items-end" : "items-start"
        } flex flex-col`}
      >
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap ${
            isUser
              ? "bg-primary-600 text-white rounded-tr-sm"
              : "bg-gray-100 text-gray-800 rounded-tl-sm"
          }`}
        >
          {message.content}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1 w-full">
            <p className="text-xs text-gray-400 font-medium">📎 来源引用：</p>
            {message.sources.map((s, i) => (
              <div
                key={i}
                className="bg-yellow-50 border border-yellow-200 rounded-md px-3 py-2 text-xs"
              >
                <span className="text-yellow-700 font-semibold">
                  📖 第 {s.page} 页
                </span>
                <p className="text-gray-600 mt-1 line-clamp-2">{s.excerpt}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}