import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface LogsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  taskId: number;
  logs: string;
}

export function LogsDialog({ open, onOpenChange, taskId, logs }: LogsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="text-sm">Логи задачи #{taskId}</DialogTitle>
        </DialogHeader>
        <ScrollArea className="h-[200px] w-full rounded-md border border-border bg-muted/30 p-3">
          <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono">
            {logs || "Нет записей"}
          </pre>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
