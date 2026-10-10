import PdfUploader from "@/components/PdfUploader";

export default function UploadPage() {
  return (
    <div>
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          上传学校规章制度
        </h1>
        <p className="text-gray-500">
          上传 PDF 文件后，即可基于文档内容进行智能问答
        </p>
      </div>
      <PdfUploader />
    </div>
  );
}