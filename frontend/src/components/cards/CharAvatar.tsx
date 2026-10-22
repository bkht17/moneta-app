import { getInitials } from "../../lib/format";

export default function CharAvatar({ fullName, className = "h-12 w-12" }: { fullName: string; className?: string }) {
  return (
    <div className={`flex items-center justify-center rounded-full bg-mint font-medium text-primary ${className}`}>
      {getInitials(fullName)}
    </div>
  );
}
