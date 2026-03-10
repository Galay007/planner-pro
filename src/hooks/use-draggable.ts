import { useState, useCallback, useEffect, useRef } from "react";

export function useDraggable() {
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const startPos = useRef({ x: 0, y: 0 });
  const startOffset = useRef({ x: 0, y: 0 });

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // Only left mouse button
      if (e.button !== 0) return;
      e.preventDefault();
      setIsDragging(true);
      startPos.current = { x: e.clientX, y: e.clientY };
      startOffset.current = { ...offset };
    },
    [offset]
  );

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      setOffset({
        x: startOffset.current.x + (e.clientX - startPos.current.x),
        y: startOffset.current.y + (e.clientY - startPos.current.y),
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  const resetPosition = useCallback(() => {
    setOffset({ x: 0, y: 0 });
  }, []);

  return { offset, isDragging, handleMouseDown, resetPosition };
}
