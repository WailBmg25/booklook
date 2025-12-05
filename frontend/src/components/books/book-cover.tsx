import { BookOpen } from "lucide-react";

interface BookCoverProps {
  imageUrl?: string | null;
  title: string;
  size?: "small" | "medium" | "large";
  className?: string;
}

const sizeClasses = {
  small: "w-24 h-36",
  medium: "w-32 h-48",
  large: "w-48 h-72",
};

const gradients = [
  "from-amber-700 via-amber-800 to-amber-900",
  "from-red-800 via-red-900 to-red-950",
  "from-emerald-700 via-emerald-800 to-emerald-900",
  "from-blue-800 via-blue-900 to-blue-950",
  "from-purple-800 via-purple-900 to-purple-950",
  "from-slate-700 via-slate-800 to-slate-900",
  "from-orange-700 via-orange-800 to-orange-900",
  "from-teal-700 via-teal-800 to-teal-900",
];

function getGradientForTitle(title: string): string {
  // Generate consistent gradient based on title
  const hash = title.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return gradients[hash % gradients.length];
}

export default function BookCover({
  imageUrl,
  title,
  size = "medium",
  className = "",
}: BookCoverProps) {
  const gradient = getGradientForTitle(title);

  if (imageUrl) {
    return (
      <div className={`${sizeClasses[size]} ${className} relative overflow-hidden rounded-lg shadow-lg`}>
        <img
          src={imageUrl}
          alt={title}
          className="w-full h-full object-cover"
          onError={(e) => {
            // If image fails to load, hide it and show fallback
            e.currentTarget.style.display = "none";
            const fallback = e.currentTarget.nextElementSibling;
            if (fallback) {
              (fallback as HTMLElement).style.display = "flex";
              (fallback as HTMLElement).classList.remove("hidden");
            }
          }}
        />
        {/* Fallback that shows if image fails */}
        <div
          className={`absolute inset-0 bg-gradient-to-br ${gradient} p-4 hidden flex-col justify-between items-center text-center`}
        >
          {/* Leather texture overlay */}
          <div className="absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-transparent via-black to-transparent"></div>
          
          {/* Book spine effect */}
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-black opacity-30"></div>
          <div className="absolute left-1 top-0 bottom-0 w-px bg-white opacity-20"></div>
          
          {/* Content */}
          <div className="relative z-10 w-full">
            <div className="text-xs text-amber-200 font-serif mb-2">📚</div>
            <h3 className="text-white font-serif text-sm leading-tight line-clamp-6 drop-shadow-lg">
              {title}
            </h3>
          </div>
          <BookOpen className="h-8 w-8 text-white opacity-30 relative z-10" />
        </div>
      </div>
    );
  }

  // No image URL - show generated cover
  return (
    <div
      className={`${sizeClasses[size]} ${className} bg-gradient-to-br ${gradient} rounded-lg shadow-lg p-4 flex flex-col justify-between items-center text-center relative overflow-hidden`}
    >
      {/* Leather texture overlay */}
      <div className="absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-transparent via-black to-transparent"></div>
      
      {/* Book spine effect */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-black opacity-30"></div>
      <div className="absolute left-1 top-0 bottom-0 w-px bg-white opacity-20"></div>
      
      {/* Content */}
      <div className="relative z-10 w-full">
        <div className="text-xs text-amber-200 font-serif mb-2">📚</div>
        <h3 className="text-white font-serif text-sm leading-tight line-clamp-6 drop-shadow-lg">
          {title}
        </h3>
      </div>
      
      <BookOpen className="h-8 w-8 text-white opacity-30 relative z-10" />
    </div>
  );
}
