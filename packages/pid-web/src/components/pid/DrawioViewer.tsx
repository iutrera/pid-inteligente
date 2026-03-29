import { useCallback, useEffect, useRef, useState } from "react";

interface DrawioViewerProps {
  pidId: string;
  className?: string;
  /** Called when the user saves changes in the Draw.io editor */
  onSave?: (xml: string) => void;
}

/**
 * Embeds the full Draw.io editor (not just the viewer) so the user can
 * edit the P&ID directly: add equipment, instruments, connections, etc.
 *
 * Uses the diagrams.net embed mode via postMessage protocol:
 * https://www.drawio.com/doc/faq/embed-mode
 *
 * Flow:
 * 1. iframe loads draw.io in embed mode
 * 2. draw.io sends "init" → we reply with "load" + XML
 * 3. User edits the diagram
 * 4. User clicks Save → draw.io sends "save" with updated XML
 * 5. We call onSave() with the new XML to rebuild the KG
 */
export function DrawioViewer({ pidId, className = "", onSave }: DrawioViewerProps): JSX.Element {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const xmlRef = useRef<string | null>(null);
  const initializedRef = useRef(false);

  // Fetch the .drawio XML from the API
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    initializedRef.current = false;

    fetch(`/api/graph/${encodeURIComponent(pidId)}/drawio`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!cancelled) {
          xmlRef.current = data.xml;
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [pidId]);

  // Handle messages from the Draw.io iframe
  const handleMessage = useCallback((evt: MessageEvent) => {
    if (!iframeRef.current) return;

    let msg: { event?: string; xml?: string; exit?: boolean };
    try {
      msg = typeof evt.data === "string" ? JSON.parse(evt.data) : evt.data;
    } catch {
      return; // Not a JSON message
    }

    const iframe = iframeRef.current;

    switch (msg.event) {
      case "init":
        // Editor is ready — send the XML to load
        if (xmlRef.current && !initializedRef.current) {
          initializedRef.current = true;
          iframe.contentWindow?.postMessage(
            JSON.stringify({
              action: "load",
              autosave: 0,
              xml: xmlRef.current,
            }),
            "*",
          );
        }
        break;

      case "save":
        // User clicked save — capture the updated XML
        if (msg.xml) {
          xmlRef.current = msg.xml;
          onSave?.(msg.xml);
          // Acknowledge the save so draw.io shows "saved" status
          iframe.contentWindow?.postMessage(
            JSON.stringify({ action: "status", message: "Guardado", modified: false }),
            "*",
          );
        }
        break;

      case "exit":
        // User clicked exit/close — we don't close, just ignore
        break;

      default:
        break;
    }
  }, [onSave]);

  useEffect(() => {
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [handleMessage]);

  if (loading) {
    return (
      <div className={`flex items-center justify-center bg-gray-50 ${className}`}>
        <div className="flex flex-col items-center gap-2">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <p className="text-xs text-gray-500">Cargando P&amp;ID...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-gray-50 ${className}`}>
        <div className="text-center">
          <p className="text-sm text-gray-500">No se pudo cargar el P&amp;ID</p>
          <p className="mt-1 text-xs text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!xmlRef.current) {
    return (
      <div className={`flex items-center justify-center bg-gray-50 ${className}`}>
        <p className="text-sm text-gray-400">No hay P&amp;ID cargado</p>
      </div>
    );
  }

  // Draw.io embed URL with editor mode enabled
  const editorUrl = [
    "https://embed.diagrams.net/?",
    "embed=1",         // Embed mode (postMessage API)
    "&proto=json",     // Use JSON protocol
    "&spin=1",         // Show spinner while loading
    "&libraries=1",    // Show shape libraries sidebar
    "&saveAndExit=0",  // Hide "Save & Exit" (we handle save ourselves)
    "&noExitBtn=1",    // Hide exit button
    "&noSaveBtn=0",    // Show save button
    "&modified=unsavedChanges", // Track unsaved changes
  ].join("");

  return (
    <div className={`relative ${className}`}>
      <iframe
        ref={iframeRef}
        src={editorUrl}
        className="h-full w-full border-0"
        title="P&amp;ID Editor"
      />
    </div>
  );
}
