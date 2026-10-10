"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-bold text-lg text-primary-700">
          🎓 校园教务 RAG 助手
        </Link>
        <div className="flex gap-2">
          <Link
            href="/"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              pathname === "/"
                ? "bg-primary-100 text-primary-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            📄 上传文档
          </Link>
          <Link
            href="/chat"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              pathname === "/chat"
                ? "bg-primary-100 text-primary-700"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            💬 智能问答
          </Link>
        </div>
      </div>
    </nav>
  );
}