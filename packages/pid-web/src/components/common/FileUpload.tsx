import React, { useCallback, useRef, useState } from "react";
import { uploadAndBuildGraph } from "@/services/api-client";
import type { PidStats } from "@/types/api";

interface FileUploadProps {
  onSuccess: (stats: PidStats, file: File) => void;
  /** Optional extra classes for the outer container. */
  className?: string;
}

const ACCEPTED_EXTENSIONS = [".drawio", ".xml"];

function isAcceptedFile(file: File): boolean {
  return ACCEPTED_EXTENSIONS.some((ext) =>
    file.name.toLowerCase().endsWith(ext),
  );
}

export function FileUpload({ onSuccess, className = "" }: FileUploadProps) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!isAcceptedFile(file)) {
        setError("Solo se aceptan archivos .drawio o .xml");
        return;
      }
      setError(null);
      setUploading(true);
      try {
        const stats = await uploadAndBuildGraph(file);
        onSuccess(stats, file);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Error al subir el archivo",
        );
      } finally {
        setUploading(false);
      }
    },
    [onSuccess],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  }, []);

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      // Reset so same file can be re-selected
      e.target.value = "";
    },
    [handleFile],
  );

  return (
    <div
      className={`relative ${className}`}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
    >
      <button
        type="button"
        disabled={uploading}
        onClick={() => inputRef.current?.click()}
        className={`flex w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors ${
          dragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50"
        } ${uploading ? "pointer-events-none opacity-60" : ""}`}
      >
        {uploading ? (
          <>
            <svg
              className="mb-3 h-10 w-10 animate-spin text-blue-500"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
            <p className="text-sm font-medium text-gray-600">
              Procesando P&amp;ID...
            </p>
          </>
        ) : (
          <>
            <svg
              className="mb-3 h-10 w-10 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 16v-8m0 0l-3 3m3-3l3 3M3 16.5V18a2.25 2.25 0 002.25 2.25h13.5A2.25 2.25 0 0021 18v-1.5M7.5 12H3m18 0h-4.5"
              />
            </svg>
            <p className="text-sm font-medium text-gray-600">
              Arrastra un archivo P&amp;ID aqui
            </p>
            <p className="mt-1 text-xs text-gray-400">
              .drawio o .xml
            </p>
          </>
        )}
      </button>

      <input
        ref={inputRef}
        type="file"
        accept=".drawio,.xml"
        className="hidden"
        onChange={onInputChange}
      />

      {error && (
        <p className="mt-2 text-center text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
