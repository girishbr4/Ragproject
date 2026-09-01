interface EmptyStateProps {
  onExampleClick: (query: string) => void;
}

const EXAMPLES = [
  {
    icon: "percent",
    iconBg: "bg-[#0ea5e9]/20 group-hover:bg-[#0ea5e9]/40",
    iconColor: "text-[#89ceff]",
    title: "Expense Ratio",
    subtitle: "What is the expense ratio of HDFC Mid Cap Fund?",
    query: "What is the expense ratio of HDFC Mid Cap Fund Direct Growth?",
  },
  {
    icon: "exit_to_app",
    iconBg: "bg-[#de8712]/20 group-hover:bg-[#de8712]/40",
    iconColor: "text-[#ffb86e]",
    title: "Exit Load",
    subtitle: "What is the exit load for HDFC ELSS?",
    query: "What is the exit load for HDFC ELSS Tax Saver Fund Direct Plan?",
  },
  {
    icon: "savings",
    iconBg: "bg-[#ee9800]/20 group-hover:bg-[#ee9800]/40",
    iconColor: "text-[#ffb95f]",
    title: "Min SIP",
    subtitle: "What is the minimum SIP for HDFC Small Cap?",
    query: "What is the minimum SIP amount for HDFC Small Cap Fund Direct Growth?",
  },
];

export default function EmptyState({ onExampleClick }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in-up">
      {/* Bot avatar with glow */}
      <div className="relative mb-8">
        <div className="absolute -inset-4 bg-[#89ceff]/20 blur-3xl rounded-full" />
        <div className="w-24 h-24 rounded-full bg-[#222a3d]/80 backdrop-blur-2xl flex items-center justify-center relative shadow-xl">
          <span
            className="material-symbols-outlined text-[#89ceff]"
            style={{
              fontSize: "48px",
              fontVariationSettings: "'FILL' 1",
            }}
          >
            smart_toy
          </span>
        </div>
      </div>

      {/* Heading */}
      <h2 className="text-5xl font-bold text-[#dae2fd] tracking-tight mb-4 max-w-2xl leading-tight">
        Hello! I can help you with factual questions about HDFC mutual fund
        schemes.
      </h2>

      {/* Subheading */}
      <p className="text-lg text-[#bec8d2] max-w-xl mb-12 leading-relaxed">
        Ask me about expense ratios, exit loads, minimum SIP amounts, lock-in
        periods, and benchmark indices.
      </p>

      {/* Example cards */}
      <div className="w-full max-w-3xl grid grid-cols-1 md:grid-cols-3 gap-6">
        {EXAMPLES.map((ex) => (
          <button
            key={ex.title}
            onClick={() => onExampleClick(ex.query)}
            className="group flex flex-col items-start p-6 bg-[#171f33]/60 backdrop-blur-xl rounded-[20px] transition-all duration-300 hover:bg-[#171f33] hover:shadow-[0_8px_32px_rgba(14,165,233,0.15)] text-left hover:-translate-y-1"
          >
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center mb-4 transition-colors ${ex.iconBg}`}
            >
              <span className={`material-symbols-outlined ${ex.iconColor}`}>
                {ex.icon}
              </span>
            </div>
            <span className="text-2xl font-semibold text-[#dae2fd] mb-2">
              {ex.title}
            </span>
            <span className="text-base text-[#bec8d2]">{ex.subtitle}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
