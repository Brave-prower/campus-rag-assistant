"use client";

import { useState, useRef } from "react";

type UploadStatus = "idle" | "uploading" | "success" | "error";

interface UploadedFile {
  name: string;
  size: number;
  pages: number;
}

export default function PdfUploader() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [error, setError] = useState<string>("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSelect = () => inputRef.current?.click();

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected || selected.length === 0) return;

    setStatus("uploading");
    setError("");

    for (const file of selected) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError(`"${file.name}" 不是 PDF 文件`);
        setStatus("error");
        continue;
      }

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("上传失败");
        const data = await res.json();
        setFiles((prev) => [
          ...prev,
          { name: data.name, size: data.size, pages: data.pages },
        ]);
      } catch (err: any) {
        setError(err.message || "上传出错");
        setStatus("error");
      }
    }

    setStatus("success");
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div>
      <div
        onClick={handleSelect}
        className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-50 transition-colors"
      >
        <div className="text-5xl mb-4">📥</div>
        <p className="text-lg font-medium text-gray-700 mb-1">
          点击选择 PDF 文件
        </p>
        <p className="text-sm text-gray-500">支持多文件上传，仅接受 .pdf 格式</p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={handleChange}
        />
      </div>

      {status === "uploading" && (
        <p className="mt-4 text-center text-primary-600">⏳ 正在上传...</p>
      )}
      {status === "error" && (
        <p className="mt-4 text-center text-red-500">❌ {error}</p>
      )}

      {files.length > 0 && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">
            ✅ 已上传 ({files.length})
          </h2>
          <ul className="space-y-2">
            {files.map((f) => (
              <li
                key={f.name}
                className="flex items-center justify-between bg-white rounded-lg px-4 py-3 border border-gray-200"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">📄</span>
                  <div>
                    <p className="font-medium text-gray-800">{f.name}</p>
                    <p className="text-xs text-gray-500">
                      {(f.size / 1024).toFixed(1)} KB · 约 {f.pages} 页
                    </p>
                  </div>
                </div>
                <span className="text-green-500 text-sm">✓ 已入库</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}