import type { SchemeInfo } from "@/types/chat";

interface SidebarProps {
  onSchemeClick: (query: string) => void;
}

const SCHEMES: SchemeInfo[] = [
  {
    id: "mid-cap",
    name: "Mid Cap Fund",
    description: "Diversified mid-cap exposure",
    risk: "Very High",
    riskColor: "error",
    riskIcon: "warning",
    path: "mid-cap-fund",
  },
  {
    id: "small-cap",
    name: "Small Cap Fund",
    description: "High growth small-cap equity",
    risk: "Very High",
    riskColor: "error",
    riskIcon: "warning",
    path: "small-cap-fund",
  },
  {
    id: "large-cap",
    name: "Large Cap Fund",
    description: "Stable blue-chip companies",
    risk: "High",
    riskColor: "tertiary",
    riskIcon: "trending_up",
    path: "large-cap-fund",
  },
  {
    id: "gold-etf",
    name: "Gold ETF FoF",
    description: "Digital gold investment",
    risk: "Moderate",
    riskColor: "secondary",
    riskIcon: "shield",
    path: "gold-etf-fof",
  },
  {
    id: "elss",
    name: "ELSS Tax Saver",
    description: "Tax savings under 80C",
    risk: "High",
    riskColor: "tertiary",
    riskIcon: "trending_up",
    path: "elss-tax-saver",
  },
];

const riskBadgeClasses: Record<string, string> = {
  error: "bg-[#93000a]/20 text-[#ffb4ab]",
  tertiary: "bg-[#de8712]/20 text-[#ffb86e]",
  secondary: "bg-[#ee9800]/20 text-[#ffb95f]",
};

export default function Sidebar({ onSchemeClick }: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-[#171f33]/60 backdrop-blur-xl z-50 flex flex-col shadow-[8px_0_32px_rgba(0,0,0,0.2)]">
      {/* Header */}
      <div className="p-6 mb-4 flex items-center gap-3 border-b border-[#3e4850]/10">
        <span className="material-symbols-outlined text-[#89ceff]">
          account_balance_wallet
        </span>
        <h2 className="text-2xl font-semibold text-[#dae2fd] tracking-tight">
          Schemes
        </h2>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-4 space-y-2 overflow-y-auto">
        {SCHEMES.map((s) => (
          <button
            key={s.id}
            onClick={() =>
              onSchemeClick(`Tell me about HDFC ${s.name} Direct Growth`)
            }
            className="w-full group flex flex-col px-4 py-3 rounded-xl transition-all hover:bg-[#2d3449]/40 text-left"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-semibold text-[#dae2fd]">
                {s.name}
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold flex items-center gap-1 ${riskBadgeClasses[s.riskColor]}`}
              >
                <span className="material-symbols-outlined text-[12px]">
                  {s.riskIcon}
                </span>
                {s.risk}
              </span>
            </div>
            <p className="text-xs text-[#bec8d2]">{s.description}</p>
          </button>
        ))}
      </nav>
    </aside>
  );
}
