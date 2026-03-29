import { useEffect, useMemo, useState } from "react";

interface DrawioViewerProps {
  pidId: string;
  className?: string;
}

/**
 * Renders a Draw.io P&ID diagram using the official diagrams.net viewer.
 * Fetches the .drawio XML from the API and renders via iframe + viewer-static.min.js.
 */
export function DrawioViewer({ pidId, className = "" }: DrawioViewerProps): JSX.Element {
  const [xmlContent, setXmlContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`/api/graph/${encodeURIComponent(pidId)}/drawio`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!cancelled) {
          setXmlContent(data.xml);
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

  const iframeSrcDoc = useMemo(() => {
    if (!xmlContent) return null;

    // Use JSON.stringify to safely escape the XML for embedding in JS
    const jsonSafeXml = JSON.stringify(xmlContent);

    // Build the config as a JS object in a script tag to avoid HTML attribute escaping issues
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    body { margin: 0; padding: 0; overflow: auto; background: #fafafa; }
    #graph-container { width: 100%; min-height: 100vh; }
  </style>
</head>
<body>
  <div id="graph-container" class="mxgraph"></div>
  <script>
    // Set the config via JS to avoid JSON-in-HTML-attribute escaping issues
    var container = document.getElementById('graph-container');
    var config = {
      highlight: '#0000ff',
      nav: true,
      resize: true,
      toolbar: 'zoom layers lightbox',
      xml: ${jsonSafeXml}
    };
    container.setAttribute('data-mxgraph', JSON.stringify(config));
  <\/script>
  <script src="https://viewer.diagrams.net/js/viewer-static.min.js"><\/script>
</body>
</html>`;
  }, [xmlContent]);

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

  if (!iframeSrcDoc) {
    return (
      <div className={`flex items-center justify-center bg-gray-50 ${className}`}>
        <p className="text-sm text-gray-400">No hay P&amp;ID cargado</p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <iframe
        srcDoc={iframeSrcDoc}
        className="h-full w-full border-0"
        sandbox="allow-scripts allow-same-origin"
        title="P&amp;ID Diagram"
      />
    </div>
  );
}
