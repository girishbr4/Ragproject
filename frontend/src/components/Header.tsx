export default function Header() {
  return (
    <header className="fixed top-0 left-72 right-0 h-20 bg-[#0b1326]/80 backdrop-blur-2xl z-40 px-6 flex items-center justify-between shadow-[0_4px_24px_rgba(0,0,0,0.15)]">
      {/* Left — logo + title */}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-[#0ea5e9]/20 flex items-center justify-center">
          <span className="material-symbols-outlined text-[#89ceff] text-xl">
            account_balance
          </span>
        </div>
        <h1 className="text-2xl font-semibold text-[#dae2fd]">
          HDFC Mutual Fund FAQ Assistant
        </h1>
      </div>

      {/* Right — disclaimer pill + avatar */}
      <div className="flex items-center gap-6">
        <div className="bg-[#ee9800]/10 border border-[#ee9800]/20 px-4 py-1.5 rounded-full flex items-center gap-2">
          <span className="material-symbols-outlined text-[#ffb95f] text-[18px]">
            warning
          </span>
          <span className="text-xs font-bold text-[#ffb95f]">
            Facts-only. No investment advice.
          </span>
        </div>
        <div className="w-10 h-10 rounded-full bg-[#89ceff] flex items-center justify-center shadow-lg shadow-[#89ceff]/20">
          <span className="material-symbols-outlined text-[#00344d] text-[20px]">
            person
          </span>
        </div>
      </div>
    </header>
  );
}
